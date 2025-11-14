"""GitHub OAuth credentials configuration.

These credentials are for the WhatNow application's OAuth client.
Users authenticate through these credentials - no setup required.

IMPORTANT FOR DEVELOPERS:
To deploy this app, you need to replace these example credentials with real ones:
1. Go to https://github.com/settings/developers
2. Click "New OAuth App"
3. Set Authorization callback URL to: http://localhost:8080/
4. Replace the CLIENT_ID and CLIENT_SECRET below with your credentials

For personal/development use, create github_credentials_local.py (gitignored) with your own credentials.
"""

# OAuth 2.0 Client Configuration
# These are the WhatNow app's credentials (created by app developer)
# REPLACE THESE WITH REAL CREDENTIALS FOR PRODUCTION USE
GITHUB_CLIENT_ID = "Iv1.0123456789abcdef"
GITHUB_CLIENT_SECRET = "0123456789abcdef0123456789abcdef01234567"

# OAuth 2.0 Configuration
# GitHub OAuth scopes - using newer fine-grained permissions
SCOPES = ["repo", "read:project"]
REDIRECT_URI = "http://localhost:8080/"
AUTHORIZATION_BASE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"

# For development: you can override these with your own test credentials
# by creating 'github_credentials_local.py' (gitignored) with:
# GITHUB_CLIENT_ID = "your-test-client-id"
# GITHUB_CLIENT_SECRET = "your-test-secret"
try:
    from .github_credentials_local import GITHUB_CLIENT_ID as _LOCAL_CLIENT_ID
    from .github_credentials_local import GITHUB_CLIENT_SECRET as _LOCAL_CLIENT_SECRET

    GITHUB_CLIENT_ID = _LOCAL_CLIENT_ID  # noqa: F811
    GITHUB_CLIENT_SECRET = _LOCAL_CLIENT_SECRET  # noqa: F811
except ImportError:
    pass  # Use the embedded credentials above


def validate_credentials() -> tuple[bool, str]:
    """Validate that OAuth credentials are properly configured.

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for placeholder values
    if "0123456789" in GITHUB_CLIENT_ID or "example" in GITHUB_CLIENT_ID.lower():
        return False, (
            "GitHub OAuth credentials are not configured.\n\n"
            "The app is using placeholder credentials that will not work. "
            "To enable GitHub integration:\n\n"
            "1. Go to https://github.com/settings/developers\n"
            "2. Click 'New OAuth App'\n"
            "3. Set Authorization callback URL to: http://localhost:8080/\n"
            "4. Download credentials or create 'github_credentials_local.py'\n\n"
            "See docs/GITHUB_OAUTH_SETUP.md for detailed instructions."
        )

    if "0123456789" in GITHUB_CLIENT_SECRET or "example" in GITHUB_CLIENT_SECRET.lower():
        return False, (
            "GitHub OAuth client secret is not configured.\n\n"
            "Please set up real OAuth credentials. "
            "See docs/GITHUB_OAUTH_SETUP.md for instructions."
        )

    return True, ""


def are_credentials_configured() -> bool:
    """Check if OAuth credentials appear to be properly configured.

    Returns:
        True if credentials look valid, False if they appear to be placeholders
    """
    valid, _ = validate_credentials()
    return valid
