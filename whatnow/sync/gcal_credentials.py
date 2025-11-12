"""Google Calendar OAuth credentials configuration.

These credentials are for the WhatNow application's OAuth client.
Users authenticate through these credentials - no setup required.

IMPORTANT FOR DEVELOPERS:
To deploy this app, you need to replace these example credentials with real ones:
1. Go to https://console.cloud.google.com/
2. Create a project and enable Google Calendar API
3. Create OAuth 2.0 Client ID (Desktop app type)
4. Replace the CLIENT_ID and CLIENT_SECRET below with your credentials
5. Add http://localhost:8080/ as an authorized redirect URI

For personal/development use, create gcal_credentials_local.py (gitignored) with your own credentials.
"""

# OAuth 2.0 Client Configuration
# These are the WhatNow app's credentials (created by app developer)
# REPLACE THESE WITH REAL CREDENTIALS FOR PRODUCTION USE
GOOGLE_CLIENT_ID = "123456789-abcdefghijklmnop.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "GOCSPX-example_secret_key_here"

# OAuth 2.0 Configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
REDIRECT_URI = 'http://localhost:8080/'

# For development: you can override these with your own test credentials
# by creating 'gcal_credentials_local.py' (gitignored) with:
# GOOGLE_CLIENT_ID = "your-test-client-id"
# GOOGLE_CLIENT_SECRET = "your-test-secret"
try:
    from .gcal_credentials_local import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
except ImportError:
    pass  # Use the embedded credentials above
