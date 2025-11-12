"""Google Calendar sync service."""

import os
import pickle
import logging
from datetime import datetime, timedelta
from typing import Optional, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .gcal_credentials import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SCOPES, REDIRECT_URI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleCalendarSync:
    """Sync service for Google Calendar."""

    def __init__(self, db, calendar_ids: Optional[List[str]] = None):
        """Initialize Google Calendar sync service.

        Args:
            db: Database instance
            calendar_ids: List of calendar IDs to sync (default: ['primary'])
        """
        self.db = db
        self.calendar_ids = calendar_ids or ['primary']
        self.creds: Optional[Credentials] = None
        self.service = None

        # Token file path (stored next to database)
        data_dir = os.path.dirname(db.db_path)
        self.token_path = os.path.join(data_dir, 'gcal_token.pickle')

    def _authenticate(self) -> bool:
        """Authenticate with Google Calendar API.

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load existing token if available
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token_file:
                    self.creds = pickle.load(token_file)

            # If credentials are invalid or don't exist, authenticate
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    # Refresh expired token
                    logger.info("Refreshing Google Calendar token")
                    self.creds.refresh(Request())
                else:
                    # Get new credentials using embedded OAuth client
                    logger.info("Starting OAuth flow for Google Calendar")

                    # Build OAuth client config from embedded credentials
                    client_config = {
                        "installed": {
                            "client_id": GOOGLE_CLIENT_ID,
                            "client_secret": GOOGLE_CLIENT_SECRET,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": [REDIRECT_URI, "http://localhost"]
                        }
                    }

                    flow = InstalledAppFlow.from_client_config(
                        client_config, SCOPES
                    )
                    self.creds = flow.run_local_server(port=8080)

                # Save token for future use
                with open(self.token_path, 'wb') as token_file:
                    pickle.dump(self.creds, token_file)

            # Build service
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True

        except Exception as e:
            logger.error(f"Google Calendar authentication failed: {e}")
            return False

    def sync(self, days_ahead: int = 7) -> bool:
        """Sync Google Calendar events.

        Args:
            days_ahead: Number of days ahead to sync

        Returns:
            True if sync was successful, False otherwise
        """
        try:
            logger.info("Starting Google Calendar sync")

            # Authenticate if not already done
            if not self.service:
                if not self._authenticate():
                    raise Exception("Authentication failed")

            # Calculate time range
            now = datetime.utcnow()
            end_time = now + timedelta(days=days_ahead)

            # Format as RFC3339 timestamp
            time_min = now.isoformat() + 'Z'
            time_max = end_time.isoformat() + 'Z'

            synced_count = 0

            # Sync each calendar
            for calendar_id in self.calendar_ids:
                logger.info(f"Syncing calendar: {calendar_id}")

                try:
                    # Get metadata from last sync
                    sync_meta = self.db.get_sync_metadata(f"gcal_{calendar_id}")
                    sync_token = sync_meta.get('sync_token') if sync_meta else None

                    # Try incremental sync first if we have a token
                    if sync_token:
                        try:
                            events_result = self.service.events().list(
                                calendarId=calendar_id,
                                syncToken=sync_token,
                                maxResults=100,
                                singleEvents=True
                            ).execute()
                        except HttpError as e:
                            if e.resp.status == 410:
                                # Sync token expired, do full sync
                                logger.info(f"Sync token expired for {calendar_id}, doing full sync")
                                sync_token = None
                            else:
                                raise

                    # Full sync if no token or token expired
                    if not sync_token:
                        events_result = self.service.events().list(
                            calendarId=calendar_id,
                            timeMin=time_min,
                            timeMax=time_max,
                            maxResults=100,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()

                    events = events_result.get('items', [])

                    # Process events
                    for event in events:
                        # Skip events that are cancelled
                        if event.get('status') == 'cancelled':
                            continue

                        # Get event times
                        start = event.get('start', {})
                        end = event.get('end', {})

                        # Parse start/end times (could be date or dateTime)
                        start_time = self._parse_event_time(start)
                        end_time = self._parse_event_time(end)

                        if not start_time or not end_time:
                            continue

                        # Extract attendees
                        attendees = []
                        for attendee in event.get('attendees', []):
                            if 'email' in attendee:
                                attendees.append(attendee['email'])

                        # Create event record
                        event_data = {
                            "id": f"{calendar_id}_{event['id']}",
                            "summary": event.get('summary', 'Untitled Event'),
                            "description": event.get('description'),
                            "start_time": start_time,
                            "end_time": end_time,
                            "location": event.get('location'),
                            "calendar_id": calendar_id,
                            "attendees": attendees,
                            "url": event.get('htmlLink')
                        }

                        self.db.upsert_calendar_event(event_data)
                        synced_count += 1

                    # Save new sync token if available
                    new_sync_token = events_result.get('nextSyncToken')
                    if new_sync_token:
                        self.db.update_sync_metadata(
                            f"gcal_{calendar_id}",
                            success=True,
                            sync_token=new_sync_token
                        )
                    else:
                        self.db.update_sync_metadata(f"gcal_{calendar_id}", success=True)

                except Exception as e:
                    logger.error(f"Error syncing calendar {calendar_id}: {e}")
                    self.db.update_sync_metadata(
                        f"gcal_{calendar_id}",
                        success=False,
                        error_message=str(e)
                    )

            logger.info(f"Google Calendar sync completed: {synced_count} events synced")

            # Update main sync metadata
            self.db.update_sync_metadata("gcal", success=True)

            return True

        except Exception as e:
            logger.error(f"Google Calendar sync failed: {e}")
            self.db.update_sync_metadata("gcal", success=False, error_message=str(e))
            return False

    def _parse_event_time(self, time_dict: dict) -> Optional[int]:
        """Parse event time from Google Calendar format.

        Args:
            time_dict: Dictionary with 'dateTime' or 'date' key

        Returns:
            Unix timestamp or None
        """
        try:
            if 'dateTime' in time_dict:
                # Parse datetime
                dt_str = time_dict['dateTime']
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                return int(dt.timestamp())
            elif 'date' in time_dict:
                # All-day event - parse date and use start of day
                date_str = time_dict['date']
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return int(dt.timestamp())
        except Exception as e:
            logger.error(f"Error parsing event time: {e}")

        return None
