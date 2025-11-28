// App-wide constants (ported from Python)

export const DEFAULT_PING_INTERVAL_MINUTES = 45;
export const DEFAULT_SYNC_INTERVAL_MINUTES = 30;
export const DEFAULT_CALENDAR_DAYS_AHEAD = 7;
export const INITIAL_SYNC_DELAY_SECONDS = 10;
export const TOOLTIP_UPDATE_INTERVAL_SECONDS = 30;

// Ping schedule generation
export const DEFAULT_SCHEDULE_PING_COUNT = 50; // ~30 hours at 45min average

// Urgency levels
export const URGENCY = {
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  URGENT: 4
} as const;

// Importance levels
export const IMPORTANCE = {
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4
} as const;

export type Urgency = typeof URGENCY[keyof typeof URGENCY];
export type Importance = typeof IMPORTANCE[keyof typeof IMPORTANCE];
