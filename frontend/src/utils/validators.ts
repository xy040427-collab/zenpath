/**
 * Validate exam score (0-maxScore range typically)
 */
export function isValidScore(score: number, maxScore: number = 750): boolean {
  return !isNaN(score) && score >= 0 && score <= maxScore;
}

/**
 * Validate rank (positive integer)
 */
export function isValidRank(rank: number): boolean {
  return !isNaN(rank) && rank > 0 && Number.isInteger(rank);
}

/**
 * Validate phone number (Chinese mobile)
 */
export function isValidPhone(phone: string): boolean {
  return /^1[3-9]\d{9}$/.test(phone);
}

/**
 * Validate email
 */
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate non-empty string
 */
export function isNotEmpty(value: string): boolean {
  return value.trim().length > 0;
}

/**
 * Validate URL
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if value is within range
 */
export function isInRange(value: number, min: number, max: number): boolean {
  return value >= min && value <= max;
}
