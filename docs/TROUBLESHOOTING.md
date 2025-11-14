# Troubleshooting

## Common Issues

### Installation Issues

#### "No module named 'gi'" on Bazzite/Fedora Atomic

**Problem**: PyGObject (gi) not available in atomic system or Homebrew installation incomplete.

**Solution 1: Use Distrobox (Recommended)**:

*Note: GUI apps work perfectly in Distrobox - display and GPU are passed through automatically.*

```bash
# Create Fedora container
distrobox create --name whatnow-dev --image fedora:39
distrobox enter whatnow-dev

# Inside container, install all dependencies
sudo dnf install python3 python3-pip python3-gobject gtk3 \
                 python3-cairo-devel pkg-config gcc gobject-introspection-devel

# Install WhatNow
pip install -e .

# Test it works (GUI should appear on your desktop)
python -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('GTK OK!')"
```

**Solution 2: Layer packages on host**:
```bash
# Layer GTK and build tools
rpm-ostree install python3-gobject gtk3 python3-cairo-devel \
                   pkg-config gcc gobject-introspection-devel

# Reboot to apply changes
systemctl reboot

# After reboot
pip install --user -e .
```

**Solution 3: Fix Homebrew GTK** (if you started with Homebrew):
```bash
# Ensure all dependencies are present
brew install pygobject3 gtk+3 cairo pkg-config

# Set environment variables for build
export PKG_CONFIG_PATH="/home/linuxbrew/.linuxbrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"
export GI_TYPELIB_PATH="/home/linuxbrew/.linuxbrew/lib/girepository-1.0:$GI_TYPELIB_PATH"

# Try installing again
pip install -e .
```

#### "No module named 'gi'" (Other Systems)

**Problem**: PyGObject (gi) not installed or not found.

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0

# Fedora (Traditional)
sudo dnf install python3-gobject gtk3

# macOS
brew install pygobject3 gtk+3
```

#### "cairo/cairo.h: No such file or directory" on Bazzite

**Problem**: Cairo development headers not found during PyGObject compilation.

**Solution (Distrobox)**:
```bash
distrobox enter whatnow-dev
sudo dnf install cairo-devel cairo-gobject-devel
pip install --force-reinstall pycairo PyGObject
```

**Solution (Host system)**:
```bash
rpm-ostree install cairo-devel cairo-gobject-devel
systemctl reboot
```

#### "Namespace Gtk not available"

**Problem**: GTK 3 not installed on system.

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install gir1.2-gtk-3.0

# Fedora (Traditional)
sudo dnf install gtk3

# Fedora Atomic (via Distrobox)
distrobox enter whatnow-dev
sudo dnf install gtk3

# Fedora Atomic (layer on host)
rpm-ostree install gtk3
systemctl reboot

# macOS
brew install gtk+3
```

### Application Issues

#### Pings not appearing

**Problem**: Poisson scheduler not running or interval too long.

**Solutions**:
1. Check settings: Open Settings → General → verify "Average ping interval"
2. For testing, set interval to 1-5 minutes
3. Check logs for errors:
   ```bash
   whatnow 2>&1 | grep -i error
   ```

#### System tray icon not showing

**Problem**: System tray not supported or dependencies missing.

**Solutions**:
1. Install AppIndicator support (Ubuntu/Debian):
   ```bash
   sudo apt-get install gir1.2-appindicator3-0.1
   ```

2. If using GNOME, install TopIcons extension:
   ```bash
   # Via GNOME Extensions website
   # https://extensions.gnome.org/
   ```

3. The app should fallback to Gtk.StatusIcon automatically

### GitHub Integration Issues

#### "GitHub API error: 401"

**Problem**: Invalid or expired GitHub token.

**Solution**:
1. Verify token has correct scopes (`repo`, `project`)
2. Generate new token if needed
3. Update token in Settings → GitHub tab

#### "Project not found"

**Problem**: Incorrect organization/user or project number.

**Solutions**:
1. Verify organization/username is correct (case-sensitive)
2. Check project number in project URL:
   - URL format: `https://github.com/orgs/ORG/projects/NUMBER`
3. Ensure token has access to the organization/project

#### No tasks syncing

**Problem**: Project may be empty or iteration not set.

**Solutions**:
1. Verify project has items in GitHub
2. Check that items have content (issues/PRs)
3. View logs for sync errors:
   ```bash
   whatnow 2>&1 | grep -i github
   ```

### Google Calendar Issues

#### OAuth flow fails

**Problem**: Credentials file invalid or OAuth not configured correctly.

**Solutions**:
1. Verify credentials.json is for "Desktop app" type
2. Ensure Google Calendar API is enabled in Cloud Console
3. Delete token file and retry:
   ```bash
   rm ~/.local/share/whatnow/gcal_token.pickle
   ```

#### "Permission denied" during OAuth

**Problem**: Restricted OAuth scopes or app not verified.

**Solutions**:
1. During OAuth flow, click "Advanced" → "Go to [App Name] (unsafe)"
2. For production, verify your app with Google
3. Ensure calendar.readonly scope is requested

#### No events syncing

**Problem**: Calendar ID incorrect or no events in range.

**Solutions**:
1. For main calendar, use `primary`
2. For other calendars, get ID from Google Calendar:
   - Open calendar settings
   - Find "Calendar ID" in "Integrate calendar" section
3. Check that calendar has events in next 7 days

### Database Issues

#### "Database is locked"

**Problem**: Multiple instances running or file permissions issue.

**Solutions**:
1. Ensure only one instance is running:
   ```bash
   ps aux | grep whatnow
   ```
2. Kill other instances if found
3. Check database file permissions:
   ```bash
   ls -la ~/.local/share/whatnow/whatnow.db
   ```

#### Corrupted database

**Problem**: Database file corrupted (rare).

**Solution**:
1. Backup existing database:
   ```bash
   cp ~/.local/share/whatnow/whatnow.db ~/.local/share/whatnow/whatnow.db.bak
   ```
2. Delete and recreate:
   ```bash
   rm ~/.local/share/whatnow/whatnow.db
   whatnow  # Will create new database
   ```

### Performance Issues

#### High CPU usage

**Problem**: Sync running too frequently or large dataset.

**Solutions**:
1. Increase sync interval: Settings → General → Sync interval
2. Reduce number of synced calendars
3. Check for infinite loop in logs

#### Slow startup

**Problem**: Large database or slow initial sync.

**Solutions**:
1. Normal for first sync (GitHub/Calendar data)
2. Subsequent starts should be faster
3. Consider reducing data retention in future versions

## Getting Help

If you continue to experience issues:

1. Check logs:
   ```bash
   whatnow 2>&1 | tee whatnow.log
   ```

2. Open an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - System information (OS, GTK version)
   - Relevant log excerpts

3. For security issues, email directly instead of opening public issue
