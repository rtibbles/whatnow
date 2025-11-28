/**
 * Retry utility with exponential backoff
 */

export interface RetryOptions {
  /**
   * Maximum number of retry attempts
   * @default 4
   */
  maxRetries?: number;

  /**
   * Initial delay in milliseconds
   * @default 2000
   */
  initialDelay?: number;

  /**
   * Maximum delay in milliseconds
   * @default 32000
   */
  maxDelay?: number;

  /**
   * Backoff multiplier
   * @default 2
   */
  backoffMultiplier?: number;

  /**
   * Function to determine if error is retryable
   * @default () => true
   */
  shouldRetry?: (error: unknown, attempt: number) => boolean;

  /**
   * Callback invoked before each retry
   */
  onRetry?: (error: unknown, attempt: number, delay: number) => void;
}

export interface RetryResult<T> {
  success: boolean;
  data?: T;
  error?: unknown;
  attempts: number;
}

/**
 * Default retry predicate - retries network errors and 5xx HTTP errors
 */
export function defaultShouldRetry(error: unknown, attempt: number): boolean {
  // Don't retry if we've exceeded max attempts
  if (attempt >= 4) {
    return false;
  }

  // Retry network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return true;
  }

  // Retry specific HTTP status codes
  if (error instanceof Response) {
    const status = error.status;
    // Retry on server errors (5xx) and rate limits (429)
    return status >= 500 || status === 429 || status === 408;
  }

  // Check if error has a status property (e.g., from fetch response)
  if (
    error &&
    typeof error === 'object' &&
    'status' in error &&
    typeof error.status === 'number'
  ) {
    const status = error.status;
    return status >= 500 || status === 429 || status === 408;
  }

  // Don't retry by default for unknown errors
  return false;
}

/**
 * Execute a function with exponential backoff retry logic
 *
 * @param fn - Async function to execute
 * @param options - Retry options
 * @returns Promise resolving to the result or throwing the final error
 *
 * @example
 * ```typescript
 * const result = await retryWithBackoff(
 *   () => fetch('https://api.github.com/user'),
 *   {
 *     maxRetries: 4,
 *     onRetry: (error, attempt, delay) => {
 *       console.log(`Retry attempt ${attempt} after ${delay}ms`);
 *     }
 *   }
 * );
 * ```
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 4,
    initialDelay = 2000,
    maxDelay = 32000,
    backoffMultiplier = 2,
    shouldRetry = defaultShouldRetry,
    onRetry
  } = options;

  let lastError: unknown;
  let attempt = 0;

  while (attempt <= maxRetries) {
    try {
      const result = await fn();
      return result;
    } catch (error) {
      lastError = error;
      attempt++;

      // Check if we should retry
      if (attempt > maxRetries || !shouldRetry(error, attempt)) {
        throw error;
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(initialDelay * Math.pow(backoffMultiplier, attempt - 1), maxDelay);

      // Add jitter (±25%) to prevent thundering herd
      const jitter = delay * 0.25 * (Math.random() * 2 - 1);
      const delayWithJitter = Math.max(0, delay + jitter);

      // Notify about retry
      if (onRetry) {
        onRetry(error, attempt, delayWithJitter);
      }

      // Wait before retrying
      await sleep(delayWithJitter);
    }
  }

  throw lastError;
}

/**
 * Execute a function with retry logic, returning a result object instead of throwing
 *
 * @param fn - Async function to execute
 * @param options - Retry options
 * @returns Promise resolving to RetryResult
 *
 * @example
 * ```typescript
 * const { success, data, error, attempts } = await tryWithBackoff(
 *   () => fetch('https://api.github.com/user')
 * );
 *
 * if (success) {
 *   console.log('Success after', attempts, 'attempts:', data);
 * } else {
 *   console.error('Failed after', attempts, 'attempts:', error);
 * }
 * ```
 */
export async function tryWithBackoff<T>(
  fn: () => Promise<T>,
  options: RetryOptions = {}
): Promise<RetryResult<T>> {
  let attempts = 0;

  try {
    const data = await retryWithBackoff(
      async () => {
        attempts++;
        return await fn();
      },
      {
        ...options,
        onRetry: (error, attempt, delay) => {
          attempts = attempt;
          options.onRetry?.(error, attempt, delay);
        }
      }
    );

    return {
      success: true,
      data,
      attempts
    };
  } catch (error) {
    return {
      success: false,
      error,
      attempts
    };
  }
}

/**
 * Sleep for a specified number of milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry predicate for GitHub API
 */
export function shouldRetryGitHub(error: unknown, attempt: number): boolean {
  if (attempt >= 4) return false;

  // Check for GitHub-specific rate limit headers
  if (
    error &&
    typeof error === 'object' &&
    'headers' in error &&
    error.headers instanceof Headers
  ) {
    const remaining = error.headers.get('x-ratelimit-remaining');
    if (remaining === '0') {
      // Rate limited - retry with longer delay
      return true;
    }
  }

  return defaultShouldRetry(error, attempt);
}

/**
 * Retry predicate for Google Calendar API
 */
export function shouldRetryGoogleCalendar(error: unknown, attempt: number): boolean {
  if (attempt >= 4) return false;

  // Don't retry on 401 (token expired - needs refresh)
  if (
    error &&
    typeof error === 'object' &&
    'status' in error &&
    error.status === 401
  ) {
    return false;
  }

  return defaultShouldRetry(error, attempt);
}
