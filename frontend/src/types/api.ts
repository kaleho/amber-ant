export interface ApiResponse<T> {
  data: T
  message?: string
  status: 'success' | 'error'
  timestamp: string
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    limit: number
    total: number
    totalPages: number
    hasNextPage: boolean
    hasPrevPage: boolean
  }
  message?: string
  status: 'success' | 'error'
  timestamp: string
}

export interface ApiError {
  message: string
  code: string
  details?: Record<string, any>
  timestamp: string
}

export interface PlaidLinkConfig {
  token: string
  onSuccess: (publicToken: string, metadata: any) => void
  onExit: (error: any, metadata: any) => void
  onEvent: (eventName: string, metadata: any) => void
}

export interface PlaidAccount {
  account_id: string
  balances: {
    available: number | null
    current: number | null
    iso_currency_code: string | null
    limit: number | null
    unofficial_currency_code: string | null
  }
  mask: string | null
  name: string
  official_name: string | null
  type: string
  subtype: string | null
}

export interface PlaidTransaction {
  account_id: string
  amount: number
  iso_currency_code: string | null
  unofficial_currency_code: string | null
  category: string[] | null
  category_id: string | null
  date: string
  datetime: string | null
  authorized_date: string | null
  authorized_datetime: string | null
  location: {
    address: string | null
    city: string | null
    region: string | null
    postal_code: string | null
    country: string | null
    lat: number | null
    lon: number | null
    store_number: string | null
  }
  merchant_name: string | null
  name: string
  payment_meta: Record<string, any>
  pending: boolean
  pending_transaction_id: string | null
  account_owner: string | null
  transaction_id: string
  transaction_code: string | null
  transaction_type: string
}

export type ApiEndpoint = 
  | '/auth/login'
  | '/auth/logout' 
  | '/auth/refresh'
  | '/users/profile'
  | '/users/preferences'
  | '/accounts'
  | '/transactions'
  | '/budgets'
  | '/savings-goals'
  | '/plaid/link-token'
  | '/plaid/exchange-token'
  | '/tithing/calculation'
  | '/reports/summary'

export interface RequestConfig {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: Record<string, string>
  body?: any
  params?: Record<string, string | number | boolean>
}