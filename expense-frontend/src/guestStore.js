const MODE_KEY = 'expense_auth_mode'
const EXPENSES_KEY = 'guest_expenses'
const CATEGORIES_KEY = 'guest_categories'

export const DEFAULT_CATEGORIES = [
  'Jedzenie',
  'Transport',
  'Mieszkanie',
  'Rozrywka',
  'Zdrowie i uroda',
  'Edukacja',
  'Ubrania',
  'Wydatki domowe',
  'Prezenty',
  'Inne',
]

function load(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function save(key, value) {
  localStorage.setItem(key, JSON.stringify(value))
}

export function getAuthMode() {
  return localStorage.getItem(MODE_KEY)
}

export function setAuthMode(mode) {
  if (mode) {
    localStorage.setItem(MODE_KEY, mode)
  } else {
    localStorage.removeItem(MODE_KEY)
  }
}

export function ensureGuestData() {
  if (!localStorage.getItem(CATEGORIES_KEY)) {
    save(
      CATEGORIES_KEY,
      DEFAULT_CATEGORIES.map((name, index) => ({ id: -(index + 1), name }))
    )
  }
  if (!localStorage.getItem(EXPENSES_KEY)) {
    save(EXPENSES_KEY, [])
  }
}

export function enterGuestMode() {
  ensureGuestData()
  setAuthMode('guest')
}

export function getGuestCategories() {
  ensureGuestData()
  return load(CATEGORIES_KEY, [])
}

export function addGuestCategory(name) {
  const trimmed = name.trim()
  const categories = getGuestCategories()
  const existing = categories.find(
    (cat) => cat.name.toLowerCase() === trimmed.toLowerCase()
  )
  if (existing) return existing

  const category = { id: Date.now(), name: trimmed }
  categories.push(category)
  save(CATEGORIES_KEY, categories)
  return category
}

export function getGuestExpenses() {
  ensureGuestData()
  return load(EXPENSES_KEY, []).sort(
    (a, b) => new Date(b.date) - new Date(a.date)
  )
}

export function addGuestExpense(payload) {
  const expenses = getGuestExpenses()
  const expense = {
    id: Date.now(),
    name: payload.name,
    amount: payload.amount,
    category: payload.category,
    date: payload.date,
    items: payload.items || [],
  }
  expenses.unshift(expense)
  save(EXPENSES_KEY, expenses)
  return expense
}

export function updateGuestExpense(id, patch) {
  const expenses = getGuestExpenses()
  const index = expenses.findIndex((expense) => expense.id === id)
  if (index === -1) {
    throw new Error('Wydatek nie istnieje')
  }
  expenses[index] = { ...expenses[index], ...patch, id }
  save(EXPENSES_KEY, expenses)
  return expenses[index]
}

export function deleteGuestExpense(id) {
  const expenses = getGuestExpenses().filter((expense) => expense.id !== id)
  save(EXPENSES_KEY, expenses)
}
