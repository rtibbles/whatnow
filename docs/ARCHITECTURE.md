# WhatNow Architecture

## Overview

WhatNow is a local-first GTK Python application that combines TagTime-style activity tracking with external service integrations.

## Components

### 1. Database Layer (`database.py`, `models.py`)

- **Technology**: SQLAlchemy with SQLite backend
- **Purpose**: Local storage for all application data
- **Models**:
  - `Ping`: Activity tracking pings
  - `GitHubTask`: Synced GitHub Projects items
  - `CalendarEvent`: Synced Google Calendar events
  - `SyncMetadata`: Sync state tracking
  - `Config`: Application configuration

### 2. Poisson Scheduler (`poisson_scheduler.py`)

- **Technology**: Python threading, exponential distribution
- **Purpose**: Generate random pings based on Poisson distribution
- **Key Features**:
  - Configurable average gap (default: 45 minutes)
  - Runs in background thread
  - Callback-based notification

### 3. User Interface (`ui/`)

#### Main Window (`main_window.py`)
- Three-tab interface:
  - Activity Pings: History of recorded activities
  - GitHub Tasks: Synced tasks from GitHub Projects
  - Calendar: Upcoming events from Google Calendar
- Refresh functionality
- Settings access

#### Ping Dialog (`ping_dialog.py`)
- Modal dialog for activity input
- Fields: Activity, Tags, Notes
- Triggered by Poisson scheduler

#### Settings Dialog (`settings.py`)
- Configuration interface for:
  - Ping interval
  - Sync interval
  - GitHub credentials and project
  - Google Calendar credentials

#### System Tray (`tray_icon.py`)
- Always-visible tray icon
- Context menu for quick access
- Supports both AppIndicator3 and Gtk.StatusIcon

### 4. Sync Services (`sync/`)

#### GitHub Sync (`github_sync.py`)
- **API**: GitHub GraphQL API
- **Authentication**: Personal Access Token
- **Features**:
  - Syncs GitHub Projects (v2)
  - Supports both organization and user projects
  - Pagination support
  - Extracts: title, state, iteration, labels, assignees

#### Google Calendar Sync (`gcal_sync.py`)
- **API**: Google Calendar API v3
- **Authentication**: OAuth 2.0 (Desktop app flow)
- **Features**:
  - Incremental sync with sync tokens
  - Multiple calendar support
  - Caches OAuth tokens locally

### 5. Main Application (`__main__.py`)

- **Technology**: GTK Application framework
- **Responsibilities**:
  - Application lifecycle management
  - Component initialization and coordination
  - Background sync thread management
  - Event handling between components

## Data Flow

```
┌─────────────────────┐
│  Poisson Scheduler  │
│  (Background Thread)│
└──────────┬──────────┘
           │ Triggers ping
           ▼
┌─────────────────────┐
│    Ping Dialog      │
│   (GTK Window)      │
└──────────┬──────────┘
           │ User input
           ▼
┌─────────────────────┐
│   Database Layer    │
│   (SQLite+SQLAlchemy)│
└──────────┬──────────┘
           │
           ├──────────────────────┐
           │                      │
           ▼                      ▼
┌─────────────────────┐  ┌─────────────────┐
│   Main Window       │  │  Sync Services  │
│   (Display)         │  │  (Background)   │
└─────────────────────┘  └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                  ┌─────────────┐   ┌──────────────┐
                  │   GitHub    │   │   Google     │
                  │   Projects  │   │   Calendar   │
                  └─────────────┘   └──────────────┘
```

## Threading Model

1. **Main Thread**: GTK event loop, UI operations
2. **Scheduler Thread**: Poisson ping generation
3. **Sync Thread**: Background sync operations

All UI updates from background threads use `GLib.idle_add()` for thread safety.

## Configuration Storage

- **Location**: `~/.local/share/whatnow/whatnow.db` (database)
- **Config Table**: Key-value pairs stored in database
- **Sensitive Data**: API tokens stored in database (consider encryption for production)

## Security Considerations

- GitHub tokens stored in plain text (should be encrypted in production)
- Google OAuth tokens stored in pickle file
- Database file should have restricted permissions
- No data sent to external servers except configured APIs

## Future Enhancements

- End-to-end encryption for sensitive data
- Export/import functionality
- Analytics and insights on tracked activities
- Additional sync integrations (Todoist, Notion, etc.)
- Mobile companion app
- Cloud backup option (optional, user-controlled)
