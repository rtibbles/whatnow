# Troubleshooting

## Common Issues

### Installation Issues

#### "No module named 'gi'" or GTK errors

**Problem**: PyGObject or GTK not installed.

**Solution: Use Ubuntu in Distrobox (works on any Linux):**

```bash
# Create Ubuntu container
distrobox create --name whatnow --image ubuntu:22.04
distrobox enter whatnow

# Install all dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                       libgirepository1.0-dev gobject-introspection

# Upgrade pip and setuptools (fixes "UNKNOWN" package and editable install issues)
pip install --upgrade pip setuptools wheel

# Test GTK works (GUI should be possible)
python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('GTK OK!')"

# Install WhatNow
cd /path/to/whatnow
pip install -e .
```

This works on **all Linux distributions** including Bazzite, Silverblue, Fedora, Arch, etc.
The GUI automatically appears on your desktop with full GPU support.

#### Package installs as "UNKNOWN-0.0.0"

**Problem**: Running `pip install .` shows "Successfully installed UNKNOWN-0.0.0" instead of "whatnow-0.1.0"

**Cause**: Old version of setuptools that doesn't fully support modern `pyproject.toml`

**Solution**:
```bash
# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Uninstall the broken package
pip uninstall UNKNOWN

# Reinstall properly
pip install -e .  # Use -e for editable/development install
```

#### "build backend is missing the 'build_editable' hook"

**Problem**: `pip install -e .` fails with editable install error

**Cause**: Old setuptools version (needs ≥64.0 for full PEP 660 support)

**Solution**:
```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```

#### "libgirepository-2.0.so.0: cannot open shared object file"

**Problem**: Running `whatnow` fails with ImportError about libgirepository

**Cause 1**: Missing GObject introspection development libraries

**Solution**:
```bash
# In distrobox container
sudo apt-get install -y libgirepository1.0-dev gobject-introspection

# Reinstall if needed
pip install --force-reinstall PyGObject
```

**Cause 2**: Leftover venv from host system interfering

Distrobox shares your home directory, so a `.venv/` created outside distrobox can interfere:

**Solution**:
```bash
# Remove any venv directories
cd /path/to/whatnow
rm -rf .venv

# Reinstall fresh
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

<details>
<summary>Alternative: Native installation (click to expand)</summary>

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                    libgirepository1.0-dev gobject-introspection
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk3
```

**Arch:**
```bash
sudo pacman -S python-gobject gtk3
```

**macOS:**
```bash
brew install pygobject3 gtk+3
```

</details>

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
