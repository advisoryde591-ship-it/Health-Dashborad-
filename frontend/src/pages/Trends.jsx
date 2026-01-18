import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import api from '../utils/api'
import { format, parseISO } from 'date-fns'
import { TrendingUp, Scale, Heart, Moon, Footprints, Flame } from 'lucide-react'

function Trends() {
  const [period, setPeriod] = useState('week')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeChart, setActiveChart] = useState('weight')

  useEffect(() => {
    fetchTrends()
  }, [period])

  const fetchTrends = async () => {
    setLoading(true)
    try {
      const response = await api.get(`/metrics/trends?period=${period}`)
      setData(response.data)
    } catch (err) {
      console.error('Failed to fetch trends:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr) => {
    try {
      return format(parseISO(dateStr), 'MMM d')
    } catch {
      return dateStr
    }
  }

  const chartData = data?.dates?.map((date, index) => ({
    date,
    formattedDate: formatDate(date),
    weight: data.weight[index],
    bodyFat: data.body_fat[index],
    muscleMass: data.muscle_mass[index],
    recovery: data.recovery[index],
    sleepHours: data.sleep_hours[index],
    steps: data.steps[index],
    caloriesBurned: data.calories_burned[index],
  })) || []

  const chartConfigs = {
    weight: {
      title: 'Weight',
      icon: Scale,
      color: '#22c55e',
      dataKey: 'weight',
      unit: 'kg',
      domain: ['auto', 'auto'],
    },
    bodyFat: {
      title: 'Body Fat',
      icon: Scale,
      color: '#eab308',
      dataKey: 'bodyFat',
      unit: '%',
      domain: [0, 40],
    },
    muscleMass: {
      title: 'Muscle Mass',
      icon: Scale,
      color: '#a855f7',
      dataKey: 'muscleMass',
      unit: 'kg',
      domain: ['auto', 'auto'],
    },
    recovery: {
      title: 'Recovery Score',
      icon: Heart,
      color: '#22c55e',
      dataKey: 'recovery',
      unit: '%',
      domain: [0, 100],
    },
    sleepHours: {
      title: 'Sleep Duration',
      icon: Moon,
      color: '#8b5cf6',
      dataKey: 'sleepHours',
      unit: 'hrs',
      domain: [0, 12],
    },
    steps: {
      title: 'Steps',
      icon: Footprints,
      color: '#3b82f6',
      dataKey: 'steps',
      unit: '',
      domain: [0, 'auto'],
    },
    caloriesBurned: {
      title: 'Calories Burned',
      icon: Flame,
      color: '#ef4444',
      dataKey: 'caloriesBurned',
      unit: 'kcal',
      domain: [0, 'auto'],
    },
  }

  const currentConfig = chartConfigs[activeChart]
  const Icon = currentConfig.icon

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-green-400" />
            Trends
          </h1>
          <p className="text-gray-400 mt-1">Track your progress over time</p>
        </div>

        {/* Period selector */}
        <div className="flex bg-gray-800 rounded-lg p-1">
          {[
            { value: 'week', label: '7 Days' },
            { value: 'month', label: '30 Days' },
            { value: '3months', label: '90 Days' },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setPeriod(option.value)}
              className={`px-4 py-2 rounded-lg transition-colors ${
                period === option.value
                  ? 'bg-green-500 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Metric selector */}
      <div className="grid grid-cols-7 gap-2">
        {Object.entries(chartConfigs).map(([key, config]) => {
          const MetricIcon = config.icon
          return (
            <button
              key={key}
              onClick={() => setActiveChart(key)}
              className={`p-3 rounded-lg transition-colors flex flex-col items-center gap-2 ${
                activeChart === key
                  ? 'bg-gray-700 border border-gray-600'
                  : 'bg-gray-800 hover:bg-gray-700'
              }`}
            >
              <MetricIcon
                className="w-5 h-5"
                style={{ color: config.color }}
              />
              <span className="text-xs text-gray-400">{config.title}</span>
            </button>
          )
        })}
      </div>

      {/* Main Chart */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <Icon className="w-6 h-6" style={{ color: currentConfig.color }} />
          <h2 className="text-xl font-semibold">{currentConfig.title}</h2>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor={currentConfig.color}
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="95%"
                    stopColor={currentConfig.color}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="formattedDate"
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af', fontSize: 12 }}
              />
              <YAxis
                stroke="#9ca3af"
                tick={{ fill: '#9ca3af', fontSize: 12 }}
                domain={currentConfig.domain}
                tickFormatter={(value) =>
                  currentConfig.unit
                    ? `${value}${currentConfig.unit === '%' ? '%' : ''}`
                    : value
                }
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#9ca3af' }}
                formatter={(value) => [
                  value !== null
                    ? `${value}${currentConfig.unit ? ` ${currentConfig.unit}` : ''}`
                    : 'No data',
                  currentConfig.title,
                ]}
              />
              <Area
                type="monotone"
                dataKey={currentConfig.dataKey}
                stroke={currentConfig.color}
                strokeWidth={2}
                fill="url(#colorGradient)"
                connectNulls
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-4 gap-4">
        {['weight', 'recovery', 'sleepHours', 'steps'].map((key) => {
          const config = chartConfigs[key]
          const values = chartData
            .map((d) => d[config.dataKey])
            .filter((v) => v !== null)
          const latest = values[values.length - 1]
          const first = values[0]
          const change = latest && first ? (latest - first).toFixed(1) : null
          const avg = values.length
            ? (values.reduce((a, b) => a + b, 0) / values.length).toFixed(1)
            : null

          return (
            <div key={key} className="card">
              <div className="flex items-center gap-2 mb-3">
                <config.icon
                  className="w-4 h-4"
                  style={{ color: config.color }}
                />
                <span className="text-sm text-gray-400">{config.title}</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Latest</span>
                  <span className="font-medium">
                    {latest ?? '-'} {config.unit}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Average</span>
                  <span className="font-medium">
                    {avg ?? '-'} {config.unit}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400 text-sm">Change</span>
                  <span
                    className={`font-medium ${
                      change > 0
                        ? key === 'weight'
                          ? 'text-red-400'
                          : 'text-green-400'
                        : key === 'weight'
                        ? 'text-green-400'
                        : 'text-red-400'
                    }`}
                  >
                    {change !== null ? (change > 0 ? '+' : '') + change : '-'}{' '}
                    {config.unit}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default Trends
