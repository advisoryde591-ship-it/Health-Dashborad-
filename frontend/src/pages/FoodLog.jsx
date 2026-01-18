import { useState, useEffect } from 'react'
import { format } from 'date-fns'
import api from '../utils/api'
import {
  UtensilsCrossed,
  Plus,
  Trash2,
  Coffee,
  Sun,
  Moon,
  Apple,
  Flame,
} from 'lucide-react'

const mealIcons = {
  breakfast: Coffee,
  lunch: Sun,
  dinner: Moon,
  snack: Apple,
}

function FoodLog() {
  const [todayFood, setTodayFood] = useState(null)
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [newFood, setNewFood] = useState({ description: '', meal_type: 'snack' })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [todayRes, historyRes] = await Promise.all([
        api.get('/food/today'),
        api.get('/food/history?days=7'),
      ])
      setTodayFood(todayRes.data)
      setHistory(historyRes.data)
    } catch (err) {
      console.error('Failed to fetch food data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!newFood.description.trim()) return

    setSubmitting(true)
    try {
      await api.post('/food/log', newFood)
      setNewFood({ description: '', meal_type: 'snack' })
      setShowAddModal(false)
      fetchData()
    } catch (err) {
      console.error('Failed to log food:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this food entry?')) return

    try {
      await api.delete(`/food/${id}`)
      fetchData()
    } catch (err) {
      console.error('Failed to delete:', err)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    )
  }

  const caloriePercentage = todayFood?.target_calories
    ? Math.min(100, (todayFood.total_calories / todayFood.target_calories) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <UtensilsCrossed className="w-8 h-8 text-orange-400" />
            Food Log
          </h1>
          <p className="text-gray-400 mt-1">Track your nutrition</p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg transition-colors"
        >
          <Plus className="w-4 h-4" />
          Log Food
        </button>
      </div>

      {/* Today's summary */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Today's Summary</h2>

        <div className="grid grid-cols-5 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-700/50 rounded-lg">
            <Flame className="w-6 h-6 text-orange-400 mx-auto mb-2" />
            <p className="text-2xl font-bold">{todayFood?.total_calories || 0}</p>
            <p className="text-gray-400 text-sm">Calories</p>
          </div>
          <div className="text-center p-4 bg-gray-700/50 rounded-lg">
            <p className="text-2xl font-bold text-red-400">
              {todayFood?.total_protein_g?.toFixed(0) || 0}g
            </p>
            <p className="text-gray-400 text-sm">Protein</p>
          </div>
          <div className="text-center p-4 bg-gray-700/50 rounded-lg">
            <p className="text-2xl font-bold text-yellow-400">
              {todayFood?.total_carbs_g?.toFixed(0) || 0}g
            </p>
            <p className="text-gray-400 text-sm">Carbs</p>
          </div>
          <div className="text-center p-4 bg-gray-700/50 rounded-lg">
            <p className="text-2xl font-bold text-blue-400">
              {todayFood?.total_fat_g?.toFixed(0) || 0}g
            </p>
            <p className="text-gray-400 text-sm">Fat</p>
          </div>
          <div className="text-center p-4 bg-gray-700/50 rounded-lg">
            <p className="text-2xl font-bold text-green-400">
              {todayFood?.remaining_calories || 0}
            </p>
            <p className="text-gray-400 text-sm">Remaining</p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Daily Progress</span>
            <span className="text-gray-400">
              {todayFood?.total_calories || 0} / {todayFood?.target_calories || 2000} kcal
            </span>
          </div>
          <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                caloriePercentage > 100
                  ? 'bg-red-500'
                  : caloriePercentage > 80
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(100, caloriePercentage)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Today's meals */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Today's Meals</h2>

        {todayFood?.meals?.length > 0 ? (
          <div className="space-y-3">
            {todayFood.meals.map((meal) => {
              const MealIcon = mealIcons[meal.meal_type] || Apple
              return (
                <div
                  key={meal.id}
                  className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-gray-600 rounded-lg">
                      <MealIcon className="w-5 h-5 text-orange-400" />
                    </div>
                    <div>
                      <p className="font-medium">{meal.description}</p>
                      <p className="text-sm text-gray-400 capitalize">
                        {meal.meal_type} - {format(new Date(meal.logged_at), 'h:mm a')}
                      </p>
                      {meal.ai_notes && (
                        <p className="text-xs text-gray-500 mt-1">{meal.ai_notes}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-bold text-orange-400">
                        {meal.estimated_calories || '?'} kcal
                      </p>
                      <p className="text-xs text-gray-400">
                        P: {meal.estimated_protein_g?.toFixed(0) || '?'}g |
                        C: {meal.estimated_carbs_g?.toFixed(0) || '?'}g |
                        F: {meal.estimated_fat_g?.toFixed(0) || '?'}g
                      </p>
                    </div>
                    <button
                      onClick={() => handleDelete(meal.id)}
                      className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-600 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-8">
            No meals logged today. Start by adding your first meal!
          </p>
        )}
      </div>

      {/* History */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Last 7 Days</h2>

        {history?.daily_summaries?.length > 0 ? (
          <div className="space-y-2">
            {history.daily_summaries.map((day) => (
              <div
                key={day.date}
                className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg"
              >
                <span className="text-gray-400">
                  {format(new Date(day.date), 'EEE, MMM d')}
                </span>
                <div className="flex items-center gap-6 text-sm">
                  <span>{day.meal_count} meals</span>
                  <span className="font-medium text-orange-400">
                    {day.total_calories} kcal
                  </span>
                  <div className="w-24 h-2 bg-gray-600 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        day.total_calories > history.target_calories
                          ? 'bg-red-500'
                          : 'bg-green-500'
                      }`}
                      style={{
                        width: `${Math.min(100, (day.total_calories / history.target_calories) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-4">No history available</p>
        )}
      </div>

      {/* Add food modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Log Food</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Meal Type
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {['breakfast', 'lunch', 'dinner', 'snack'].map((type) => {
                    const Icon = mealIcons[type]
                    return (
                      <button
                        key={type}
                        type="button"
                        onClick={() =>
                          setNewFood({ ...newFood, meal_type: type })
                        }
                        className={`p-3 rounded-lg flex flex-col items-center gap-1 transition-colors ${
                          newFood.meal_type === type
                            ? 'bg-green-500/20 border border-green-500'
                            : 'bg-gray-700 hover:bg-gray-600'
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="text-xs capitalize">{type}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  What did you eat?
                </label>
                <textarea
                  value={newFood.description}
                  onChange={(e) =>
                    setNewFood({ ...newFood, description: e.target.value })
                  }
                  placeholder="e.g., 2 eggs, toast with butter, coffee with milk"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:border-green-500 resize-none"
                  rows={3}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  AI will estimate calories and macros
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 py-3 bg-green-500 hover:bg-green-600 rounded-lg transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Logging...' : 'Log Food'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default FoodLog
