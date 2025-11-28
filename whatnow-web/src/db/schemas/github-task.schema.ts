import type { RxJsonSchema } from 'rxdb';

export interface GitHubTaskDocument {
  id: string;                    // GitHub issue/PR ID
  title: string;
  body: string;
  state: 'OPEN' | 'IN_PROGRESS' | 'DONE';
  projectName: string;
  iteration: string;             // Current sprint/iteration
  urgency: 1 | 2 | 3 | 4;
  importance: 1 | 2 | 3 | 4;
  assignees: string[];
  labels: string[];
  url: string;
  createdAt: number;
  updatedAt: number;
  syncedAt: number;
}

export const githubTaskSchema: RxJsonSchema<GitHubTaskDocument> = {
  version: 0,
  primaryKey: 'id',
  type: 'object',
  properties: {
    id: { type: 'string', maxLength: 100 },
    title: { type: 'string' },
    body: { type: 'string' },
    state: {
      type: 'string',
      enum: ['OPEN', 'IN_PROGRESS', 'DONE'],
      maxLength: 20
    },
    projectName: { type: 'string' },
    iteration: { type: 'string', maxLength: 200 },
    urgency: { type: 'number', minimum: 1, maximum: 4, multipleOf: 1 },
    importance: { type: 'number', minimum: 1, maximum: 4, multipleOf: 1 },
    assignees: {
      type: 'array',
      items: { type: 'string' },
      default: []
    },
    labels: {
      type: 'array',
      items: { type: 'string' },
      default: []
    },
    url: { type: 'string' },
    createdAt: { type: 'number', multipleOf: 1, minimum: 0 },
    updatedAt: { type: 'number', multipleOf: 1, minimum: 0 },
    syncedAt: { type: 'number', multipleOf: 1, minimum: 0 }
  },
  required: [
    'id', 'title', 'body', 'state', 'projectName', 'iteration',
    'urgency', 'importance', 'assignees', 'labels', 'url',
    'createdAt', 'updatedAt', 'syncedAt'
  ],
  indexes: ['iteration', ['urgency', 'importance'], 'state']
};
