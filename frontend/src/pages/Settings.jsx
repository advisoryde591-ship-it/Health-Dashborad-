import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import {
  Settings as SettingsIcon,
  User,
  Target,
  Flame,
  Bell,
  Save,
  CheckCircle,
} from 'lucide-react'

function Settings() {
  const { user, updateUser } = useAuth()
  const [targetWeight, setTargetWeight] = useState(user?.target_weight || 76)
  const [calorieTarget, setCalorieTarget] = useState(user?.daily_calorie_target || 2000)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateUser({
        target_weight: targetWeight,
        daily_calorie_target: calorieTarget,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      console.error('Failed to save settings:', err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <SettingsIcon className="w-8 h-8 text-gray-400" />
          Settings
        </h1>
        <p className="text-gray-400 mt-1">Manage your preferences</p>
      </div>

      {/* Profile section */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <User className="w-5 h-5 text-blue-400" />
          Profile
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">Username</label>
            <input
              type="text"
              value={user?.username || ''}
              disabled
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-400"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">Email</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-400"
            />
          </div>
        </div>
      </div>

      {/* Goals section */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-green-400" />
          Goals
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Target Weight (kg)
            </label>
            <input
              type="number"
              value={targetWeight}
              onChange={(e) => setTargetWeight(parseFloat(e.target.value))}
              step="0.1"
              min="40"
              max="200"
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-green-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Current: {user?.target_weight || 76} kg
            </p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              <Flame className="w-4 h-4 inline mr-1 text-orange-400" />
              Daily Calorie Target
            </label>
            <input
              type="number"
              value={calorieTarget}
              onChange={(e) => setCalorieTarget(parseInt(e.target.value))}
              step="50"
              min="1000"
              max="5000"
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-green-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Current: {user?.daily_calorie_target || 2000} kcal
            </p>
          </div>
        </div>
      </div>

      {/* Notifications section */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Bell className="w-5 h-5 text-yellow-400" />
          Notifications
        </h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
            <div>
              <p className="font-medium">Daily Summary</p>
              <p className="text-sm text-gray-400">
                Receive daily health summary via Telegram at 9:00 AM
              </p>
            </div>
            <div className="px-3 py-1 bg-green-500/20 text-green-400 text-sm rounded">
              Active
            </div>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
            <div>
              <p className="font-medium">Auto Screenshot Processing</p>
              <p className="text-sm text-gray-400">
                Automatically process new screenshots from Google Drive
              </p>
            </div>
            <div className="px-3 py-1 bg-green-500/20 text-green-400 text-sm rounded">
              Active
            </div>
          </div>
        </div>
      </div>

      {/* Integration status */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Integration Status</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
            <span>Google Drive</span>
            <span className="text-green-400 text-sm">Connected</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
            <span>Telegram Bot</span>
            <span className="text-green-400 text-sm">Connected</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg">
            <span>Claude AI</span>
            <span className="text-green-400 text-sm">Active</span>
          </div>
        </div>
      </div>

      {/* Save button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-6 py-3 bg-green-500 hover:bg-green-600 rounded-lg transition-colors disabled:opacity-50"
        >
          {saved ? (
            <>
              <CheckCircle className="w-5 h-5" />
              Saved!
            </>
          ) : saving ? (
            'Saving...'
          ) : (
            <>
              <Save className="w-5 h-5" />
              Save Changes
            </>
          )}
        </button>
      </div>
    </div>
  )
}

export default Settings
