/**
 * Format a number with comma separators
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('zh-CN');
}

/**
 * Format a score value
 */
export function formatScore(score: number): string {
  return `${score}分`;
}

/**
 * Format rank with Chinese suffix
 */
export function formatRank(rank: number): string {
  if (rank >= 10000) {
    return `${(rank / 10000).toFixed(1)}万名`;
  }
  return `${rank}名`;
}

/**
 * Format probability as percentage
 */
export function formatProbability(prob: number): string {
  return `${Math.round(prob * 100)}%`;
}

/**
 * Match score display
 */
export function formatMatchScore(score: number): string {
  return `${Math.round(score)}%`;
}

/**
 * Currency formatter
 */
export function formatPrice(price: number): string {
  if (price === 0) return '免费';
  return `¥${price}`;
}

/**
 * Date formatter for Chinese locale
 */
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Format timestamp to relative time
 */
export function formatRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 30) return `${days}天前`;
  return formatDate(dateStr);
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.slice(0, length) + '…';
}

/**
 * Get ordinal Chinese number
 */
export function getChineseOrdinal(n: number): string {
  const map = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
  return map[n - 1] || String(n);
}
