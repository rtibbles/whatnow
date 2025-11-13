# Google Calendar OAuth Setup Guide

This guide explains how to set up Google Calendar OAuth credentials for WhatNow.

## Overview

WhatNow uses OAuth 2.0 to connect to your Google Calendar. The app includes embedded OAuth client credentials, but if you're:
- Running from source code
- Contributing to development
- Seeing "credentials not configured" errors

...you'll need to set up your own OAuth credentials.

## Quick Start (For Users)

If you're just using the app, OAuth should work automatically. Simply:
1. Open Settings → Google Calendar tab
2. Click "Connect Google Calendar"
3. Authorize in your browser

If you see an error about credentials not being configured, follow the Developer Setup below.

## Developer Setup

### Prerequisites
- Google account
- Google Cloud Console access
- 5-10 minutes

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: "WhatNow" (or your preferred name)
4. Click "Create"
5. Wait for project creation to complete

### Step 2: Enable Google Calendar API

1. In the Cloud Console, ensure your new project is selected
2. Go to "APIs & Services" → "Library"
3. Search for "Google Calendar API"
4. Click on it, then click "Enable"
5. Wait for API to be enabled

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted about OAuth consent screen:
   - Click "Configure Consent Screen"
   - Choose "External" user type
   - Click "Create"
   - Fill in:
     - App name: "WhatNow"
     - User support email: (your email)
     - Developer contact: (your email)
   - Click "Save and Continue" through all steps
   - On "Scopes" page, you don't need to add scopes manually
   - On "Test users" page, add your Gmail address
   - Click "Save and Continue"
   - Return to Credentials page

4. Click "Create Credentials" → "OAuth client ID" again
5. Choose "Desktop app" as application type
6. Name: "WhatNow Desktop" (or your preferred name)
7. Click "Create"

### Step 4: Configure WhatNow

You have two options:

#### Option A: Create credentials_local.py (Recommended)

1. In the WhatNow source directory, create:
   ```
   whatnow/sync/gcal_credentials_local.py
   ```

2. Add the following content (replace with your actual credentials):
   ```python
   # Local Google Calendar OAuth credentials
   # This file is gitignored - safe for development

   GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID_HERE.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
   ```

3. Copy the Client ID and Client Secret from Google Cloud Console
4. Save the file

#### Option B: Edit gcal_credentials.py Directly

1. Open `whatnow/sync/gcal_credentials.py`
2. Replace the placeholder values:
   ```python
   GOOGLE_CLIENT_ID = "your-actual-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET = "your-actual-client-secret"
   ```
3. Save the file

**Warning**: Don't commit real credentials to git if you plan to share your code!

### Step 5: Configure Redirect URI

1. In Google Cloud Console → Credentials
2. Click on your OAuth 2.0 Client ID
3. Under "Authorized redirect URIs", add:
   ```
   http://localhost:8080/
   ```
4. Click "Save"

### Step 6: Test Connection

1. Run WhatNow
2. Go to Settings → Google Calendar
3. Click "Connect Google Calendar"
4. Your browser should open
5. Sign in with your Google account
6. Grant calendar read-only permissions
7. You should see "✓ Connected" in settings

## Troubleshooting

### Error: "OAuth Credentials Not Configured"

**Cause**: The app is using placeholder credentials.

**Solution**: Follow the Developer Setup above.

### Error: "redirect_uri_mismatch"

**Cause**: The redirect URI in Google Cloud Console doesn't match what the app is using.

**Solution**:
1. Check the error message for the redirect URI
2. Add it in Google Cloud Console → Credentials → OAuth 2.0 Client ID → Authorized redirect URIs
3. Common URIs to add:
   - `http://localhost:8080/`
   - `http://localhost:8080`
   - `http://localhost/`

### Error: "This app isn't verified"

**Cause**: Your OAuth app is in testing mode and you're the only test user.

**Solution**:
- Click "Advanced" → "Go to WhatNow (unsafe)" - this is safe for your own app
- OR add users in Google Cloud Console → OAuth consent screen → Test users

### Can't see Calendar Events After Connecting

**Possible causes**:
1. Check Settings → Google Calendar → Calendar IDs
   - Make sure "primary" is listed (or your specific calendar ID)
2. Check that you granted calendar permissions during OAuth
3. Check logs for sync errors: Look for "Calendar sync error" messages

### How to Reset Connection

1. Delete the token file: `~/.local/share/whatnow/gcal_token.pickle`
2. In WhatNow settings, click "Connect Google Calendar" again
3. Re-authorize in browser

## Security Notes

### Is it safe to use my own OAuth credentials?

Yes! When you create OAuth credentials for desktop apps:
- The client secret can't truly be kept secret (it's in the source code)
- Security is enforced by Google when users authorize
- The app only gets the permissions users explicitly grant
- You can revoke access anytime in your Google Account settings

### Where are tokens stored?

- User access tokens: `~/.local/share/whatnow/gcal_token.pickle`
- These tokens grant access to YOUR calendar only
- File permissions: 600 (owner read/write only)
- Tokens are refreshed automatically when they expire

### Can I revoke access?

Yes, anytime:
1. Go to [Google Account → Security → Third-party apps](https://myaccount.google.com/permissions)
2. Find "WhatNow" or your app name
3. Click "Remove Access"

## For App Distributors

If you're distributing WhatNow to other users:

1. Create OAuth credentials as above
2. Replace the placeholder values in `gcal_credentials.py` with your credentials
3. **Important**: These credentials identify your OAuth app, not user data
4. Users will still need to authorize the app for their own calendars
5. Consider publishing your OAuth app (remove "Testing" status) for better UX

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)

## Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Open an issue on GitHub
- Review Google's OAuth documentation

