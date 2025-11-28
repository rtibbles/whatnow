import { createRxDatabase, addRxPlugin } from 'rxdb';
import { getRxStorageDexie } from 'rxdb/plugins/storage-dexie';
import { RxDBDevModePlugin } from 'rxdb/plugins/dev-mode';
import { RxDBUpdatePlugin } from 'rxdb/plugins/update';
import { RxDBQueryBuilderPlugin } from 'rxdb/plugins/query-builder';
import type { RxDatabase, RxCollection } from 'rxdb';

// Import schemas
import { pingSchema, type PingDocument } from './schemas/ping.schema';
import { localTodoSchema, type LocalTodoDocument } from './schemas/local-todo.schema';
import { githubTaskSchema, type GitHubTaskDocument } from './schemas/github-task.schema';
import { calendarEventSchema, type CalendarEventDocument } from './schemas/calendar-event.schema';
import { workSessionSchema, type WorkSessionDocument } from './schemas/work-session.schema';
import { syncMetadataSchema, type SyncMetadataDocument } from './schemas/sync-metadata.schema';
import { configSchema, type ConfigDocument } from './schemas/config.schema';

// Add plugins
if (import.meta.env.DEV) {
  addRxPlugin(RxDBDevModePlugin);
}
addRxPlugin(RxDBUpdatePlugin);
addRxPlugin(RxDBQueryBuilderPlugin);

// Collection types
export type PingCollection = RxCollection<PingDocument>;
export type LocalTodoCollection = RxCollection<LocalTodoDocument>;
export type GitHubTaskCollection = RxCollection<GitHubTaskDocument>;
export type CalendarEventCollection = RxCollection<CalendarEventDocument>;
export type WorkSessionCollection = RxCollection<WorkSessionDocument>;
export type SyncMetadataCollection = RxCollection<SyncMetadataDocument>;
export type ConfigCollection = RxCollection<ConfigDocument>;

// Database type
export type WhatNowDatabase = RxDatabase<{
  pings: PingCollection;
  local_todos: LocalTodoCollection;
  github_tasks: GitHubTaskCollection;
  calendar_events: CalendarEventCollection;
  work_sessions: WorkSessionCollection;
  sync_metadata: SyncMetadataCollection;
  config: ConfigCollection;
}>;

let dbInstance: WhatNowDatabase | null = null;

/**
 * Initialize RxDB database
 */
export async function initDatabase(): Promise<WhatNowDatabase> {
  if (dbInstance) {
    return dbInstance;
  }

  console.log('Initializing WhatNow database...');

  const db = await createRxDatabase<{
    pings: PingCollection;
    local_todos: LocalTodoCollection;
    github_tasks: GitHubTaskCollection;
    calendar_events: CalendarEventCollection;
    work_sessions: WorkSessionCollection;
    sync_metadata: SyncMetadataCollection;
    config: ConfigCollection;
  }>({
    name: 'whatnow',
    storage: getRxStorageDexie(),
    multiInstance: true,          // Support multiple tabs
    eventReduce: true,            // Performance optimization
    ignoreDuplicate: true         // Allow multiple instances (needed for testing)
  });

  // Add collections
  await db.addCollections({
    pings: { schema: pingSchema },
    local_todos: { schema: localTodoSchema },
    github_tasks: { schema: githubTaskSchema },
    calendar_events: { schema: calendarEventSchema },
    work_sessions: { schema: workSessionSchema },
    sync_metadata: { schema: syncMetadataSchema },
    config: { schema: configSchema }
  });

  console.log('Database initialized successfully');

  dbInstance = db;
  return db;
}

/**
 * Get database instance (must call initDatabase first)
 */
export function getDatabase(): WhatNowDatabase {
  if (!dbInstance) {
    throw new Error('Database not initialized. Call initDatabase() first.');
  }
  return dbInstance;
}

/**
 * Destroy database (for testing)
 */
export async function destroyDatabase(): Promise<void> {
  if (dbInstance) {
    await dbInstance.destroy();
    dbInstance = null;
  }
}
