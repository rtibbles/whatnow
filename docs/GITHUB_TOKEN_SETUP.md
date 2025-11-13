# GitHub Personal Access Token Setup

This guide walks you through creating a GitHub Personal Access Token (PAT) for WhatNow to sync with your GitHub Projects.

## Why Do I Need This?

WhatNow integrates with GitHub Projects to:
- Automatically sync your current iteration tasks
- Show you relevant tasks during pings
- Track time spent on specific GitHub issues

## Step-by-Step Instructions

### 1. Go to GitHub Settings

1. Log into [GitHub.com](https://github.com)
2. Click your profile photo in the top-right corner
3. Click **Settings**
4. Scroll down to **Developer settings** (in the left sidebar)
5. Click **Personal access tokens**
6. Click **Tokens (classic)**

### 2. Generate New Token

1. Click **Generate new token** → **Generate new token (classic)**
2. GitHub may ask for your password - enter it and continue

### 3. Configure Token Settings

**Note/Description:**
Enter something descriptive like "WhatNow Activity Tracker"

**Expiration:**
Choose your preferred expiration:
- **90 days** (recommended for security)
- **No expiration** (convenient but less secure)

**Select scopes:**
Check the following boxes:
- ☑️ `repo` (Full control of private repositories)
- ☑️ `project` (Full control of projects)
  - ☑️ `read:project` (Read access to projects)
  - ☑️ `write:project` (Write access to projects)

### 4. Generate and Copy Token

1. Scroll to the bottom and click **Generate token**
2. **IMPORTANT:** Copy the token immediately!
   - It starts with `ghp_`
   - You'll only see it once
   - Store it somewhere safe (password manager recommended)

### 5. Add Token to WhatNow

1. Open WhatNow
2. Click the Settings button (⚙️ icon) or press `Ctrl+,`
3. Go to the **GitHub** tab
4. Paste your token into the "Personal Access Token" field
5. Enter your GitHub organization or username
6. Enter your project number (found in the project URL)
7. Click **Test Connection** to verify it works
8. Click **Save**

## Finding Your Project Number

The project number is in your GitHub Project URL:

```
https://github.com/orgs/YOUR_ORG/projects/42
                                           ^^
                                    This is your project number
```

For user projects:
```
https://github.com/users/YOUR_USERNAME/projects/42
                                               ^^
                                    This is your project number
```

## Troubleshooting

### "Connection failed: 401 Unauthorized"

- Your token may be invalid or expired
- Make sure you copied the entire token (starts with `ghp_`)
- Regenerate the token if needed

### "Connection failed: 404 Not Found"

- Check your organization/username is correct
- Verify the project number is correct
- Make sure the project exists and you have access to it

### "Connection failed: 403 Forbidden"

- The token may not have the required scopes
- Regenerate the token with `repo` and `project` scopes

### Token Expired

If your token expires:
1. Go back to GitHub Settings → Personal access tokens
2. Click on your WhatNow token
3. Click **Regenerate token**
4. Copy the new token
5. Update it in WhatNow settings

## Security Best Practices

1. **Never share your token** - It's like a password
2. **Use expiration dates** - 90 days is a good balance
3. **Store securely** - WhatNow stores tokens in your system keyring
4. **Regenerate if compromised** - Delete the old token on GitHub immediately
5. **Use minimal scopes** - Only grant the permissions needed

## Need Help?

If you're still having trouble:
1. Check the WhatNow logs: `~/.local/share/whatnow/whatnow.log`
2. File an issue: [GitHub Issues](https://github.com/anthropics/whatnow/issues)
3. Ensure your GitHub organization allows Personal Access Tokens
