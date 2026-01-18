import { clsx } from 'clsx'
import { Target, TrendingDown, TrendingUp, Minus } from 'lucide-react'

function WeightProgress({ weightProgress }) {
  if (!weightProgress?.current) {
    return (
      <div className="text-gray-400 text-center py-8">
        No weight data available
      </div>
    )
  }

  const { current, target, to_goal, week_change } = weightProgress

  const progressPercent = target
    ? Math.min(100, Math.max(0, ((current - target) / (current * 0.2)) * 100))
    : 0

  const getTrendIcon = () => {
    if (week_change === null || week_change === undefined) return Minus
    return week_change < 0 ? TrendingDown : TrendingUp
  }

  const TrendIcon = getTrendIcon()

  return (
    <div className="space-y-4">
      {/* Current weight */}
      <div className="text-center">
        <span className="text-5xl font-bold text-white">
          {current.toFixed(1)}
        </span>
        <span className="text-2xl text-gray-400 ml-2">kg</span>
      </div>

      {/* Progress bar to goal */}
      {target && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-400">
            <span>Current</span>
            <span>Target: {target} kg</span>
          </div>
          <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full transition-all duration-500"
              style={{
                width: `${100 - Math.min(100, (to_goal / (current - target + to_goal)) * 100)}%`,
              }}
            />
          </div>
          <div className="flex items-center justify-center gap-2 text-sm">
            <Target className="w-4 h-4 text-green-400" />
            <span className={clsx(to_goal > 0 ? 'text-yellow-400' : 'text-green-400')}>
              {to_goal > 0 ? `${to_goal.toFixed(1)} kg to go` : 'Goal reached!'}
            </span>
          </div>
        </div>
      )}

      {/* Week change */}
      {week_change !== null && week_change !== undefined && (
        <div
          className={clsx(
            'flex items-center justify-center gap-2 p-3 rounded-lg',
            week_change < 0 ? 'bg-green-500/10' : week_change > 0 ? 'bg-red-500/10' : 'bg-gray-700'
          )}
        >
          <TrendIcon
            className={clsx(
              'w-5 h-5',
              week_change < 0 ? 'text-green-400' : week_change > 0 ? 'text-red-400' : 'text-gray-400'
            )}
          />
          <span
            className={clsx(
              'font-medium',
              week_change < 0 ? 'text-green-400' : week_change > 0 ? 'text-red-400' : 'text-gray-400'
            )}
          >
            {week_change > 0 ? '+' : ''}{week_change.toFixed(1)} kg this week
          </span>
        </div>
      )}
    </div>
  )
}

export default WeightProgress
