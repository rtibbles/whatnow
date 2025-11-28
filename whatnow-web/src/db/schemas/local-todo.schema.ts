import type { RxJsonSchema } from 'rxdb';

export interface LocalTodoDocument {
  id: string;
  text: string;
  tags: string[];
  isActive: boolean;
  urgency: 1 | 2 | 3 | 4;
  importance: 1 | 2 | 3 | 4;
  createdAt: number;
  completedAt: number | null;
}

export const localTodoSchema: RxJsonSchema<LocalTodoDocument> = {
  version: 0,
  primaryKey: 'id',
  type: 'object',
  properties: {
    id: { type: 'string', maxLength: 36 },
    text: { type: 'string' },
    tags: {
      type: 'array',
      items: { type: 'string' },
      default: []
    },
    isActive: { type: 'boolean' },
    urgency: { type: 'number', minimum: 1, maximum: 4, multipleOf: 1 },
    importance: { type: 'number', minimum: 1, maximum: 4, multipleOf: 1 },
    createdAt: { type: 'number', multipleOf: 1, minimum: 0 },
    completedAt: { type: ['number', 'null'], multipleOf: 1, minimum: 0 }
  },
  required: ['id', 'text', 'tags', 'isActive', 'urgency', 'importance', 'createdAt'],
  indexes: ['isActive', ['urgency', 'importance']]
};
