import api from './api'
import {
  getAuthMode,
  getGuestCategories,
  addGuestCategory,
  getGuestExpenses,
  addGuestExpense,
  updateGuestExpense,
  deleteGuestExpense,
} from './guestStore'

export function isGuestMode() {
  return getAuthMode() === 'guest'
}

export async function listExpenses() {
  if (isGuestMode()) return getGuestExpenses()
  const { data } = await api.get('expenses/')
  return data
}

export async function createExpense(payload) {
  if (isGuestMode()) return addGuestExpense(payload)
  const { data } = await api.post('expenses/', payload)
  return data
}

export async function updateExpense(id, patch) {
  if (isGuestMode()) return updateGuestExpense(id, patch)
  const { data } = await api.patch(`expenses/${id}/`, patch)
  return data
}

export async function removeExpense(id) {
  if (isGuestMode()) {
    deleteGuestExpense(id)
    return
  }
  await api.delete(`expenses/${id}/`)
}

export async function listCategories() {
  if (isGuestMode()) return getGuestCategories()
  const { data } = await api.get('categories/')
  return data
}

export async function createCategory(name) {
  if (isGuestMode()) return addGuestCategory(name)
  const { data } = await api.post('categories/', { name })
  return data
}
