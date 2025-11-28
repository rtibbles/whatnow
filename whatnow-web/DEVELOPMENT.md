# Development Guide

Technical documentation for WhatNow Web developers.

## Development Setup

### Prerequisites
- Node.js 18+ (LTS recommended)
- npm 9+
- Git
- Modern browser with DevTools
- (Optional) VS Code with recommended extensions

### Recommended VS Code Extensions
- Vue Language Features (Volar)
- TypeScript Vue Plugin (Volar)
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- RxDB DevTools

### Initial Setup

```bash
# Clone and install
git clone <repository-url>
cd whatnow/whatnow-web
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your OAuth credentials

# Start dev server
npm run dev
```

## Architecture Deep Dive

### State Management Pattern

**No Vuex/Pinia**: We use Vue 3 Composition API with composables for state management.

**Reactive Database**: RxDB provides reactive state through observables, automatically updating UI when data changes.

**Local-First**: All state stored in IndexedDB, synced to external services.

### Data Flow

```
User Action → Composable → Service → RxDB → Reactive Update → UI
     ↓
External API (GitHub/Calendar) → Background Sync → RxDB → UI
```

### Poisson Scheduler Implementation

The core time-tracking algorithm:

```typescript
// services/poisson.ts
export function generatePoissonInterval(averageMinutes: number): number {
  const U = Math.random(); // Uniform random [0,1)
  const lambda = averageMinutes; // Average interval
  return -Math.log(U) * lambda; // Exponential distribution
}
```

**Why Poisson?**
- Unbiased time sampling
- No correlation between pings
- Statistically rigorous time estimates
- Original TagTime methodology

**Time Calculation**:
```typescript
// Each ping represents average gap duration
totalTime = pingCount × averageGap
```

### RxDB Schema Design

**Collections**:
- `pings`: Time tracking records
- `local_todos`: User-created tasks
- `github_tasks`: Synced GitHub issues/PRs
- `calendar_events`: Synced Google Calendar events
- `work_sessions`: Work session tracking
- `sync_metadata`: Sync state management
- `config`: App configuration

**Key Schema Features**:
- Composite indexes for efficient queries
- Encrypted fields for sensitive data (future)
- Automatic timestamps
- Foreign key relationships

Example schema:
```typescript
// db/schemas/ping.schema.ts
export const pingSchema = {
  version: 0,
  type: 'object',
  properties: {
    id: { type: 'string', maxLength: 100 },
    timestamp: { type: 'number', minimum: 0 },
    tags: { type: 'array', items: { type: 'string' } },
    todoId: { type: 'string' },
    todoType: { type: 'string', enum: ['local', 'github', 'meeting'] },
    notes: { type: 'string' },
    isMeeting: { type: 'boolean' },
    eventId: { type: 'string' }
  },
  required: ['id', 'timestamp'],
  indexes: ['timestamp', 'todoId'],
  primaryKey: 'id'
};
```

### OAuth Flows

**GitHub (Device Flow)**:
1. Request device code from GitHub
2. Show user code to user
3. Poll for authorization
4. Store access token in IndexedDB
5. Use token for GitHub API calls

Benefits:
- No client secret needed
- Secure for public clients
- Great UX for desktop/mobile

**Google Calendar (PKCE Flow)**:
1. Generate code verifier and challenge
2. Redirect to Google OAuth
3. Exchange code for token
4. Store tokens in IndexedDB
5. Auto-refresh with refresh token

Benefits:
- Secure for SPAs
- No server required
- Standard OAuth 2.1

### Service Worker Architecture

**Custom Service Worker** (not generated):
- Manual precaching strategy
- Custom sync logic
- Direct IndexedDB access (RxDB not available in SW)
- Periodic background sync registration

**Workbox Integration**:
- Precache app shell
- Cache-first for images
- Network-first for API calls
- Stale-while-revalidate for fonts

**Background Sync**:
```typescript
// Periodic Sync (Chrome only)
registration.periodicSync.register('sync-external-data', {
  minInterval: 12 * 60 * 60 * 1000 // 12 hours
});

// One-off Background Sync
registration.sync.register('github-sync');
```

### Error Handling Strategy

**Layers**:
1. **Service Layer**: Catch and log errors, return Result types
2. **Composable Layer**: Handle errors, set error state
3. **Component Layer**: Display error UI
4. **Global**: Catch-all error boundary (future)

**Retry Logic**:
- Exponential backoff: 2s → 4s → 8s → 16s → 32s
- Jitter: ±25% to prevent thundering herd
- Smart retry predicates (don't retry 4xx except rate limits)

### Testing Strategy

**Unit Tests** (Vitest):
- Pure functions in services/
- Utility functions
- Business logic

**Component Tests** (Vitest + Testing Library):
- Vue components in isolation
- User interactions
- Accessibility

**E2E Tests** (Playwright - future):
- Critical user flows
- OAuth flows (mocked)
- Data export/import

### Performance Optimizations

**Bundle Splitting**:
- Vue vendor chunk
- RxDB chunk
- Route-based code splitting (future)

**Database**:
- Indexed queries for fast lookups
- Limit query results
- Pagination for large datasets

**UI**:
- Virtual scrolling for long lists (future)
- Skeleton loaders for perceived performance
- Debounced search inputs
- Lazy component loading

## Code Style Guide

### TypeScript

**Strict Mode**: Always enabled
```typescript
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

**Type Annotations**:
- Always annotate function parameters and return types
- Let TypeScript infer variable types when obvious
- Use interfaces for object shapes
- Use type aliases for unions

**Naming Conventions**:
- PascalCase: Types, Interfaces, Classes, Components
- camelCase: Variables, functions, methods
- SCREAMING_SNAKE_CASE: Constants
- kebab-case: File names (except components)

### Vue

**Composition API**: Always use `<script setup>` syntax

**Composable Naming**: Prefix with `use`
```typescript
// useDatabase.ts
export function useDatabase() {
  // ...
}
```

**Component Structure**:
```vue
<template>
  <!-- Template -->
</template>

<script setup lang="ts">
// Imports
import { ref } from 'vue';

// Props
const props = defineProps<{ foo: string }>();

// Emits
const emit = defineEmits<{ bar: [value: number] }>();

// Composables
const { data } = useData();

// Reactive state
const count = ref(0);

// Computed
const double = computed(() => count.value * 2);

// Methods
const increment = () => count.value++;

// Lifecycle
onMounted(() => {});
</script>

<style scoped>
/* Component styles */
</style>
```

**Props**: Use TypeScript types
```vue
<script setup lang="ts">
interface Props {
  title: string;
  count?: number;
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
});
</script>
```

### CSS

**Tailwind First**: Use Tailwind utilities when possible

**Custom CSS**: Use @layer for Tailwind integration
```css
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-blue-600 text-white rounded;
  }
}
```

**Scoped Styles**: Always scope component styles
```vue
<style scoped>
.component-class {
  /* Scoped to this component */
}
</style>
```

## Debugging

### Vue DevTools
- Install Vue DevTools browser extension
- Inspect component tree
- Monitor reactive state
- Track events

### RxDB DevTools
- Access in-memory database
- Query collections
- Inspect documents
- Monitor subscriptions

### Service Worker
- Chrome DevTools → Application → Service Workers
- View registered workers
- Force update
- Unregister for testing

### Network
- DevTools → Network tab
- Filter by type (XHR, Fetch)
- Inspect OAuth flows
- Monitor API calls

### Database
- Chrome DevTools → Application → IndexedDB
- Inspect databases
- View collections
- Query data

## Common Tasks

### Adding a New Collection

1. **Create Schema** (`src/db/schemas/my-collection.schema.ts`):
```typescript
export const myCollectionSchema = {
  version: 0,
  type: 'object',
  properties: {
    id: { type: 'string' },
    name: { type: 'string' }
  },
  required: ['id', 'name'],
  primaryKey: 'id'
};

export type MyCollectionDocument = {
  id: string;
  name: string;
};
```

2. **Add to Database** (`src/db/database.ts`):
```typescript
import { myCollectionSchema } from './schemas/my-collection.schema';

// Add collection type
export type MyCollectionCollection = RxCollection<MyCollectionDocument>;

// Update database type
export type WhatNowDatabase = RxDatabase<{
  // ... existing collections
  my_collection: MyCollectionCollection;
}>;

// Add to initialization
await db.addCollections({
  // ... existing collections
  my_collection: { schema: myCollectionSchema }
});
```

3. **Create Service** (`src/services/my-collection.ts`):
```typescript
import { getDatabase } from '../db/database';

export class MyCollectionService {
  async create(data: Partial<MyCollectionDocument>) {
    const db = getDatabase();
    await db.my_collection.insert(data);
  }

  async findById(id: string) {
    const db = getDatabase();
    return await db.my_collection.findOne(id).exec();
  }
}
```

4. **Create Composable** (`src/composables/useMyCollection.ts`):
```typescript
export function useMyCollection() {
  const service = new MyCollectionService();
  const items = ref<MyCollectionDocument[]>([]);

  const load = async () => {
    const db = getDatabase();
    items.value = await db.my_collection.find().exec();
  };

  onMounted(() => load());

  return { items, load };
}
```

### Adding OAuth Integration

1. **Create OAuth Service** (`src/services/my-oauth/oauth.ts`)
2. **Implement Token Storage** (IndexedDB via RxDB)
3. **Create API Client** with token refresh
4. **Add Settings Component** for connection UI
5. **Add Background Sync** in service worker

### Adding Export Format

1. **Update ExportService** (`src/services/export.ts`):
```typescript
static exportToXML(data: any[]): string {
  // Implementation
}
```

2. **Add Export Button** in UI
3. **Add MIME Type** for download

## Deployment

### Production Build

```bash
npm run build
```

Output: `dist/` folder

**Build Optimizations**:
- Minification
- Tree shaking
- Code splitting
- Gzip compression
- Source maps (for debugging)

### Environment Variables

**Development** (`.env.local`):
```env
VITE_GOOGLE_CLIENT_ID=dev_client_id
VITE_GITHUB_CLIENT_ID=dev_client_id
```

**Production** (hosting platform):
```env
VITE_GOOGLE_CLIENT_ID=prod_client_id
VITE_GITHUB_CLIENT_ID=prod_client_id
```

### Hosting Platforms

**Netlify**:
```toml
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

**Vercel**:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "routes": [
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

### CI/CD

**GitHub Actions** (`.github/workflows/deploy.yml`):
```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run build
      - run: npm run deploy
```

## Troubleshooting

### Build Failures

**TypeScript Errors**:
- Run `npm run type-check` to see all errors
- Fix type annotations
- Check for missing imports

**Vite Errors**:
- Clear cache: `rm -rf node_modules/.vite`
- Reinstall: `rm -rf node_modules && npm install`
- Update dependencies: `npm update`

### Database Issues

**Migration Errors**:
- Increment schema version
- Add migration strategy
- Clear database in dev: `localStorage.clear()`

**Query Performance**:
- Add indexes to schema
- Limit query results
- Use pagination

### Service Worker Issues

**Not Updating**:
- Increment version in manifest
- Force update in DevTools
- Clear cache

**Not Registering**:
- Check HTTPS (required except localhost)
- Check service worker scope
- Check console for errors

## Resources

- [Vue 3 Docs](https://vuejs.org/)
- [RxDB Docs](https://rxdb.info/)
- [Vite Docs](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [OAuth 2.1 Spec](https://oauth.net/2.1/)
- [Service Workers](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [TagTime Paper](https://messymatters.com/tagtime/)
