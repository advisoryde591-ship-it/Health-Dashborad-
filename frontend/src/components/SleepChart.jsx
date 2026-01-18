import { clsx } from 'clsx'

function SleepChart({ sleep }) {
  if (!sleep) {
    return (
      <div className="text-gray-400 text-center py-8">
        No sleep data available
      </div>
    )
  }

  const stages = [
    { key: 'awake', label: 'Awake', color: 'bg-gray-500', percentage: sleep.awake_percentage },
    { key: 'light', label: 'Light', color: 'bg-blue-400', percentage: sleep.light_sleep_percentage },
    { key: 'deep', label: 'Deep', color: 'bg-purple-500', percentage: sleep.deep_sleep_percentage },
    { key: 'rem', label: 'REM', color: 'bg-pink-400', percentage: sleep.rem_sleep_percentage },
  ]

  const totalMinutes = sleep.actual_sleep_minutes || sleep.total_duration_minutes || 0
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  return (
    <div className="space-y-4">
      {/* Total sleep time */}
      <div className="text-center">
        <span className="text-4xl font-bold text-white">
          {hours}h {minutes}m
        </span>
        <p className="text-gray-400 text-sm mt-1">Total Sleep</p>
      </div>

      {/* Sleep stages bar */}
      <div className="h-8 flex rounded-lg overflow-hidden">
        {stages.map((stage) => (
          stage.percentage > 0 && (
            <div
              key={stage.key}
              className={clsx(stage.color, 'transition-all')}
              style={{ width: `${stage.percentage}%` }}
              title={`${stage.label}: ${stage.percentage}%`}
            />
          )
        ))}
      </div>

      {/* Legend */}
      <div className="grid grid-cols-4 gap-2 text-sm">
        {stages.map((stage) => (
          <div key={stage.key} className="flex items-center gap-2">
            <div className={clsx('w-3 h-3 rounded', stage.color)} />
            <div>
              <p className="text-gray-400">{stage.label}</p>
              <p className="font-medium">{stage.percentage?.toFixed(0) || 0}%</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SleepChart
