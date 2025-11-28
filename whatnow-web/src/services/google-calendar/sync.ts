import { getDatabase } from '../../db/database';
import { GoogleCalendarAPI, type GoogleCalendarEvent } from './api';
import { GoogleCalendarOAuth } from './oauth';
import type { CalendarEventDocument } from '../../db/schemas/calendar-event.schema';

/**
 * Google Calendar sync service
 * Syncs calendar events from Google Calendar API to local database
 */
export class GoogleCalendarSync {
  private oauth: GoogleCalendarOAuth;
  private api: GoogleCalendarAPI;

  constructor() {
    this.oauth = new GoogleCalendarOAuth();
    this.api = new GoogleCalendarAPI(this.oauth);
  }

  /**
   * Perform full sync of calendar events
   */
  async performSync(days: number = 7): Promise<{ added: number; updated: number; errors: number }> {
    const stats = { added: 0, updated: 0, errors: 0 };

    try {
      // Check if authenticated
      const isAuth = await this.oauth.isAuthenticated();
      if (!isAuth) {
        console.log('Not authenticated with Google Calendar');
        return stats;
      }

      // Fetch events from Google Calendar
      const events = await this.api.getUpcomingEvents(days);
      const db = await getDatabase();

      // Sync each event
      for (const event of events) {
        try {
          const calendarEvent = this.convertToCalendarEvent(event);

          // Check if event already exists
          const existing = await db.calendar_events
            .findOne({ selector: { id: calendarEvent.id } })
            .exec();

          if (existing) {
            // Update existing event
            await existing.update({
              $set: {
                summary: calendarEvent.summary,
                description: calendarEvent.description,
                startTime: calendarEvent.startTime,
                endTime: calendarEvent.endTime,
                location: calendarEvent.location,
                attendees: calendarEvent.attendees,
                url: calendarEvent.url,
                syncedAt: calendarEvent.syncedAt
              }
            });
            stats.updated++;
          } else {
            // Insert new event
            await db.calendar_events.insert(calendarEvent);
            stats.added++;
          }
        } catch (error) {
          console.error('Error syncing event:', event.id, error);
          stats.errors++;
        }
      }

      // Clean up old events (older than sync window)
      await this.cleanupOldEvents(days);

      console.log(`Calendar sync complete:`, stats);
      return stats;

    } catch (error) {
      console.error('Calendar sync failed:', error);
      throw error;
    }
  }

  /**
   * Convert Google Calendar event to our CalendarEventDocument format
   */
  private convertToCalendarEvent(event: GoogleCalendarEvent): CalendarEventDocument {
    // Parse start and end times
    const startTime = event.start.dateTime
      ? new Date(event.start.dateTime).getTime()
      : new Date(event.start.date!).getTime();

    const endTime = event.end.dateTime
      ? new Date(event.end.dateTime).getTime()
      : new Date(event.end.date!).getTime();

    // Extract attendee emails
    const attendees = event.attendees?.map(a => a.email || a.displayName || '') || [];

    return {
      id: `primary_${event.id}`, // Composite: calendar_id + event_id
      summary: event.summary || '(No title)',
      description: event.description || '',
      startTime,
      endTime,
      location: event.location || '',
      calendarId: 'primary',
      eventId: event.id,
      attendees,
      url: event.htmlLink,
      syncedAt: Date.now()
    };
  }

  /**
   * Clean up events older than the sync window
   */
  private async cleanupOldEvents(days: number): Promise<void> {
    const db = await getDatabase();
    const cutoffTime = Date.now() - (days * 24 * 60 * 60 * 1000);

    const oldEvents = await db.calendar_events
      .find({
        selector: {
          endTime: {
            $lt: cutoffTime
          }
        }
      })
      .exec();

    for (const event of oldEvents) {
      await event.remove();
    }

    if (oldEvents.length > 0) {
      console.log(`Cleaned up ${oldEvents.length} old calendar events`);
    }
  }

  /**
   * Get OAuth instance (for external use)
   */
  getOAuth(): GoogleCalendarOAuth {
    return this.oauth;
  }
}

/**
 * Standalone function for use in service worker
 */
export async function performCalendarSync(): Promise<void> {
  const sync = new GoogleCalendarSync();
  await sync.performSync();
}
