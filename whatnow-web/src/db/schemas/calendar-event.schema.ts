import type { RxJsonSchema } from 'rxdb';

export interface CalendarEventDocument {
  id: string;                    // Composite: calendar_id + event_id
  summary: string;
  description: string;
  startTime: number;
  endTime: number;
  location: string;
  calendarId: string;
  eventId: string;
  attendees: string[];
  url: string;
  syncedAt: number;
}

export const calendarEventSchema: RxJsonSchema<CalendarEventDocument> = {
  version: 0,
  primaryKey: 'id',
  type: 'object',
  properties: {
    id: { type: 'string', maxLength: 200 },
    summary: { type: 'string' },
    description: { type: 'string' },
    startTime: { type: 'number', multipleOf: 1, minimum: 0, maximum: 9999999999999 },
    endTime: { type: 'number', multipleOf: 1, minimum: 0, maximum: 9999999999999 },
    location: { type: 'string' },
    calendarId: { type: 'string' },
    eventId: { type: 'string' },
    attendees: {
      type: 'array',
      items: { type: 'string' },
      default: []
    },
    url: { type: 'string' },
    syncedAt: { type: 'number', multipleOf: 1, minimum: 0 }
  },
  required: [
    'id', 'summary', 'description', 'startTime', 'endTime',
    'location', 'calendarId', 'eventId', 'attendees', 'url', 'syncedAt'
  ],
  indexes: ['startTime', 'endTime', ['startTime', 'endTime']]
};
