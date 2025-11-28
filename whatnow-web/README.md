# WhatNow Web

A modern, offline-first Progressive Web App (PWA) for time tracking using the TagTime methodology. Built with Vue 3, TypeScript, and RxDB.

## Features

### Core Functionality
- **Poisson Ping Scheduling**: Stochastic time sampling based on TagTime methodology
- **TODO Management**: Track local tasks, GitHub issues, and Google Calendar events
- **Time Analysis**: Comprehensive time tracking with Poisson-weighted statistics
- **Multi-format Export**: Export data in CSV, TSV, and JSON formats

### Integrations
- **GitHub Integration**: OAuth Device Flow for GitHub issues and pull requests
- **Google Calendar**: OAuth PKCE flow for meeting tracking
- **Background Sync**: Automatic data synchronization with retry logic

### PWA Features
- **Offline Support**: Full offline functionality with IndexedDB
- **Install Prompt**: One-click installation on desktop and mobile
- **Service Worker**: Smart caching and background sync
- **Push Notifications**: Ping reminders with snooze support

### Data Management
- **Local Database**: RxDB with IndexedDB storage
- **Data Export/Import**: Full backup and restore capabilities
- **Settings Sync**: LocalStorage-based configuration persistence
- **Multi-device Support**: Sync across multiple devices

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Modern browser (Chrome 90+, Firefox 88+, Safari 14+)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whatnow/whatnow-web
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Development server**
   ```bash
   npm run dev
   ```
   Open http://localhost:5173

4. **Production build**
   ```bash
   npm run build
   npm run preview
   ```

### Deployment

The app is a static PWA and can be deployed to any static hosting service:

- **Netlify**: Drop the `dist` folder or connect your Git repo
- **Vercel**: Import your repository and select the `dist` folder
- **GitHub Pages**: Push the `dist` folder to `gh-pages` branch
- **Firebase Hosting**: `firebase deploy`

## Usage Guide

### First-Time Setup

1. **Start a Work Session**
   - Click "Start Session" to begin tracking
   - Set your ping interval (default: 45 minutes)
   - The first ping will arrive based on Poisson distribution

2. **Connect Integrations** (Optional)
   - **Google Calendar**: Click "Connect" in Calendar settings
   - **GitHub**: Click "Connect" in GitHub settings and follow Device Flow

3. **Configure Settings**
   - Adjust ping intervals
   - Enable/disable notifications
   - Set theme preferences
   - Configure background sync

### Daily Workflow

1. **Receive Ping Notification**
   - Notification appears at random intervals (Poisson distribution)
   - Click notification or open app to respond

2. **Record Your Activity**
   - Select or create a TODO item
   - Add tags (e.g., `work`, `coding`, `meeting`)
   - Add optional notes
   - Submit the ping

3. **Review Time Data**
   - Navigate to Time Analysis section
   - Select date range (last 7 days, 30 days, custom, etc.)
   - View breakdown by tags and TODOs
   - Export data for further analysis

### Tag System

Tags help categorize your time:
- Use lowercase, single words (e.g., `coding`, `meeting`, `email`)
- Separate multiple tags with spaces
- Common tags: `work`, `personal`, `break`, `admin`, `creative`
- Be consistent for better analysis

### Data Export

Export your data in multiple formats:
1. Go to Settings → Data Management
2. Click "Export All Data" (JSON format with settings)
3. Or use Time Analysis to export filtered data:
   - CSV: For spreadsheet analysis
   - TSV: For Excel compatibility
   - JSON: For programmatic access

## Architecture

### Technology Stack
- **Frontend**: Vue 3 with Composition API, TypeScript
- **Database**: RxDB with IndexedDB (Dexie adapter)
- **Build Tool**: Vite
- **UI Framework**: Tailwind CSS
- **PWA**: Vite PWA Plugin with Workbox
- **OAuth**: oauth4webapi (standards-compliant OAuth 2.1)

### Project Structure
```
src/
├── components/          # Vue components
│   ├── analysis/       # Time analysis components
│   ├── common/         # Reusable UI components
│   ├── layout/         # Layout components
│   ├── ping/           # Ping dialog and management
│   ├── pwa/            # PWA-specific components
│   ├── settings/       # Settings panels
│   └── work-session/   # Work session controls
├── composables/        # Vue composables (hooks)
│   ├── useDatabase.ts
│   ├── usePoissonScheduler.ts
│   ├── usePWA.ts
│   ├── useSettings.ts
│   ├── useTimeAnalysis.ts
│   └── useKeyboardShortcuts.ts
├── db/                 # Database layer
│   ├── database.ts     # RxDB initialization
│   └── schemas/        # Collection schemas
├── services/           # Business logic
│   ├── export.ts       # Data export service
│   ├── github/         # GitHub API integration
│   ├── google-calendar/# Google Calendar API
│   ├── poisson.ts      # Poisson distribution
│   ├── settings.ts     # Settings management
│   ├── time-analysis.ts# Time analysis engine
│   └── todos/          # TODO management
├── utils/              # Utility functions
│   └── retry.ts        # Exponential backoff retry
├── assets/             # Static assets
├── service-worker.ts   # Service worker
└── App.vue             # Root component
```

### Key Design Decisions

**Offline-First Architecture**
- All data stored locally in IndexedDB
- Background sync when online
- Optimistic UI updates
- Conflict resolution for synced data

**Poisson Ping Scheduling**
- `-ln(U) × λ` distribution (U = random, λ = interval)
- Each ping weighted by average gap for time calculation
- Missed ping detection with catch-up dialogs
- Pause/resume support

**OAuth Integration**
- Device Flow for GitHub (no client secret needed)
- PKCE for Google Calendar (secure for SPAs)
- Token storage in IndexedDB
- Automatic token refresh

## Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome  | 90+     | Full ✓  |
| Firefox | 88+     | Full ✓  |
| Safari  | 14+     | Full ✓  |
| Edge    | 90+     | Full ✓  |

**Required Features**:
- Service Workers
- IndexedDB
- Notifications API
- LocalStorage

**Progressive Enhancement**:
- Periodic Background Sync (Chrome only)
- Background Sync API (Chrome/Edge)
- Notification actions (varies by platform)

## Development

### Available Commands

```bash
# Development server with HMR
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npm run format
```

### Environment Variables

Create a `.env.local` file:
```env
# Google Calendar OAuth
VITE_GOOGLE_CLIENT_ID=your_google_client_id

# GitHub OAuth
VITE_GITHUB_CLIENT_ID=your_github_client_id
```

### Adding New Features

1. **New Service**: Add to `src/services/`
2. **New Composable**: Add to `src/composables/`
3. **New Component**: Add to appropriate `src/components/` subdirectory
4. **New Schema**: Add to `src/db/schemas/`

## Troubleshooting

### Notifications Not Working
- Check browser permissions in Settings
- Enable notifications in app Settings panel
- Ensure site is served over HTTPS (required for service workers)

### Sync Failing
- Check internet connection
- Verify OAuth tokens in Settings
- Check browser console for errors
- Try disconnecting and reconnecting integration

### Database Errors
- Clear browser data (Settings → Privacy)
- Or use app's "Clear All Data" in Settings
- Export data first to avoid losing pings!

### Service Worker Issues
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Unregister service worker in DevTools → Application → Service Workers
- Clear cache and reload

## Privacy & Security

- **Data Storage**: All data stored locally in browser
- **OAuth Tokens**: Stored in IndexedDB, never sent to third parties
- **No Analytics**: No tracking or telemetry
- **No Backend**: Purely client-side application
- **Export/Delete**: Full control over your data

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **TagTime**: Original concept by Dreeves and Messina
- **RxDB**: Reactive database framework
- **Vue.js**: Progressive JavaScript framework
- **Workbox**: Service worker library by Google

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: This README
- Code Comments: Inline documentation in source

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Desktop app (Tauri)
- [ ] End-to-end encryption
- [ ] Team collaboration features
- [ ] Advanced analytics and insights
- [ ] Integration with more services (Todoist, Trello, etc.)
