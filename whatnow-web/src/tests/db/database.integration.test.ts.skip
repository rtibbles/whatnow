import { describe, it, expect } from 'vitest';
import { initDatabase, destroyDatabase } from '../../db/database';

describe('Database Initialization', () => {
  it('should initialize database with all collections', async () => {
    const db = await initDatabase();

    expect(db).toBeDefined();
    expect(db.name).toBe('whatnow');

    // Check all collections exist
    expect(db.collections.pings).toBeDefined();
    expect(db.collections.local_todos).toBeDefined();
    expect(db.collections.github_tasks).toBeDefined();
    expect(db.collections.calendar_events).toBeDefined();
    expect(db.collections.work_sessions).toBeDefined();
    expect(db.collections.sync_metadata).toBeDefined();
    expect(db.collections.config).toBeDefined();

    await destroyDatabase();
  });

  it('should return same instance on multiple calls', async () => {
    const db1 = await initDatabase();
    const db2 = await initDatabase();

    expect(db1).toBe(db2);

    await destroyDatabase();
  });

  it('should create and retrieve config document', async () => {
    const db = await initDatabase();

    // Create config
    await db.config.insert({
      key: 'test_key',
      value: { foo: 'bar' },
      updatedAt: Date.now()
    });

    // Retrieve config
    const doc = await db.config.findOne({ selector: { key: 'test_key' } }).exec();

    expect(doc).toBeDefined();
    expect(doc?.key).toBe('test_key');
    expect(doc?.value).toEqual({ foo: 'bar' });

    await destroyDatabase();
  });

  it('should create and retrieve ping document', async () => {
    const db = await initDatabase();

    const now = Date.now();
    await db.pings.insert({
      id: crypto.randomUUID(),
      timestamp: now,
      todoId: null,
      todoType: null,
      tags: ['coding', 'typescript'],
      notes: 'Test ping',
      eventId: null,
      isMeeting: false,
      createdAt: now
    });

    const pings = await db.pings.find().exec();

    expect(pings).toHaveLength(1);
    expect(pings[0].tags).toEqual(['coding', 'typescript']);
    expect(pings[0].notes).toBe('Test ping');

    await destroyDatabase();
  });

  it('should create and retrieve local TODO document', async () => {
    const db = await initDatabase();

    await db.local_todos.insert({
      id: crypto.randomUUID(),
      text: 'Test TODO',
      tags: ['work'],
      isActive: true,
      urgency: 3,
      importance: 4,
      createdAt: Date.now(),
      completedAt: null
    });

    const todos = await db.local_todos.find({ selector: { isActive: true } }).exec();

    expect(todos).toHaveLength(1);
    expect(todos[0].text).toBe('Test TODO');
    expect(todos[0].urgency).toBe(3);
    expect(todos[0].importance).toBe(4);

    await destroyDatabase();
  });
});
