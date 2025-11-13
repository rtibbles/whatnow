"""Application-wide constants and configuration values."""

# Ping scheduling constants
DEFAULT_PING_INTERVAL_MINUTES = 45  # Average time between pings (Poisson distribution)
MIN_PING_INTERVAL_MINUTES = 1
MAX_PING_INTERVAL_MINUTES = 180
PING_INTERVAL_INCREMENT = 1
PING_INTERVAL_LARGE_INCREMENT = 15

# Sync constants
DEFAULT_SYNC_INTERVAL_MINUTES = 30  # Time between background syncs
MIN_SYNC_INTERVAL_MINUTES = 5
MAX_SYNC_INTERVAL_MINUTES = 120
SYNC_INTERVAL_INCREMENT = 5
SYNC_INTERVAL_LARGE_INCREMENT = 15
INITIAL_SYNC_DELAY_SECONDS = 10  # Wait before first sync

# Calendar sync constants
DEFAULT_CALENDAR_DAYS_AHEAD = 7  # Days ahead to sync calendar events
DEFAULT_CALENDAR_IDS = ['primary']

# Retry constants
DEFAULT_MAX_RETRIES = 4
DEFAULT_INITIAL_RETRY_DELAY = 2.0  # seconds
DEFAULT_RETRY_BACKOFF_FACTOR = 2.0
DEFAULT_MAX_RETRY_DELAY = 60.0  # seconds
DEFAULT_NETWORK_TIMEOUT = 30  # seconds

# Pagination constants
DEFAULT_PAGE_SIZE = 100  # Number of items per page
DEFAULT_PINGS_LIMIT = 100

# UI constants
STATUS_MESSAGE_AUTO_CLEAR_SECONDS = 5  # Auto-clear status messages after this many seconds
STATUS_MESSAGE_SUCCESS_CLEAR_SECONDS = 3  # Shorter for success messages
TOOLTIP_UPDATE_INTERVAL_SECONDS = 30  # Update system tray tooltip every 30 seconds

# GitHub API constants
GITHUB_API_ENDPOINT = "https://api.github.com/graphql"
GITHUB_MAX_ITEMS_PER_PAGE = 100

# Google Calendar API constants
GCAL_MAX_RESULTS = 100

# Thread shutdown timeout
THREAD_SHUTDOWN_TIMEOUT_SECONDS = 10

# Database constants
DB_FILENAME = 'whatnow.db'
ALEMBIC_CONFIG_FILENAME = 'alembic.ini'

# TagTime statistical constants
# With Poisson distribution, the fraction of pings tagged with activity X
# approximates the fraction of time spent on activity X
POISSON_DISTRIBUTION_NOTE = (
    "TagTime uses Poisson distribution for random pings. "
    "A 45-minute average means ~32 pings per day."
)
