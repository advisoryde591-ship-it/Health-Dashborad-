import { format, parseISO } from 'date-fns'

export function formatDate(date) {
  if (!date) return ''
  const d = typeof date === 'string' ? parseISO(date) : date
  return format(d, 'MMM d, yyyy')
}

export function formatTime(date) {
  if (!date) return ''
  const d = typeof date === 'string' ? parseISO(date) : date
  return format(d, 'h:mm a')
}

export function formatNumber(num, decimals = 1) {
  if (num === null || num === undefined) return '-'
  return Number(num).toFixed(decimals)
}

export function formatDuration(minutes) {
  if (!minutes) return '-'
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  if (hours === 0) return `${mins}m`
  return `${hours}h ${mins}m`
}

export function formatWeight(kg) {
  if (kg === null || kg === undefined) return '-'
  return `${kg.toFixed(1)} kg`
}

export function formatPercentage(value) {
  if (value === null || value === undefined) return '-'
  return `${value.toFixed(0)}%`
}

export function getWeightChangeColor(change) {
  if (change === null || change === undefined) return 'text-gray-400'
  if (change < 0) return 'text-green-400'
  if (change > 0) return 'text-red-400'
  return 'text-gray-400'
}

export function getRecoveryColor(score) {
  if (score >= 67) return 'text-green-400'
  if (score >= 34) return 'text-yellow-400'
  return 'text-red-400'
}
