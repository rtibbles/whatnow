import { describe, it, expect } from 'vitest';
import { pingSchema } from '../../db/schemas/ping.schema';
import { localTodoSchema } from '../../db/schemas/local-todo.schema';
import { githubTaskSchema } from '../../db/schemas/github-task.schema';
import { calendarEventSchema } from '../../db/schemas/calendar-event.schema';
import { workSessionSchema } from '../../db/schemas/work-session.schema';
import { syncMetadataSchema } from '../../db/schemas/sync-metadata.schema';
import { configSchema } from '../../db/schemas/config.schema';

describe('RxDB Schema Definitions', () => {
  it('ping schema should have correct structure', () => {
    expect(pingSchema).toBeDefined();
    expect(pingSchema.primaryKey).toBe('id');
    expect(pingSchema.properties.id).toBeDefined();
    expect(pingSchema.properties.timestamp).toBeDefined();
    expect(pingSchema.indexes).toContain('timestamp');
  });

  it('local TODO schema should have correct structure', () => {
    expect(localTodoSchema).toBeDefined();
    expect(localTodoSchema.primaryKey).toBe('id');
    expect(localTodoSchema.properties.urgency).toBeDefined();
    expect(localTodoSchema.properties.importance).toBeDefined();
    expect(localTodoSchema.indexes).toContain('isActive');
  });

  it('GitHub task schema should have correct structure', () => {
    expect(githubTaskSchema).toBeDefined();
    expect(githubTaskSchema.primaryKey).toBe('id');
    expect(githubTaskSchema.properties.iteration).toBeDefined();
    expect(githubTaskSchema.properties.state).toBeDefined();
  });

  it('calendar event schema should have correct structure', () => {
    expect(calendarEventSchema).toBeDefined();
    expect(calendarEventSchema.primaryKey).toBe('id');
    expect(calendarEventSchema.properties.startTime).toBeDefined();
    expect(calendarEventSchema.properties.endTime).toBeDefined();
  });

  it('work session schema should have correct structure', () => {
    expect(workSessionSchema).toBeDefined();
    expect(workSessionSchema.primaryKey).toBe('id');
    expect(workSessionSchema.properties.startTime).toBeDefined();
    expect(workSessionSchema.properties.totalSeconds).toBeDefined();
  });

  it('sync metadata schema should have correct structure', () => {
    expect(syncMetadataSchema).toBeDefined();
    expect(syncMetadataSchema.primaryKey).toBe('service');
    expect(syncMetadataSchema.properties.lastSync).toBeDefined();
    expect(syncMetadataSchema.properties.syncToken).toBeDefined();
  });

  it('config schema should have correct structure', () => {
    expect(configSchema).toBeDefined();
    expect(configSchema.primaryKey).toBe('key');
    expect(configSchema.properties.value).toBeDefined();
  });

  it('all primary keys should have maxLength', () => {
    const schemas = [
      { name: 'ping', schema: pingSchema },
      { name: 'localTodo', schema: localTodoSchema },
      { name: 'githubTask', schema: githubTaskSchema },
      { name: 'calendarEvent', schema: calendarEventSchema },
      { name: 'workSession', schema: workSessionSchema },
      { name: 'syncMetadata', schema: syncMetadataSchema },
      { name: 'config', schema: configSchema }
    ];

    schemas.forEach(({ name, schema }) => {
      const pkField = schema.primaryKey as string;
      const pkProperty = (schema.properties as any)[pkField];
      expect(
        pkProperty.maxLength,
        `${name} schema primary key should have maxLength`
      ).toBeDefined();
    });
  });

  it('indexed number fields should have min and max', () => {
    // Check ping.timestamp
    expect(pingSchema.properties.timestamp.minimum).toBeDefined();
    expect(pingSchema.properties.timestamp.maximum).toBeDefined();

    // Check calendar event times
    expect(calendarEventSchema.properties.startTime.minimum).toBeDefined();
    expect(calendarEventSchema.properties.startTime.maximum).toBeDefined();

    // Check work session times
    expect(workSessionSchema.properties.startTime.minimum).toBeDefined();
    expect(workSessionSchema.properties.startTime.maximum).toBeDefined();
  });

  it('indexed string fields should have maxLength', () => {
    // Check GitHub task indexed fields
    expect(githubTaskSchema.properties.iteration.maxLength).toBeDefined();
    expect(githubTaskSchema.properties.state.maxLength).toBeDefined();
  });
});
