import { clsx } from 'clsx'

function MetricCard({
  title,
  value,
  unit,
  subValue,
  icon: Icon,
  trend,
  color = 'green',
  size = 'normal',
}) {
  const colorClasses = {
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
    purple: 'text-purple-400',
  }

  const bgColorClasses = {
    green: 'bg-green-500/10',
    yellow: 'bg-yellow-500/10',
    red: 'bg-red-500/10',
    blue: 'bg-blue-500/10',
    purple: 'bg-purple-500/10',
  }

  return (
    <div
      className={clsx(
        'metric-card',
        size === 'large' && 'p-6'
      )}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-gray-400 text-sm uppercase tracking-wide">
          {title}
        </span>
        {Icon && (
          <div className={clsx('p-2 rounded-lg', bgColorClasses[color])}>
            <Icon className={clsx('w-4 h-4', colorClasses[color])} />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2">
        <span
          className={clsx(
            'font-bold',
            colorClasses[color],
            size === 'large' ? 'text-4xl' : 'text-2xl'
          )}
        >
          {value ?? '-'}
        </span>
        {unit && <span className="text-gray-400 text-sm">{unit}</span>}
      </div>

      {(subValue || trend) && (
        <div className="mt-2 flex items-center gap-2 text-sm">
          {subValue && <span className="text-gray-400">{subValue}</span>}
          {trend && (
            <span
              className={clsx(
                trend > 0 ? 'text-red-400' : 'text-green-400'
              )}
            >
              {trend > 0 ? '+' : ''}{trend}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default MetricCard
