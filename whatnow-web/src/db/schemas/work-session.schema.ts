import type { RxJsonSchema } from 'rxdb';

export interface WorkSessionDocument {
  id: string;
  startTime: number;
  endTime: number | null;
  totalSeconds: number;
}

export const workSessionSchema: RxJsonSchema<WorkSessionDocument> = {
  version: 0,
  primaryKey: 'id',
  type: 'object',
  properties: {
    id: { type: 'string', maxLength: 36 },
    startTime: { type: 'number', multipleOf: 1, minimum: 0, maximum: 9999999999999 },
    endTime: { type: ['number', 'null'], multipleOf: 1, minimum: 0, maximum: 9999999999999 },
    totalSeconds: { type: 'number', multipleOf: 1, minimum: 0 }
  },
  required: ['id', 'startTime', 'totalSeconds'],
  indexes: ['startTime']  // Removed endTime (nullable field can't be indexed)
};
