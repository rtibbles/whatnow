import * as oauth from 'oauth4webapi';
import { getDatabase } from '../../db/database';

export interface DeviceFlowData {
  userCode: string;
  verificationUri: string;
  verificationUriComplete?: string;
  deviceCode: string;
  expiresIn: number;
  interval: number;
}

/**
 * GitHub OAuth 2.0 service using Device Flow
 * Perfect for static apps - no redirect needed
 */
export class GitHubOAuth {
  private readonly clientId = import.meta.env.VITE_GITHUB_CLIENT_ID || '';
  private readonly authServer: oauth.AuthorizationServer = {
    issuer: 'https://github.com',
    device_authorization_endpoint: 'https://github.com/login/device/code',
    token_endpoint: 'https://github.com/login/oauth/access_token'
  };

  private client: oauth.Client;

  constructor() {
    this.client = {
      client_id: this.clientId,
      token_endpoint_auth_method: 'none'
    };
  }

  /**
   * Start device authorization flow
   */
  async startDeviceFlow(): Promise<DeviceFlowData> {
    const response = await oauth.deviceAuthorizationRequest(
      this.authServer,
      this.client,
      {
        scope: 'repo read:project read:org'
      }
    );

    const deviceAuth = await oauth.processDeviceAuthorizationResponse(
      this.authServer,
      this.client,
      response
    );

    if (oauth.isOAuth2Error(deviceAuth)) {
      throw new Error(`Device flow error: ${deviceAuth.error_description || deviceAuth.error}`);
    }

    return {
      userCode: deviceAuth.user_code,
      verificationUri: deviceAuth.verification_uri,
      verificationUriComplete: deviceAuth.verification_uri_complete,
      deviceCode: deviceAuth.device_code,
      expiresIn: deviceAuth.expires_in,
      interval: deviceAuth.interval || 5
    };
  }

  /**
   * Poll for access token (recursive)
   */
  async pollForToken(deviceCode: string, interval: number = 5): Promise<string> {
    const response = await oauth.deviceCodeGrantRequest(
      this.authServer,
      this.client,
      deviceCode
    );

    const result = await oauth.processDeviceCodeResponse(
      this.authServer,
      this.client,
      response
    );

    if (oauth.isOAuth2Error(result)) {
      if (result.error === 'authorization_pending') {
        // User hasn't authorized yet, keep polling
        await new Promise(resolve => setTimeout(resolve, interval * 1000));
        return this.pollForToken(deviceCode, interval);
      } else if (result.error === 'slow_down') {
        // GitHub asking us to slow down
        await new Promise(resolve => setTimeout(resolve, (interval + 5) * 1000));
        return this.pollForToken(deviceCode, interval + 5);
      } else {
        // Other error (expired, denied, etc.)
        throw new Error(`OAuth error: ${result.error_description || result.error}`);
      }
    }

    // Success!
    await this.storeToken(result.access_token);
    return result.access_token;
  }

  /**
   * Get current access token
   */
  async getAccessToken(): Promise<string> {
    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'github_access_token' } })
      .exec();

    if (!config) {
      throw new Error('Not authenticated - please sign in');
    }

    return config.value;
  }

  /**
   * Check if authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'github_access_token' } })
      .exec();

    return !!config;
  }

  /**
   * Sign out
   */
  async signOut(): Promise<void> {
    const db = await getDatabase();
    const token = await db.config
      .findOne({ selector: { key: 'github_access_token' } })
      .exec();

    if (token) {
      await token.remove();
    }
  }

  /**
   * Store token
   */
  private async storeToken(token: string): Promise<void> {
    const db = await getDatabase();
    await db.config.upsert({
      key: 'github_access_token',
      value: token,
      updatedAt: Date.now()
    });
  }
}
