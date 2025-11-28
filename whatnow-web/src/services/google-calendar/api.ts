import { GoogleCalendarOAuth } from './oauth';
import { retryWithBackoff, shouldRetryGoogleCalendar } from '../../utils/retry';

/**
 * Google Calendar API response types
 */
export interface GoogleCalendarEvent {
  id: string;
  summary: string;
  description?: string;
  start: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  end: {
    dateTime?: string;
    date?: string;
    timeZone?: string;
  };
  location?: string;
  attendees?: Array<{
    email: string;
    displayName?: string;
    responseStatus?: string;
  }>;
  htmlLink: string;
  status: string;
}

export interface GoogleCalendarListResponse {
  items: GoogleCalendarEvent[];
  nextPageToken?: string;
}

/**
 * Google Calendar API client
 */
export class GoogleCalendarAPI {
  private readonly baseUrl = 'https://www.googleapis.com/calendar/v3';
  private oauth: GoogleCalendarOAuth;

  constructor(oauth: GoogleCalendarOAuth) {
    this.oauth = oauth;
  }

  /**
   * Fetch events from primary calendar with retry logic
   */
  async fetchEvents(
    timeMin: Date,
    timeMax: Date,
    maxResults: number = 100
  ): Promise<GoogleCalendarEvent[]> {
    return retryWithBackoff(
      async () => {
        const token = await this.oauth.getAccessToken();

        const url = new URL(`${this.baseUrl}/calendars/primary/events`);
        url.searchParams.set('timeMin', timeMin.toISOString());
        url.searchParams.set('timeMax', timeMax.toISOString());
        url.searchParams.set('maxResults', maxResults.toString());
        url.searchParams.set('singleEvents', 'true');
        url.searchParams.set('orderBy', 'startTime');

        const response = await fetch(url.toString(), {
          headers: {
            Authorization: `Bearer ${token}`,
            Accept: 'application/json'
          }
        });

        if (!response.ok) {
          if (response.status === 401) {
            // Token might be expired, try refreshing
            const newToken = await this.oauth.refreshAccessToken();
            return this.fetchEventsWithToken(url.toString(), newToken);
          }
          // Attach status for retry logic
          const error: any = new Error(`Calendar API error: ${response.statusText}`);
          error.status = response.status;
          throw error;
        }

        const data: GoogleCalendarListResponse = await response.json();
        return data.items || [];
      },
      {
        maxRetries: 4,
        initialDelay: 2000,
        shouldRetry: shouldRetryGoogleCalendar,
        onRetry: (error, attempt, delay) => {
          console.log(
            `[Google Calendar API] Retry attempt ${attempt} after ${Math.round(delay)}ms:`,
            error instanceof Error ? error.message : error
          );
        }
      }
    );
  }

  /**
   * Fetch events with a specific token (after refresh)
   */
  private async fetchEventsWithToken(url: string, token: string): Promise<GoogleCalendarEvent[]> {
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Calendar API error: ${response.statusText}`);
    }

    const data: GoogleCalendarListResponse = await response.json();
    return data.items || [];
  }

  /**
   * Get upcoming events (next 7 days)
   */
  async getUpcomingEvents(days: number = 7): Promise<GoogleCalendarEvent[]> {
    const now = new Date();
    const future = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);

    return this.fetchEvents(now, future);
  }

  /**
   * Get today's events
   */
  async getTodaysEvents(): Promise<GoogleCalendarEvent[]> {
    const now = new Date();
    const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const endOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);

    return this.fetchEvents(startOfDay, endOfDay);
  }
}
