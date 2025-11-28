import type { RxJsonSchema } from 'rxdb';

export interface ConfigDocument {
  key: string;
  value: any;                    // JSON-serializable value
  updatedAt: number;
}

export const configSchema: RxJsonSchema<ConfigDocument> = {
  version: 0,
  primaryKey: 'key',
  type: 'object',
  properties: {
    key: { type: 'string', maxLength: 100 },
    value: {},                   // Any JSON value
    updatedAt: { type: 'number', multipleOf: 1, minimum: 0 }
  },
  required: ['key', 'value', 'updatedAt']
};
