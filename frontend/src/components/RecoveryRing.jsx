import { clsx } from 'clsx'

function RecoveryRing({ score, size = 120 }) {
  const radius = (size - 12) / 2
  const circumference = radius * 2 * Math.PI
  const progress = score ? ((100 - score) / 100) * circumference : circumference

  const getColor = () => {
    if (!score) return '#6b7280'
    if (score >= 67) return '#22c55e'
    if (score >= 34) return '#eab308'
    return '#ef4444'
  }

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#374151"
          strokeWidth="8"
        />
        {/* Progress ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor()}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={progress}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className={clsx('text-3xl font-bold', {
            'text-green-400': score >= 67,
            'text-yellow-400': score >= 34 && score < 67,
            'text-red-400': score < 34,
            'text-gray-400': !score,
          })}
        >
          {score ?? '-'}
          {score && '%'}
        </span>
        <span className="text-gray-400 text-sm">Recovery</span>
      </div>
    </div>
  )
}

export default RecoveryRing
