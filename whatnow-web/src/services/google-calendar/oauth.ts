import * as oauth from 'oauth4webapi';
import { getDatabase } from '../../db/database';

/**
 * Google Calendar OAuth 2.0 service using PKCE flow
 * Handles authentication and token management for Google Calendar API
 */
export class GoogleCalendarOAuth {
  private readonly issuer = new URL('https://accounts.google.com');
  private readonly clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  private readonly redirectUri = window.location.origin + window.location.pathname;
  private readonly scopes = ['https://www.googleapis.com/auth/calendar.readonly'];

  private client: oauth.Client;
  private authServer: oauth.AuthorizationServer | null = null;

  constructor() {
    this.client = {
      client_id: this.clientId,
      token_endpoint_auth_method: 'none' // Public client, no secret
    };
  }

  /**
   * Initialize by discovering OAuth server metadata
   */
  async initialize(): Promise<void> {
    this.authServer = await oauth
      .discoveryRequest(this.issuer)
      .then((response) => oauth.processDiscoveryResponse(this.issuer, response));
  }

  /**
   * Start PKCE authorization flow
   */
  async startAuthFlow(): Promise<void> {
    if (!this.authServer) await this.initialize();

    // Generate PKCE parameters
    const codeVerifier = oauth.generateRandomCodeVerifier();
    const codeChallenge = await oauth.calculatePKCECodeChallenge(codeVerifier);
    const state = oauth.generateRandomState();

    // Store for callback (session storage is cleared after auth)
    sessionStorage.setItem('gcal_code_verifier', codeVerifier);
    sessionStorage.setItem('gcal_state', state);

    // Build authorization URL
    const authUrl = new URL(this.authServer!.authorization_endpoint!);
    authUrl.searchParams.set('client_id', this.clientId);
    authUrl.searchParams.set('redirect_uri', this.redirectUri);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', this.scopes.join(' '));
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('code_challenge', codeChallenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    authUrl.searchParams.set('access_type', 'offline');
    authUrl.searchParams.set('prompt', 'consent');

    // Redirect to Google
    window.location.href = authUrl.toString();
  }

  /**
   * Handle OAuth callback
   */
  async handleCallback(): Promise<oauth.TokenEndpointResponse | null> {
    if (!this.authServer) await this.initialize();

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code) return null;

    // Verify state (CSRF protection)
    const storedState = sessionStorage.getItem('gcal_state');
    if (state !== storedState) {
      throw new Error('State mismatch - possible CSRF attack');
    }

    // Get code verifier
    const codeVerifier = sessionStorage.getItem('gcal_code_verifier');
    if (!codeVerifier) {
      throw new Error('Code verifier not found');
    }

    // Exchange authorization code for tokens
    const tokenResponse = await oauth.authorizationCodeGrantRequest(
      this.authServer!,
      this.client,
      params,
      this.redirectUri,
      codeVerifier
    );

    const result = await oauth.processAuthorizationCodeOpenIDResponse(
      this.authServer!,
      this.client,
      tokenResponse
    );

    if (oauth.isOAuth2Error(result)) {
      throw new Error(`OAuth error: ${result.error_description || result.error}`);
    }

    // Store tokens
    await this.storeTokens(result);

    // Clean up
    sessionStorage.removeItem('gcal_code_verifier');
    sessionStorage.removeItem('gcal_state');
    window.history.replaceState({}, document.title, window.location.pathname);

    return result;
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<string> {
    if (!this.authServer) await this.initialize();

    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'gcal_refresh_token' } })
      .exec();

    if (!config) {
      throw new Error('No refresh token found - please re-authenticate');
    }

    const response = await oauth.refreshTokenGrantRequest(
      this.authServer!,
      this.client,
      config.value
    );

    const result = await oauth.processRefreshTokenResponse(
      this.authServer!,
      this.client,
      response
    );

    if (oauth.isOAuth2Error(result)) {
      throw new Error(`Token refresh failed: ${result.error_description || result.error}`);
    }

    await this.storeTokens(result);
    return result.access_token;
  }

  /**
   * Get current access token (refresh if expired)
   */
  async getAccessToken(): Promise<string> {
    const db = await getDatabase();

    const [tokenConfig, expiresConfig] = await Promise.all([
      db.config.findOne({ selector: { key: 'gcal_access_token' } }).exec(),
      db.config.findOne({ selector: { key: 'gcal_token_expires_at' } }).exec()
    ]);

    if (!tokenConfig) {
      throw new Error('Not authenticated - please sign in');
    }

    // Check if token expired
    if (expiresConfig && expiresConfig.value < Date.now()) {
      console.log('Access token expired, refreshing...');
      return await this.refreshAccessToken();
    }

    return tokenConfig.value;
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'gcal_refresh_token' } })
      .exec();

    return !!config;
  }

  /**
   * Sign out (clear tokens)
   */
  async signOut(): Promise<void> {
    const db = await getDatabase();

    const tokens = await Promise.all([
      db.config.findOne({ selector: { key: 'gcal_access_token' } }).exec(),
      db.config.findOne({ selector: { key: 'gcal_refresh_token' } }).exec(),
      db.config.findOne({ selector: { key: 'gcal_token_expires_at' } }).exec()
    ]);

    for (const token of tokens) {
      if (token) await token.remove();
    }
  }

  /**
   * Store tokens in database
   */
  private async storeTokens(tokens: oauth.TokenEndpointResponse): Promise<void> {
    const db = await getDatabase();

    await db.config.upsert({
      key: 'gcal_access_token',
      value: tokens.access_token,
      updatedAt: Date.now()
    });

    if (tokens.refresh_token) {
      await db.config.upsert({
        key: 'gcal_refresh_token',
        value: tokens.refresh_token,
        updatedAt: Date.now()
      });
    }

    if (tokens.expires_in) {
      await db.config.upsert({
        key: 'gcal_token_expires_at',
        value: Date.now() + tokens.expires_in * 1000,
        updatedAt: Date.now()
      });
    }
  }
}
