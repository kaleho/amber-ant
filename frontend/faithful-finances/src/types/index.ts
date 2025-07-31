// Performance-optimized type definitions for Faithful Finances

export type PersonaType = 
  | 'pre_teen' 
  | 'teen' 
  | 'college_student' 
  | 'single_adult' 
  | 'married_couple' 
  | 'single_parent' 
  | 'two_parent_family' 
  | 'fixed_income';

export type ExpenseType = 'fixed' | 'discretionary';

export type FamilyRole = 
  | 'administrator' 
  | 'spouse' 
  | 'teen' 
  | 'pre_teen' 
  | 'support';

// Optimized user interface with computed properties
export interface User {
  id: string;
  email: string;
  name: string;
  persona: PersonaType;
  preferences: UserPreferences;
  family_id?: string;
  family_role?: FamilyRole;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  notifications: NotificationPreferences;
  currency: string;
  date_format: string;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  frequency: 'immediate' | 'daily' | 'weekly';
}

// Performance-optimized account structure
export interface Account {
  id: string;
  user_id: string;
  plaid_account_id?: string;
  name: string;
  official_name: string;
  type: 'depository' | 'credit' | 'loan' | 'investment';
  subtype: string;
  balance: AccountBalance;
  mask: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountBalance {
  available: number;
  current: number;
  limit?: number;
  iso_currency_code: string;
}

// Optimized transaction with pre-computed fields
export interface Transaction {
  id: string;
  plaid_transaction_id?: string;
  account_id: string;
  amount: number;
  iso_currency_code: string;
  date: string;
  authorized_date?: string;
  name: string;
  merchant_name?: string;
  plaid_category?: string;
  plaid_category_detailed?: string[];
  app_expense_type: ExpenseType;
  is_split: boolean;
  split_details?: SplitDetails;
  notes?: string;
  is_tithing_income: boolean;
  created_at: string;
  updated_at: string;
}

export interface SplitDetails {
  fixed_categories: CategoryAmount[];
  discretionary_categories: CategoryAmount[];
}

export interface CategoryAmount {
  category: string;
  amount: number;
}

// Budget with performance optimizations
export interface Budget {
  id: string;
  user_id: string;
  name: string;
  period: 'monthly' | 'weekly' | 'yearly';
  start_date: string;
  end_date: string;
  categories: BudgetCategory[];
  total_budget: number;
  total_spent: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Computed fields for performance
  remaining_budget?: number;
  progress_percentage?: number;
}

export interface BudgetCategory {
  category: string;
  expense_type: ExpenseType;
  budgeted_amount: number;
  spent_amount: number;
  remaining_amount: number;
  // Performance helpers
  is_over_budget?: boolean;
  progress_percentage?: number;
}

// Savings goals with progress tracking
export interface SavingsGoal {
  id: string;
  user_id: string;
  name: string;
  description: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  progress_percentage: number;
  is_completed: boolean;
  created_at: string;
  updated_at: string;
  // Performance computed fields
  remaining_amount?: number;
  days_remaining?: number;
  required_monthly_saving?: number;
}

// Tithing with performance optimizations
export interface TithingData {
  user_id: string;
  year: number;
  total_income: number;
  total_tithe_due: number;
  total_tithe_paid: number;
  balance: number;
  current_percentage: number;
  recent_payments: TithePayment[];
}

export interface TithePayment {
  id: string;
  amount: number;
  date: string;
  method: 'cash' | 'check' | 'online' | 'transfer';
  recipient: string;
  notes?: string;
  created_at: string;
}

// Family management with role-based permissions
export interface Family {
  id: string;
  name: string;
  administrator_id: string;
  members: FamilyMember[];
  settings: FamilySettings;
  created_at: string;
  updated_at: string;
}

export interface FamilyMember {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: FamilyRole;
  permissions: FamilyPermissions;
  status: 'active' | 'pending' | 'inactive';
  joined_at: string;
}

export interface FamilyPermissions {
  can_view_accounts: boolean;
  can_view_transactions: boolean;
  can_manage_budget: boolean;
  can_approve_spending: boolean;
  requires_approval_over?: number;
  can_invite_members: boolean;
}

export interface FamilySettings {
  joint_tithing: boolean;
  shared_emergency_fund: boolean;
  notification_coordination: boolean;
}

// Performance-optimized dashboard data
export interface DashboardData {
  accounts: Account[];
  recent_transactions: Transaction[];
  budget_summary: BudgetSummary;
  savings_progress: SavingsGoal[];
  tithing_status: TithingData;
  alerts: Alert[];
  // Pre-computed aggregations for performance
  total_balance: number;
  monthly_spending: number;
  budget_health_score: number;
}

export interface BudgetSummary {
  total_budgeted: number;
  total_spent: number;
  remaining: number;
  categories_over_budget: number;
  progress_percentage: number;
}

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  is_read: boolean;
  expires_at?: string;
  action_url?: string;
  created_at: string;
}

// API response types for performance
export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp: string;
  // Performance metadata
  cache_hit?: boolean;
  processing_time?: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Performance monitoring types
export interface PerformanceMetrics {
  page_load_time: number;
  first_contentful_paint: number;
  largest_contentful_paint: number;
  cumulative_layout_shift: number;
  first_input_delay: number;
  memory_usage: number;
  bundle_size: number;
  cache_hit_rate: number;
}

// Component props interfaces
export interface PersonaProps {
  persona: PersonaType;
  user: User;
  children?: React.ReactNode;
}

export interface OptimizedListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
  loading?: boolean;
  onScrollEnd?: () => void;
}

// Hook return types
export interface UseFinancialDataReturn {
  accounts: Account[];
  transactions: Transaction[];
  budgets: Budget[];
  goals: SavingsGoal[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export interface UsePersonaReturn {
  persona: PersonaType;
  isLoading: boolean;
  preferences: UserPreferences;
  updatePreferences: (preferences: Partial<UserPreferences>) => Promise<void>;
}

// Chart data types for performance
export interface ChartDataPoint {
  date: string;
  value: number;
  category?: string;
  formatted_value?: string; // Pre-formatted for display
}

export interface BudgetChartData {
  category: string;
  budgeted: number;
  spent: number;
  remaining: number;
  expense_type: ExpenseType;
  color: string; // Pre-computed color for performance
}

// Virtual scrolling types
export interface VirtualScrollItem {
  id: string;
  height: number;
  data: any;
}

export interface VirtualScrollState {
  scrollTop: number;
  visibleStartIndex: number;
  visibleEndIndex: number;
  totalHeight: number;
}