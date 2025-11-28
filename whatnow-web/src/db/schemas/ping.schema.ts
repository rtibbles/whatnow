import type { RxJsonSchema } from 'rxdb';

export interface PingDocument {
  id: string;                    // UUID (RxDB requires string primary keys)
  timestamp: number;             // Unix timestamp (ms)
  todoId: string | null;
  todoType: 'github' | 'local' | 'meeting' | null;
  tags: string[];
  notes: string | null;
  eventId: string | null;
  isMeeting: boolean;
  createdAt: number;
}

export const pingSchema: RxJsonSchema<PingDocument> = {
  version: 0,
  primaryKey: 'id',
  type: 'object',
  properties: {
    id: { type: 'string', maxLength: 36 },
    timestamp: { type: 'number', multipleOf: 1, minimum: 0, maximum: 9999999999999 },
    todoId: { type: ['string', 'null'] },
    todoType: {
      type: ['string', 'null'],
      enum: ['github', 'local', 'meeting', null]
    },
    tags: {
      type: 'array',
      items: { type: 'string' },
      default: []
    },
    notes: { type: ['string', 'null'] },
    eventId: { type: ['string', 'null'] },
    isMeeting: { type: 'boolean' },
    createdAt: { type: 'number', multipleOf: 1, minimum: 0 }
  },
  required: ['id', 'timestamp', 'tags', 'isMeeting', 'createdAt'],
  indexes: ['timestamp']  // Removed composite index on nullable fields
};
