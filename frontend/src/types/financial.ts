export interface Account {
  id: string
  user_id: string
  plaid_account_id?: string
  name: string
  type: AccountType
  subtype: string
  balance_current: number
  balance_available?: number
  currency: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type AccountType = 
  | 'checking'
  | 'savings'
  | 'credit_card'
  | 'investment'
  | 'loan'
  | 'other'

export interface Transaction {
  id: string
  user_id: string
  account_id: string
  plaid_transaction_id?: string
  amount: number
  description: string
  date: string
  category_primary: string
  category_detailed?: string
  category_biblical?: BiblicalCategory
  merchant_name?: string
  is_pending: boolean
  created_at: string
  updated_at: string
}

export type BiblicalCategory = 
  | 'tithe'
  | 'offering'
  | 'charity'
  | 'family_care'
  | 'stewardship'
  | 'provision'
  | 'investment'
  | 'other'

export interface Budget {
  id: string
  user_id: string
  name: string
  period_type: 'monthly' | 'weekly' | 'annual'
  start_date: string
  end_date: string
  categories: BudgetCategory[]
  total_income: number
  total_expenses: number
  created_at: string
  updated_at: string
}

export interface BudgetCategory {
  id: string
  budget_id: string
  name: string
  category_type: 'income' | 'expense'
  budgeted_amount: number
  actual_amount: number
  variance: number
  is_tithe_category: boolean
}

export interface SavingsGoal {
  id: string
  user_id: string
  name: string
  description?: string
  target_amount: number
  current_amount: number
  target_date?: string
  priority: 'low' | 'medium' | 'high'
  is_emergency_fund: boolean
  created_at: string
  updated_at: string
}

export interface TitheCalculation {
  user_id: string
  period_start: string
  period_end: string
  gross_income: number
  tithe_amount: number
  tithe_paid: number
  tithe_remaining: number
  calculated_at: string
}

export interface FinancialSummary {
  total_balance: number
  monthly_income: number
  monthly_expenses: number
  tithe_status: {
    current_period: number
    paid: number
    remaining: number
    percentage: number
  }
  savings_goals: {
    total_target: number
    total_saved: number
    completion_percentage: number
  }
  budget_status: {
    categories_on_track: number
    categories_over_budget: number
    overall_variance: number
  }
}