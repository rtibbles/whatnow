# GitHub OAuth Setup Guide

## Overview

WhatNow uses OAuth 2.0 to connect to GitHub, which is more secure and modern than Personal Access Tokens (which GitHub has deprecated). This guide explains how to set up GitHub OAuth for development or deployment.

## For End Users

**Good news!** If you're just using WhatNow, you don't need to do anything special. The app comes with embedded OAuth credentials that work out of the box.

Simply:
1. Open WhatNow settings
2. Go to the GitHub tab
3. Click "Connect GitHub (OAuth)"
4. Authorize the app in your browser
5. Done!

The OAuth flow will open your browser to GitHub's authorization page, where you can grant WhatNow access to your repositories and projects.

## For Developers (Local Development)

If you're developing WhatNow and want to use your own OAuth credentials for testing:

### 1. Create a GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **"New OAuth App"**
3. Fill in the application details:
   - **Application name**: "WhatNow Development" (or your preferred name)
   - **Homepage URL**: `http://localhost` (or your repo URL)
   - **Authorization callback URL**: `http://localhost:8080/`
4. Click **"Register application"**

### 2. Get Your Credentials

After creating the app:
1. You'll see your **Client ID** on the app page
2. Click **"Generate a new client secret"** to get your **Client Secret**
3. Copy both values (you'll need them in the next step)

### 3. Create Local Credentials File

Create a file named `whatnow/sync/github_credentials_local.py` (this file is gitignored):

```python
# Local development OAuth credentials
# This file is gitignored and will not be committed

GITHUB_CLIENT_ID = "your_client_id_here"
GITHUB_CLIENT_SECRET = "your_client_secret_here"
```

Replace the placeholder values with your actual Client ID and Client Secret.

### 4. Test Your Setup

Run WhatNow:
```bash
python -m whatnow
```

Go to Settings → GitHub → Click "Connect GitHub (OAuth)" and verify the OAuth flow works.

## For Deployment (Production)

If you're deploying WhatNow for others to use, you should create production OAuth credentials:

### 1. Create a Production OAuth App

Follow the same steps as development, but:
- Use a descriptive name: "WhatNow - Activity Tracker"
- Use your production homepage URL
- Authorization callback URL remains: `http://localhost:8080/`

**Important**: The callback URL must be `http://localhost:8080/` because WhatNow runs a local server on the user's machine to receive the OAuth callback.

### 2. Replace Embedded Credentials

Edit `whatnow/sync/github_credentials.py` and replace the placeholder values:

```python
# OAuth 2.0 Client Configuration
GITHUB_CLIENT_ID = "your_production_client_id"
GITHUB_CLIENT_SECRET = "your_production_client_secret"
```

### 3. Security Considerations

**Client Secret in Source Code:**
GitHub OAuth Apps require a client secret for the authorization code exchange. For desktop applications that run locally, this is the standard pattern - the secret is embedded in the application.

This is different from web applications where the secret would be stored server-side. GitHub's OAuth model for "desktop apps" accepts this limitation.

**Best Practices:**
- Limit OAuth scopes to only what's needed (`repo` and `read:project`)
- The app runs locally, so tokens stay on the user's machine
- Tokens are stored in `~/.local/share/whatnow/github_token.pickle`
- Users can revoke access at any time in GitHub Settings → Applications

## OAuth Scopes

WhatNow requests the following GitHub scopes:

- **`repo`**: Full control of private repositories
  - Needed to read repository information and issues/PRs in private repos
  - Required for GitHub Projects V2 GraphQL API access

- **`read:project`**: Read access to projects
  - Needed to read GitHub Projects data
  - Note: GitHub Projects V2 requires this scope

## Troubleshooting

### "OAuth Credentials Not Configured" Error

This means the embedded credentials are still placeholders. Either:
1. Create `github_credentials_local.py` with your own credentials (for development)
2. Replace the placeholder values in `github_credentials.py` (for production)

### OAuth Flow Times Out

The OAuth callback server waits for 5 minutes. If it times out:
1. Check that you authorized the app in your browser
2. Verify the callback URL in your OAuth app settings is `http://localhost:8080/`
3. Make sure port 8080 is not blocked by a firewall
4. Try again - the browser should automatically open

### "State mismatch" Error

This indicates a potential security issue (CSRF attack) or browser/timing problem:
1. Close all browser windows related to the authorization
2. Try the OAuth flow again
3. If it persists, check for browser extensions that might interfere

### Connection Works But Sync Fails

This is a separate issue from OAuth:
1. Verify your organization/username is correct
2. Verify the project number is correct
3. Check that you have access to the project in GitHub
4. Look at the error message in the sync status for details

## Technical Details

### OAuth Flow Implementation

WhatNow implements the OAuth 2.0 Authorization Code flow:

1. **Authorization Request**: Opens browser to GitHub's authorization page
2. **User Authorizes**: User grants permissions in browser
3. **Callback**: GitHub redirects to `http://localhost:8080/` with authorization code
4. **Local Server**: WhatNow runs a temporary HTTP server to receive the callback
5. **Token Exchange**: App exchanges authorization code for access token
6. **Token Storage**: Access token is saved to `github_token.pickle`
7. **Future Requests**: Token is loaded from disk and used for API requests

### Token Refresh

GitHub OAuth tokens for OAuth Apps do not expire by default. Unlike GitHub Apps, OAuth Apps receive long-lived tokens that remain valid until:
- The user revokes access
- The OAuth App is deleted
- The token is explicitly revoked

This means WhatNow doesn't need to implement token refresh logic for GitHub OAuth.

## Support

If you encounter issues with OAuth setup:
1. Check this documentation thoroughly
2. Verify your OAuth app settings on GitHub
3. Check WhatNow logs for detailed error messages
4. Open an issue on GitHub with details about your setup
