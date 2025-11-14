# WhatNow - TagTime Activity Tracker

A local-first GTK Python application for activity tracking with TagTime-style Poisson-distributed pings, GitHub Projects integration, and Google Calendar sync.

## Features

- **TagTime-style Activity Tracking**: Random pings based on Poisson distribution to track what you're doing
- **Local-First Architecture**: All data stored locally in SQLite database
- **GitHub Projects Integration**: Sync with GitHub Projects to track iteration tasks
- **Google Calendar Sync**: Integrate with Google Calendar to see your schedule
- **System Tray Operation**: Runs in background with system tray icon
- **Privacy-Focused**: Your data stays on your machine
- **Cross-Platform**: Works on Linux, macOS, and Windows (where GTK is supported)

## Quick Start

```bash
# Create Ubuntu container (works on any Linux distro)
distrobox create --name whatnow --image ubuntu:22.04
distrobox enter whatnow

# Inside container, install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                       libgirepository1.0-dev gobject-introspection

# Upgrade pip and setuptools (required for pyproject.toml)
pip install --upgrade pip setuptools wheel

# Clone and install WhatNow
git clone https://github.com/yourusername/whatnow.git
cd whatnow
pip install -e .

# Run (appears on your desktop automatically)
whatnow
```

For detailed installation instructions, see [Quick Start Guide](docs/QUICKSTART.md).

## Why WhatNow?

Traditional time tracking requires you to remember to start/stop timers. WhatNow uses **TagTime's approach**: random sampling based on Poisson distribution. This gives you an unbiased picture of how you spend your time without the burden of manual tracking.

### How It Works

1. **Random Pings**: Get randomly timed notifications (average 45 minutes apart)
2. **Quick Responses**: Answer "What are you doing?" with activity + tags
3. **Automatic Insights**: Build a statistical picture of your time usage
4. **Context Integration**: See your GitHub tasks and calendar alongside activities

## Architecture

- **GUI**: Python GTK 3 (PyGObject)
- **Database**: SQLite with SQLAlchemy ORM
- **APIs**: GitHub GraphQL API, Google Calendar API v3
- **Ping Distribution**: Poisson distribution (configurable average gap)

## Installation

### Recommended: Distrobox (All Linux Distributions)

Works on Bazzite, Silverblue, Fedora, Arch, openSUSE, or any Linux distro:

```bash
# Create Ubuntu container
distrobox create --name whatnow --image ubuntu:22.04
distrobox enter whatnow

# Inside container, install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                       libgirepository1.0-dev gobject-introspection

# Upgrade pip and setuptools (required for pyproject.toml)
pip install --upgrade pip setuptools wheel

# Clone and install
cd /path/to/whatnow  # or clone: git clone <url>
pip install -e ".[dev]"

# Run - GUI appears on your desktop automatically!
whatnow
```

**Why Distrobox?**
- Works on immutable systems (Bazzite, Silverblue)
- Full GUI support with GPU acceleration
- No system modifications needed
- Same environment for everyone

### Alternative: Native Installation

<details>
<summary>Click to expand native installation instructions</summary>

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                    libgirepository1.0-dev gobject-introspection
pip install -e .
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk3
pip install -e .
```

**Arch:**
```bash
sudo pacman -S python-gobject gtk3
pip install -e .
```

**macOS:**
```bash
brew install pygobject3 gtk+3
pip install -e .
```

</details>

## Usage

### First Run

```bash
whatnow
```

On first run, you'll need to configure:
1. Ping interval preferences
2. GitHub Personal Access Token (optional, with `repo` and `project` scopes)
3. Google Calendar connection (optional, simple browser-based OAuth)

### Running the App

```bash
whatnow
```

The app will:
- Run in the background with system tray icon
- Show random pings based on Poisson distribution
- Sync with GitHub Projects and Google Calendar at configured intervals

## Configuration

Configuration is stored in the SQLite database at `~/.local/share/whatnow/whatnow.db`

### GitHub Setup

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Create a token with `repo` and `project` scopes
3. Enter the token in WhatNow settings

### Google Calendar Setup

1. Open WhatNow settings (Settings → Google Calendar tab)
2. Click "Connect Google Calendar"
3. Authorize in your browser when prompted
4. Done! Meetings will be automatically detected and logged

No additional setup required - the app handles OAuth authentication automatically.

## Data Storage

All data is stored locally in `~/.local/share/whatnow/whatnow.db` (SQLite database)

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)**: Get up and running quickly
- **[Architecture](docs/ARCHITECTURE.md)**: Technical overview and design decisions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Contributing](CONTRIBUTING.md)**: How to contribute to the project

## Development

### Project Structure

```
whatnow/
├── __init__.py
├── __main__.py          # Entry point and main application
├── database.py          # SQLAlchemy database layer
├── models.py            # SQLAlchemy models
├── poisson_scheduler.py # Poisson ping scheduler
├── ui/
│   ├── __init__.py
│   ├── main_window.py   # Main GTK window
│   ├── ping_dialog.py   # Ping dialog
│   ├── settings.py      # Settings dialog
│   └── tray_icon.py     # System tray icon
└── sync/
    ├── __init__.py
    ├── github_sync.py   # GitHub Projects sync
    └── gcal_sync.py     # Google Calendar sync
```

### Development Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run from source
python -m whatnow
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## Roadmap

- [ ] Data export (CSV, JSON)
- [ ] Activity analytics and visualizations
- [ ] Additional integrations (Todoist, Notion, Jira)
- [ ] Encrypted credential storage
- [ ] Unit and integration tests
- [ ] Optional cloud backup
- [ ] Mobile companion app

## Inspiration

This project is inspired by:
- [TagTime](http://tagtime.software/) - Original Poisson-distributed time tracking
- [GTD](https://gettingthingsdone.com/) - Time management methodology
- Local-first software principles

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/whatnow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/whatnow/discussions)
- **Documentation**: [docs/](docs/)

## Acknowledgments

- TagTime project for the Poisson distribution approach
- PyGObject team for GTK Python bindings
- SQLAlchemy for excellent ORM
- All contributors
