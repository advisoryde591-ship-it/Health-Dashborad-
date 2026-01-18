import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import api from '../utils/api'
import MetricCard from '../components/MetricCard'
import RecoveryRing from '../components/RecoveryRing'
import SleepChart from '../components/SleepChart'
import WeightProgress from '../components/WeightProgress'
import {
  Heart,
  Activity,
  Footprints,
  Flame,
  Droplets,
  Wind,
  Scale,
  Dumbbell,
  Calendar,
  ChevronLeft,
  ChevronRight,
  Upload,
} from 'lucide-react'

function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedDate, setSelectedDate] = useState(new Date())
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    fetchData()
  }, [selectedDate])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd')
      const response = await api.get(`/metrics/date/${dateStr}`)
      setData(response.data)
    } catch (err) {
      setError('Failed to load data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const files = e.target.files
    if (!files.length) return

    setUploading(true)

    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        await api.post('/screenshots/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      }
      fetchData()
    } catch (err) {
      console.error('Upload failed:', err)
    } finally {
      setUploading(false)
    }
  }

  const changeDate = (days) => {
    const newDate = new Date(selectedDate)
    newDate.setDate(newDate.getDate() + days)
    if (newDate <= new Date()) {
      setSelectedDate(newDate)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    )
  }

  const isToday = format(selectedDate, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-1">Your health at a glance</p>
        </div>

        <div className="flex items-center gap-4">
          {/* Date selector */}
          <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-2">
            <button
              onClick={() => changeDate(-1)}
              className="p-1 hover:bg-gray-700 rounded"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2 px-3">
              <Calendar className="w-4 h-4 text-gray-400" />
              <span className="font-medium">
                {isToday ? 'Today' : format(selectedDate, 'MMM d, yyyy')}
              </span>
            </div>
            <button
              onClick={() => changeDate(1)}
              disabled={isToday}
              className="p-1 hover:bg-gray-700 rounded disabled:opacity-50"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {/* Upload button */}
          <label className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg cursor-pointer transition-colors">
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Uploading...' : 'Upload Screenshots'}</span>
            <input
              type="file"
              multiple
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Main grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Recovery Score */}
        <div className="col-span-4 card flex flex-col items-center justify-center">
          <RecoveryRing score={data?.metrics?.recovery_score} size={160} />
          <div className="mt-4 grid grid-cols-2 gap-4 w-full">
            <div className="text-center">
              <p className="text-gray-400 text-sm">HRV</p>
              <p className="text-xl font-bold text-blue-400">
                {data?.metrics?.hrv ?? '-'} <span className="text-sm text-gray-400">ms</span>
              </p>
            </div>
            <div className="text-center">
              <p className="text-gray-400 text-sm">Resting HR</p>
              <p className="text-xl font-bold text-red-400">
                {data?.metrics?.resting_heart_rate ?? '-'} <span className="text-sm text-gray-400">bpm</span>
              </p>
            </div>
          </div>
        </div>

        {/* Weight Progress */}
        <div className="col-span-4 card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Scale className="w-5 h-5 text-green-400" />
            Weight Progress
          </h3>
          <WeightProgress weightProgress={data?.weight_progress} />
        </div>

        {/* Body Composition */}
        <div className="col-span-4 card">
          <h3 className="text-lg font-semibold mb-4">Body Composition</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg">
              <span className="text-gray-400">Body Fat</span>
              <span className="text-xl font-bold text-yellow-400">
                {data?.body?.body_fat_percentage?.toFixed(1) ?? '-'}%
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg">
              <span className="text-gray-400">Muscle Mass</span>
              <span className="text-xl font-bold text-purple-400">
                {data?.body?.skeletal_muscle_mass_kg?.toFixed(1) ?? '-'} kg
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg">
              <span className="text-gray-400">Body Water</span>
              <span className="text-xl font-bold text-blue-400">
                {data?.body?.body_water_percentage?.toFixed(1) ?? '-'}%
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-700/50 rounded-lg">
              <span className="text-gray-400">BMI</span>
              <span className="text-xl font-bold text-green-400">
                {data?.body?.bmi?.toFixed(1) ?? '-'}
              </span>
            </div>
          </div>
        </div>

        {/* Sleep */}
        <div className="col-span-6 card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            Sleep Analysis
          </h3>
          <SleepChart sleep={data?.sleep} />
        </div>

        {/* Activity Metrics */}
        <div className="col-span-6 card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-400" />
            Activity
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              title="Steps"
              value={data?.metrics?.steps?.toLocaleString()}
              icon={Footprints}
              color="blue"
            />
            <MetricCard
              title="Calories Burned"
              value={data?.metrics?.calories_burned?.toLocaleString()}
              unit="kcal"
              icon={Flame}
              color="red"
            />
            <MetricCard
              title="VO2 Max"
              value={data?.metrics?.vo2_max}
              icon={Wind}
              color="green"
            />
            <MetricCard
              title="Respiratory Rate"
              value={data?.metrics?.respiratory_rate?.toFixed(1)}
              unit="br/min"
              icon={Wind}
              color="purple"
            />
          </div>
        </div>

        {/* Workouts */}
        <div className="col-span-12 card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Dumbbell className="w-5 h-5 text-green-400" />
            Workouts
          </h3>
          {data?.workouts?.length > 0 ? (
            <div className="grid grid-cols-3 gap-4">
              {data.workouts.map((workout, index) => (
                <div key={index} className="p-4 bg-gray-700/50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Dumbbell className="w-4 h-4 text-green-400" />
                    <span className="font-medium">{workout.workout_type}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-400">Duration</span>
                      <p className="font-medium">{workout.duration_minutes} min</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Calories</span>
                      <p className="font-medium">{workout.total_calories} kcal</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Avg HR</span>
                      <p className="font-medium">{workout.avg_heart_rate} bpm</p>
                    </div>
                    <div>
                      <span className="text-gray-400">Effort</span>
                      <p className="font-medium">{workout.effort_label || '-'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No workouts recorded</p>
          )}
        </div>

        {/* Calorie Summary */}
        <div className="col-span-12 card">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-400" />
            Calorie Balance
          </h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-500/10 rounded-lg">
              <p className="text-gray-400 text-sm">Consumed</p>
              <p className="text-2xl font-bold text-green-400">
                {data?.calorie_summary?.consumed || 0}
              </p>
              <p className="text-gray-400 text-xs">kcal</p>
            </div>
            <div className="text-center p-4 bg-red-500/10 rounded-lg">
              <p className="text-gray-400 text-sm">Burned</p>
              <p className="text-2xl font-bold text-red-400">
                {data?.calorie_summary?.burned || 0}
              </p>
              <p className="text-gray-400 text-xs">kcal</p>
            </div>
            <div className="text-center p-4 bg-blue-500/10 rounded-lg">
              <p className="text-gray-400 text-sm">Target</p>
              <p className="text-2xl font-bold text-blue-400">
                {data?.calorie_summary?.target || 2000}
              </p>
              <p className="text-gray-400 text-xs">kcal</p>
            </div>
            <div className="text-center p-4 bg-purple-500/10 rounded-lg">
              <p className="text-gray-400 text-sm">Remaining</p>
              <p className="text-2xl font-bold text-purple-400">
                {data?.calorie_summary?.remaining || 0}
              </p>
              <p className="text-gray-400 text-xs">kcal</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
