import type { RxJsonSchema } from 'rxdb';

export interface SyncMetadataDocument {
  service: string;               // 'github', 'gcal', 'gcal_{id}'
  lastSync: number;
  lastSuccess: number;
  errorMessage: string;
  syncToken: string;             // For incremental sync
}

export const syncMetadataSchema: RxJsonSchema<SyncMetadataDocument> = {
  version: 0,
  primaryKey: 'service',
  type: 'object',
  properties: {
    service: { type: 'string', maxLength: 100 },
    lastSync: { type: 'number', multipleOf: 1, minimum: 0 },
    lastSuccess: { type: 'number', multipleOf: 1, minimum: 0 },
    errorMessage: { type: 'string' },
    syncToken: { type: 'string' }
  },
  required: ['service', 'lastSync', 'lastSuccess', 'errorMessage', 'syncToken']
};
