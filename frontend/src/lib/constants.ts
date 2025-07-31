export const APP_CONFIG = {
  name: 'Faithful Finances',
  description: 'Biblical stewardship-focused personal finance management',
  version: '1.0.0',
  defaultCurrency: 'USD',
  supportEmail: 'support@faithfulfinances.com',
} as const

export const BIBLICAL_PRINCIPLES = {
  tithing: {
    percentage: 0.1,
    verse: 'Malachi 3:10',
    description: 'Bring the whole tithe into the storehouse',
  },
  stewardship: {
    verse: 'Luke 16:10',
    description: 'Whoever is faithful in very little is also faithful in much',
  },
  contentment: {
    verse: 'Philippians 4:19',
    description: 'And my God will meet all your needs according to his riches',
  },
  planning: {
    verse: 'Proverbs 21:5',
    description: 'The plans of the diligent lead to profit',
  },
} as const

export const TRANSACTION_CATEGORIES = {
  income: [
    'salary',
    'wages',
    'freelance',
    'business',
    'investment',
    'rental',
    'gifts',
    'other_income',
  ],
  expenses: [
    'housing',
    'transportation',
    'food',
    'utilities',
    'healthcare',
    'insurance',
    'entertainment',
    'shopping',
    'education',
    'personal_care',
    'other_expenses',
  ],
  biblical: [
    'tithe',
    'offering',
    'charity',
    'family_care',
    'stewardship',
    'provision',
    'investment',
    'other',
  ],
} as const

export const NOTIFICATION_TYPES = {
  tithe_reminder: {
    title: 'Tithe Reminder',
    icon: '💰',
    priority: 'high',
  },
  budget_alert: {
    title: 'Budget Alert',
    icon: '⚠️',
    priority: 'medium',
  },
  goal_milestone: {
    title: 'Goal Milestone',
    icon: '🎯',
    priority: 'medium',
  },
  account_sync: {
    title: 'Account Sync',
    icon: '🔄',
    priority: 'low',
  },
} as const

export const PLAID_CONFIG = {
  environment: import.meta.env.VITE_PLAID_ENV || 'sandbox',
  clientName: APP_CONFIG.name,
  products: ['transactions', 'auth', 'assets'],
  countryCodes: ['US'],
  language: 'en',
} as const

export const THEME_COLORS = {
  light: {
    primary: '#2563eb',
    secondary: '#059669',
    accent: '#dc2626',
    background: '#ffffff',
    surface: '#f8fafc',
    text: '#1e293b',
  },
  dark: {
    primary: '#3b82f6',
    secondary: '#10b981',
    accent: '#ef4444',
    background: '#0f172a',
    surface: '#1e293b',
    text: '#f1f5f9',
  },
} as const

export const BREAKPOINTS = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const

export const ANIMATION_DURATIONS = {
  fast: 150,
  normal: 300,
  slow: 500,
} as const

export const STORAGE_KEYS = {
  auth_token: 'ff_auth_token',
  user_preferences: 'ff_user_preferences',
  theme: 'ff_theme',
  last_sync: 'ff_last_sync',
} as const

export const API_ENDPOINTS = {
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    profile: '/users/profile',
  },
  financial: {
    accounts: '/accounts',
    transactions: '/transactions',
    budgets: '/budgets',
    goals: '/savings-goals',
  },
  plaid: {
    linkToken: '/plaid/link-token',
    exchangeToken: '/plaid/exchange-token',
  },
  reports: {
    summary: '/reports/summary',
    detailed: '/reports/detailed',
  },
} as const

export const ERROR_MESSAGES = {
  network: 'Network connection error. Please check your internet connection.',
  unauthorized: 'Please log in to access this feature.',
  forbidden: 'You do not have permission to perform this action.',
  not_found: 'The requested resource was not found.',
  server_error: 'A server error occurred. Please try again later.',
  validation: 'Please check your input and try again.',
  unknown: 'An unexpected error occurred.',
} as const

export const SUCCESS_MESSAGES = {
  login: 'Successfully logged in!',
  logout: 'Successfully logged out!',
  save: 'Successfully saved!',
  delete: 'Successfully deleted!',
  update: 'Successfully updated!',
  sync: 'Successfully synchronized!',
} as const