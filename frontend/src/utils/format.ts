import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * Format large numbers for display
 * e.g., 1000 -> 1K, 10000 -> 1万, 100000000 -> 1亿
 */
export const formatNumber = (num: number): string => {
  if (num === undefined || num === null) return '0'
  if (num < 1000) return num.toString()
  if (num < 10000) return `${(num / 1000).toFixed(1)}K`
  if (num < 100000000) return `${(num / 10000).toFixed(1)}万`
  return `${(num / 100000000).toFixed(1)}亿`
}

/**
 * Format date relative to now
 * e.g., "2 hours ago", "3 days ago"
 */
export const formatRelativeTime = (date: string | number | Date): string => {
  return dayjs(date).fromNow()
}

/**
 * Alias for formatRelativeTime
 */
export const formatTimeAgo = formatRelativeTime

/**
 * Format date to standard format
 */
export const formatDate = (date: string | number | Date, format = 'YYYY-MM-DD HH:mm:ss'): string => {
  return dayjs(date).format(format)
}

/**
 * Format duration in seconds to mm:ss format
 */
export const formatDuration = (seconds: number): string => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * Calculate engagement rate
 */
export const calculateEngagementRate = (
  likes: number,
  comments: number,
  shares: number,
  views: number
): string => {
  if (!views) return '0%'
  const rate = ((likes + comments + shares) / views) * 100
  return `${rate.toFixed(2)}%`
}

/**
 * Extract ID from Douyin URL
 */
export const extractIdFromUrl = (url: string): { type: string; id: string } | null => {
  // Video URL patterns
  const videoPatterns = [
    /\/video\/(\d+)/,
    /item_ids=(\d+)/,
    /aweme_id=(\d+)/,
  ]
  for (const pattern of videoPatterns) {
    const match = url.match(pattern)
    if (match) {
      return { type: 'video', id: match[1] }
    }
  }

  // User URL patterns
  const userPatterns = [
    /sec_uid=([^&]+)/,
    /\/user\/([A-Za-z0-9_-]+)/,
  ]
  for (const pattern of userPatterns) {
    const match = url.match(pattern)
    if (match) {
      return { type: 'user', id: match[1] }
    }
  }

  // Live URL patterns
  const livePatterns = [
    /live\.douyin\.com\/(\d+)/,
    /room_id=(\d+)/,
  ]
  for (const pattern of livePatterns) {
    const match = url.match(pattern)
    if (match) {
      return { type: 'live', id: match[1] }
    }
  }

  return null
}

/**
 * Truncate text with ellipsis
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}
