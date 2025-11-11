# Quick Start Guide

## Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip python3-gobject gtk3
```

**macOS:**
```bash
brew install python3 pygobject3 gtk+3
```

### 2. Install WhatNow

```bash
git clone https://github.com/yourusername/whatnow.git
cd whatnow
pip install -e .
```

## First Run

1. Launch WhatNow:
```bash
whatnow
```

2. On first run, you'll see a welcome dialog. Click OK to configure settings.

3. In the Settings dialog:
   - **General Tab**: Set your ping interval (default 45 minutes)
   - **GitHub Tab** (optional): Configure GitHub integration
   - **Google Calendar Tab** (optional): Configure calendar sync

4. Click "Save" to start using WhatNow!

## Basic Usage

### Activity Tracking

1. WhatNow will randomly ping you based on the configured interval
2. When a ping dialog appears, enter:
   - **Activity**: What you're doing (required)
   - **Tags**: Space-separated tags (optional)
   - **Notes**: Additional details (optional)
3. Click "Submit" to log the activity, or "Skip" to dismiss

### Viewing History

- Open the main window from the system tray
- The "Activity Pings" tab shows your recent activities
- Use the search function to filter activities

## Optional: GitHub Projects Integration

### Setup

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Create a token with these scopes:
   - `repo` (Full control of private repositories)
   - `project` (Full control of projects)
3. Copy the token

### Configuration

1. Open WhatNow settings
2. Go to the "GitHub" tab
3. Enter:
   - **Token**: Your GitHub personal access token
   - **Organization/User**: Your GitHub username or organization
   - **Project Number**: The number of your project (visible in project URL)
4. Save settings

WhatNow will sync your current iteration tasks every 30 minutes (configurable).

## Optional: Google Calendar Integration

### Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "Google Calendar API"
4. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download the credentials JSON file

### Configuration

1. Open WhatNow settings
2. Go to the "Google Calendar" tab
3. Click "Browse" and select your credentials JSON file
4. Enter calendar IDs to sync (one per line):
   - Use `primary` for your main calendar
   - Or specific calendar IDs from Google Calendar settings
5. Save settings

On first sync, a browser window will open for OAuth authorization.

## Tips

- **System Tray**: WhatNow runs in the background with a system tray icon
- **Window Management**: Close the window to minimize to tray; use the tray menu to show it again
- **Ping Distribution**: Pings are randomly distributed (Poisson), so intervals vary
- **Expected Pings**: With 45-minute average, expect ~32 pings per day

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
