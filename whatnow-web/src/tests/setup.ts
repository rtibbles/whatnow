// Vitest setup file
import { afterEach, beforeAll } from 'vitest';
import { destroyDatabase } from '../db/database';
import fakeIndexedDB from 'fake-indexeddb';
// @ts-ignore - fake-indexeddb type exports are not properly resolved
import FDBFactory from 'fake-indexeddb/lib/FDBFactory';
// @ts-ignore
import FDBKeyRange from 'fake-indexeddb/lib/FDBKeyRange';
// @ts-ignore
import FDBCursor from 'fake-indexeddb/lib/FDBCursor';
// @ts-ignore
import FDBCursorWithValue from 'fake-indexeddb/lib/FDBCursorWithValue';
// @ts-ignore
import FDBDatabase from 'fake-indexeddb/lib/FDBDatabase';
// @ts-ignore
import FDBIndex from 'fake-indexeddb/lib/FDBIndex';
// @ts-ignore
import FDBObjectStore from 'fake-indexeddb/lib/FDBObjectStore';
// @ts-ignore
import FDBOpenDBRequest from 'fake-indexeddb/lib/FDBOpenDBRequest';
// @ts-ignore
import FDBRequest from 'fake-indexeddb/lib/FDBRequest';
// @ts-ignore
import FDBTransaction from 'fake-indexeddb/lib/FDBTransaction';
// @ts-ignore
import FDBVersionChangeEvent from 'fake-indexeddb/lib/FDBVersionChangeEvent';

// Set up fake IndexedDB for testing
beforeAll(() => {
  // Set up all IndexedDB globals on both global and window
  const indexedDBGlobals = {
    indexedDB: fakeIndexedDB,
    IDBFactory: FDBFactory,
    IDBKeyRange: FDBKeyRange,
    IDBCursor: FDBCursor,
    IDBCursorWithValue: FDBCursorWithValue,
    IDBDatabase: FDBDatabase,
    IDBIndex: FDBIndex,
    IDBObjectStore: FDBObjectStore,
    IDBOpenDBRequest: FDBOpenDBRequest,
    IDBRequest: FDBRequest,
    IDBTransaction: FDBTransaction,
    IDBVersionChangeEvent: FDBVersionChangeEvent
  };

  Object.assign(global, indexedDBGlobals);
  if (typeof window !== 'undefined') {
    Object.assign(window, indexedDBGlobals);
  }

  console.log('IndexedDB setup for testing');
});

// Clean up database after each test
afterEach(async () => {
  try {
    await destroyDatabase();
  } catch (error) {
    // Ignore cleanup errors
    console.warn('Database cleanup warning:', error);
  }
});
