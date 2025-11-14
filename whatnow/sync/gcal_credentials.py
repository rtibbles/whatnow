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
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
REDIRECT_URI = "http://localhost:8080/"

# For development: you can override these with your own test credentials
# by creating 'gcal_credentials_local.py' (gitignored) with:
# GOOGLE_CLIENT_ID = "your-test-client-id"
# GOOGLE_CLIENT_SECRET = "your-test-secret"
try:
    from .gcal_credentials_local import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
except ImportError:
    pass  # Use the embedded credentials above


def validate_credentials() -> tuple[bool, str]:
    """Validate that OAuth credentials are properly configured.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for placeholder values
    if "123456789" in GOOGLE_CLIENT_ID or "example" in GOOGLE_CLIENT_ID.lower():
        return False, (
            "Google Calendar OAuth credentials are not configured.\n\n"
            "The app is using placeholder credentials that will not work. "
            "To enable Google Calendar integration:\n\n"
            "1. Go to https://console.cloud.google.com/\n"
            "2. Create a project and enable Google Calendar API\n"
            "3. Create OAuth 2.0 Client ID (Desktop app type)\n"
            "4. Download credentials or create 'gcal_credentials_local.py'\n\n"
            "See docs/GOOGLE_OAUTH_SETUP.md for detailed instructions."
        )

    if "example" in GOOGLE_CLIENT_SECRET.lower() or "YOUR_" in GOOGLE_CLIENT_SECRET:
        return False, (
            "Google Calendar OAuth client secret is not configured.\n\n"
            "Please set up real OAuth credentials. "
            "See docs/GOOGLE_OAUTH_SETUP.md for instructions."
        )

    return True, ""


def are_credentials_configured() -> bool:
    """Check if OAuth credentials appear to be properly configured.

    Returns:
        True if credentials look valid, False if they appear to be placeholders
    """
    valid, _ = validate_credentials()
    return valid
