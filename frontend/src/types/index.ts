// User and Authentication Types
export interface User {
  id: string
  email: string
  name: string
  persona: Persona
  preferences: UserPreferences
  family_id?: string
  family_role?: FamilyRole
  created_at: string
  updated_at: string
}

export type Persona = 
  | 'pre_teen'
  | 'teen' 
  | 'college_student'
  | 'single_adult'
  | 'married_couple'
  | 'single_parent'
  | 'two_parent_family'
  | 'fixed_income'

export type FamilyRole = 
  | 'administrator'
  | 'spouse'
  | 'teen'
  | 'pre_teen'
  | 'support'

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  notifications: NotificationPreferences
  currency: string
  date_format: string
  accessibility?: AccessibilityPreferences
}

export interface NotificationPreferences {
  email: boolean
  push: boolean
  sms: boolean
  frequency: 'immediate' | 'daily' | 'weekly'
}

export interface AccessibilityPreferences {
  high_contrast: boolean
  large_text: boolean
  reduce_motion: boolean
  screen_reader: boolean
}

// Account and Financial Types
export interface Account {
  id: string
  user_id: string
  plaid_account_id?: string
  name: string
  official_name?: string
  type: AccountType
  subtype: AccountSubtype
  balance: Balance
  mask?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type AccountType = 'depository' | 'credit' | 'loan' | 'investment' | 'other'
export type AccountSubtype = 
  | 'checking' | 'savings' | 'money_market' | 'cd'
  | 'credit_card' | 'auto' | 'mortgage' | 'student'
  | 'investment' | 'retirement' | 'other'

export interface Balance {
  available: number | null
  current: number
  limit: number | null
  iso_currency_code: string
}

// Transaction Types
export interface Transaction {
  id: string
  plaid_transaction_id?: string
  account_id: string
  amount: number
  iso_currency_code: string
  date: string
  authorized_date?: string
  name: string
  merchant_name?: string
  plaid_category?: string
  plaid_category_detailed?: string[]
  app_expense_type: ExpenseType
  is_split: boolean
  split_details?: SplitDetails
  notes?: string
  is_tithing_income: boolean
  created_at: string
  updated_at: string
}

export type ExpenseType = 'fixed' | 'discretionary' | 'split'

export interface SplitDetails {
  fixed_categories: SplitCategory[]
  discretionary_categories: SplitCategory[]
}

export interface SplitCategory {
  category: string
  amount: number
}

export interface TransactionSplit {
  id: string
  transaction_id: string
  category: string
  expense_type: 'fixed' | 'discretionary'
  amount: number
  percentage: number
}

// Budget Types
export interface Budget {
  id: string
  user_id: string
  name: string
  period: 'weekly' | 'monthly' | 'yearly'
  start_date: string
  end_date: string
  categories: BudgetCategory[]
  total_budget: number
  total_spent: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface BudgetCategory {
  category: string
  expense_type: 'fixed' | 'discretionary'
  budgeted_amount: number
  spent_amount: number
  remaining_amount: number
}

export interface BudgetProgress {
  percentage: number
  status: 'under' | 'on-track' | 'warning' | 'over'
  remaining: number
  days_remaining: number
}

// Savings Goals Types
export interface SavingsGoal {
  id: string
  user_id: string
  name: string
  description?: string
  target_amount: number
  current_amount: number
  target_date?: string
  progress_percentage: number
  is_completed: boolean
  created_at: string
  updated_at: string
}

export interface SavingsProgress {
  percentage: number
  remaining: number
  monthly_required?: number
  on_track?: boolean
  projected_completion?: string
}

// Tithing Types
export interface TithingSummary {
  user_id: string
  year: number
  total_income: number
  total_tithe_due: number
  total_tithe_paid: number
  balance: number
  current_percentage: number
  recent_payments: TithingPayment[]
}

export interface TithingPayment {
  id: string
  amount: number
  date: string
  method: 'cash' | 'check' | 'online' | 'transfer'
  recipient: string
  notes?: string
  created_at: string
}

// Family Types
export interface Family {
  id: string
  name: string
  administrator_id: string
  members: FamilyMember[]
  settings: FamilySettings
  created_at: string
  updated_at: string
}

export interface FamilyMember {
  id: string
  user_id: string
  name: string
  email: string
  role: FamilyRole
  permissions: FamilyPermissions
  status: 'active' | 'inactive' | 'pending'
  joined_at: string
}

export interface FamilyPermissions {
  can_view_accounts: boolean
  can_view_transactions: boolean
  can_manage_budget: boolean
  can_approve_spending: boolean
  requires_approval_over?: number
  can_invite_members: boolean
}

export interface FamilySettings {
  joint_tithing: boolean
  shared_emergency_fund: boolean
  notification_coordination: boolean
}

export interface FamilyInvitation {
  id: string
  family_id: string
  inviter_id: string
  email: string
  role: FamilyRole
  permissions: FamilyPermissions
  message?: string
  status: 'pending' | 'accepted' | 'declined' | 'expired'
  expires_at: string
  created_at: string
}

// Subscription Types
export interface Subscription {
  id: string
  user_id: string
  stripe_subscription_id: string
  plan: SubscriptionPlan
  status: SubscriptionStatus
  current_period_start: string
  current_period_end: string
  trial_end?: string
  cancel_at_period_end: boolean
  created_at: string
  updated_at: string
}

export type SubscriptionPlan = 
  | 'free'
  | 'premium_individual' 
  | 'premium_family'
  | 'premium_unlimited'

export type SubscriptionStatus = 
  | 'active'
  | 'canceled'
  | 'incomplete'
  | 'incomplete_expired'
  | 'past_due'
  | 'trialing'
  | 'unpaid'

// Form Types
export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'checkbox' | 'radio'
  placeholder?: string
  required?: boolean
  validation?: ValidationRule[]
  options?: SelectOption[]
  disabled?: boolean
}

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface ValidationRule {
  type: 'required' | 'email' | 'minLength' | 'maxLength' | 'min' | 'max' | 'pattern'
  value?: string | number
  message: string
}

// UI Component Types
export interface ComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface ChartData {
  name: string
  value: number
  color?: string
  percentage?: number
}

export interface TableColumn<T> {
  key: keyof T
  header: string
  sortable?: boolean
  render?: (value: T[keyof T], row: T) => React.ReactNode
}

// API Response Types
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
    pages: number
  }
}

export interface ErrorResponse {
  error: string
  message: string
  details?: Record<string, unknown>
  timestamp: string
}

// State Management Types
export interface AppState {
  user: User | null
  accounts: Account[]
  transactions: Transaction[]
  budgets: Budget[]
  savings_goals: SavingsGoal[]
  family?: Family
  loading: boolean
  error?: string
}

export interface TransactionState {
  transactions: Transaction[]
  filters: TransactionFilters
  loading: boolean
  error?: string
}

export interface TransactionFilters {
  accounts?: string[]
  categories?: string[]
  expense_types?: ExpenseType[]
  date_range?: {
    start: string
    end: string
  }
  amount_range?: {
    min: number
    max: number
  }
  search?: string
}

// Analytics Types
export interface SpendingAnalytics {
  total_spent: number
  categories: CategorySpending[]
  trends: SpendingTrend[]
  budget_performance: BudgetPerformance[]
}

export interface CategorySpending {
  category: string
  amount: number
  percentage: number
  expense_type: 'fixed' | 'discretionary'
  transactions_count: number
}

export interface SpendingTrend {
  period: string
  amount: number
  change_percentage: number
}

export interface BudgetPerformance {
  category: string
  budgeted: number
  spent: number
  remaining: number
  status: 'under' | 'on-track' | 'warning' | 'over'
}

// Event Types
export interface AppEvent {
  type: string
  payload?: unknown
  timestamp: Date
}

export interface TransactionEvent extends AppEvent {
  type: 'transaction_added' | 'transaction_updated' | 'transaction_categorized'
  payload: {
    transaction: Transaction
    previous?: Partial<Transaction>
  }
}

export interface BudgetEvent extends AppEvent {
  type: 'budget_created' | 'budget_updated' | 'budget_exceeded'
  payload: {
    budget: Budget
    category?: string
  }
}

// Utility Types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>

export type OptionalFields<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

// Constants
export const PERSONAS: Record<Persona, string> = {
  pre_teen: 'Pre-Teen (8-14)',
  teen: 'Teen (15-17)',
  college_student: 'College Student (18-22)',
  single_adult: 'Single Adult (25-40)',
  married_couple: 'Married Couple (25-65)',
  single_parent: 'Single Parent (25-45)',
  two_parent_family: 'Two Parent Family (30-50)',
  fixed_income: 'Fixed Income (55+)'
}

export const EXPENSE_CATEGORIES = [
  'groceries', 'transportation', 'rent', 'utilities', 'health',
  'entertainment', 'shopping', 'dining', 'household', 'clothing',
  'education', 'professional_services', 'insurance', 'travel',
  'personal_care', 'gifts', 'charity', 'taxes'
] as const

export const ACCOUNT_TYPES: Record<AccountType, string> = {
  depository: 'Bank Account',
  credit: 'Credit Account',
  loan: 'Loan',
  investment: 'Investment',
  other: 'Other'
}