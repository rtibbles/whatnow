# WhatNow Web App

Vue3 + TypeScript static web app for activity tracking with TagTime Poisson pings.

## Features

- **Local-first architecture** with RxDB (IndexedDB storage)
- **TagTime-style ping tracking** with Poisson-distributed random pings
- **Work session management** with automatic time tracking
- **GitHub Projects integration** via OAuth Device Flow
- **Google Calendar integration** via PKCE OAuth
- **Progressive Web App** - installable, works offline

## Tech Stack

- **Vue 3** with Composition API
- **TypeScript** (strict mode)
- **RxDB** for reactive local database
- **Tailwind CSS** + Headless UI
- **Vite** for build tooling
- **Vitest** for testing

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── db/schemas/          # RxDB database schemas
├── composables/         # Vue composables
├── components/          # Vue components
├── services/            # Business logic (OAuth, sync, scheduler)
├── utils/               # Utility functions
└── tests/               # Unit and integration tests
```

## Configuration

Copy `.env.example` to `.env` and configure:

```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_GITHUB_CLIENT_ID=your-github-client-id
```

## Development

```bash
# Run tests in watch mode
npm test

# Run linter
npm run lint

# Format code
npm run format
```

## License

See parent project license.
