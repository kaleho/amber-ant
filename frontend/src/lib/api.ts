/**
 * API Integration Layer for Faithful Finances
 * Handles all API calls with mock data support and proper error handling
 */

import { QueryClient } from '@tanstack/react-query';
import { 
  User, 
  Account, 
  Transaction, 
  Budget, 
  SavingsGoal, 
  TithingSummary,
  Family,
  Subscription,
  PersonaType,
  CreateTransactionRequest,
  UpdateTransactionRequest,
  SplitTransactionRequest,
  CreateBudgetRequest,
  UpdateBudgetRequest,
  CreateSavingsGoalRequest,
  UpdateSavingsGoalRequest,
  CreateTithingRequest,
  CreateFamilyRequest,
  FamilyInvitationRequest,
  CreateSubscriptionRequest,
  UpdateSubscriptionRequest
} from '@/types';

// Create the query client
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors
        if (error?.status >= 400 && error?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

// Base API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1';
const MOCK_MODE = import.meta.env.VITE_API_MOCK_MODE === 'true';

// Mock data import
let mockData: any = null;
if (MOCK_MODE) {
  try {
    // Import mock data - this will be replaced with actual API calls in production
    mockData = await import('../../mock-data.json');
  } catch (error) {
    console.warn('Could not load mock data:', error);
  }
}

/**
 * Enhanced API client with authentication and error handling
 */
class ApiClient {
  private baseURL: string;
  private getAccessToken: (() => Promise<string>) | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  setAuthTokenProvider(getAccessToken: () => Promise<string>) {
    this.getAccessToken = getAccessToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    // If in mock mode, return mock data
    if (MOCK_MODE && mockData) {
      return this.getMockData<T>(endpoint, options.method || 'GET');
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add authentication token if available
    if (this.getAccessToken) {
      try {
        const token = await this.getAccessToken();
        headers['Authorization'] = `Bearer ${token}`;
      } catch (error) {
        console.error('Failed to get access token:', error);
        throw new Error('Authentication failed');
      }
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.message || 'API request failed',
        response.status,
        errorData
      );
    }

    return response.json();
  }

  private getMockData<T>(endpoint: string, method: string): T {
    const delay = () => new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 700));
    
    return delay().then(() => {
      // Simple mock data routing based on endpoint
      if (endpoint.includes('/users')) {
        if (method === 'POST') {
          return mockData.users[0] as T; // Return first user as created user
        }
        return mockData.users as T;
      }
      
      if (endpoint.includes('/accounts')) {
        return mockData.accounts as T;
      }
      
      if (endpoint.includes('/transactions')) {
        return {
          transactions: mockData.transactions,
          total_count: mockData.transactions.length,
          has_more: false
        } as T;
      }
      
      if (endpoint.includes('/budgets')) {
        return mockData.budgets as T;
      }
      
      if (endpoint.includes('/goals')) {
        return mockData.savings_goals as T;
      }
      
      if (endpoint.includes('/tithing')) {
        return mockData.tithing_summaries as T;
      }
      
      if (endpoint.includes('/families')) {
        return mockData.families as T;
      }
      
      if (endpoint.includes('/subscriptions')) {
        return mockData.subscriptions as T;
      }
      
      // Default empty response
      return {} as T;
    });
  }

  // Authentication endpoints
  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // User management
  async createUser(userData: Partial<User>): Promise<User> {
    return this.request<User>('/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async updateUser(userId: string, updates: Partial<User>): Promise<User> {
    return this.request<User>(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Account management
  async getAccounts(): Promise<Account[]> {
    return this.request<Account[]>('/accounts');
  }

  async getAccount(accountId: string): Promise<Account> {
    return this.request<Account>(`/accounts/${accountId}`);
  }

  // Transaction management
  async getTransactions(params?: {
    account_id?: string;
    start_date?: string;
    end_date?: string;
    category?: string;
    expense_type?: 'fixed' | 'discretionary';
    limit?: number;
    offset?: number;
  }): Promise<{
    transactions: Transaction[];
    total_count: number;
    has_more: boolean;
  }> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/transactions${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return this.request(endpoint);
  }

  async getTransaction(transactionId: string): Promise<Transaction> {
    return this.request<Transaction>(`/transactions/${transactionId}`);
  }

  async createTransaction(transactionData: CreateTransactionRequest): Promise<Transaction> {
    return this.request<Transaction>('/transactions', {
      method: 'POST',
      body: JSON.stringify(transactionData),
    });
  }

  async updateTransaction(transactionId: string, updates: UpdateTransactionRequest): Promise<Transaction> {
    return this.request<Transaction>(`/transactions/${transactionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async splitTransaction(transactionId: string, splitData: SplitTransactionRequest): Promise<Transaction> {
    return this.request<Transaction>(`/transactions/${transactionId}/split`, {
      method: 'POST',
      body: JSON.stringify(splitData),
    });
  }

  // Budget management
  async getBudgets(): Promise<Budget[]> {
    return this.request<Budget[]>('/budgets');
  }

  async getBudget(budgetId: string): Promise<Budget> {
    return this.request<Budget>(`/budgets/${budgetId}`);
  }

  async createBudget(budgetData: CreateBudgetRequest): Promise<Budget> {
    return this.request<Budget>('/budgets', {
      method: 'POST',
      body: JSON.stringify(budgetData),
    });
  }

  async updateBudget(budgetId: string, updates: UpdateBudgetRequest): Promise<Budget> {
    return this.request<Budget>(`/budgets/${budgetId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteBudget(budgetId: string): Promise<void> {
    return this.request<void>(`/budgets/${budgetId}`, {
      method: 'DELETE',
    });
  }

  // Savings goals
  async getSavingsGoals(): Promise<SavingsGoal[]> {
    return this.request<SavingsGoal[]>('/goals');
  }

  async getSavingsGoal(goalId: string): Promise<SavingsGoal> {
    return this.request<SavingsGoal>(`/goals/${goalId}`);
  }

  async createSavingsGoal(goalData: CreateSavingsGoalRequest): Promise<SavingsGoal> {
    return this.request<SavingsGoal>('/goals', {
      method: 'POST',
      body: JSON.stringify(goalData),
    });
  }

  async updateSavingsGoal(goalId: string, updates: UpdateSavingsGoalRequest): Promise<SavingsGoal> {
    return this.request<SavingsGoal>(`/goals/${goalId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Tithing
  async getTithingSummary(year?: number): Promise<TithingSummary> {
    const params = year ? `?year=${year}` : '';
    return this.request<TithingSummary>(`/tithing${params}`);
  }

  async recordTithingPayment(paymentData: CreateTithingRequest): Promise<any> {
    return this.request('/tithing', {
      method: 'POST',
      body: JSON.stringify(paymentData),
    });
  }

  // Family management
  async getFamilies(): Promise<Family[]> {
    return this.request<Family[]>('/families');
  }

  async getFamily(familyId: string): Promise<Family> {
    return this.request<Family>(`/families/${familyId}`);
  }

  async createFamily(familyData: CreateFamilyRequest): Promise<Family> {
    return this.request<Family>('/families', {
      method: 'POST',
      body: JSON.stringify(familyData),
    });
  }

  async inviteFamilyMember(familyId: string, invitationData: FamilyInvitationRequest): Promise<any> {
    return this.request(`/families/${familyId}/invitations`, {
      method: 'POST',
      body: JSON.stringify(invitationData),
    });
  }

  async acceptFamilyInvitation(invitationId: string): Promise<any> {
    return this.request(`/families/invitations/${invitationId}/accept`, {
      method: 'POST',
    });
  }

  // Subscription management
  async getSubscriptions(): Promise<Subscription[]> {
    return this.request<Subscription[]>('/subscriptions');
  }

  async createSubscription(subscriptionData: CreateSubscriptionRequest): Promise<Subscription> {
    return this.request<Subscription>('/subscriptions', {
      method: 'POST',
      body: JSON.stringify(subscriptionData),
    });
  }

  async updateSubscription(subscriptionId: string, updates: UpdateSubscriptionRequest): Promise<Subscription> {
    return this.request<Subscription>(`/subscriptions/${subscriptionId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async cancelSubscription(subscriptionId: string): Promise<void> {
    return this.request<void>(`/subscriptions/${subscriptionId}`, {
      method: 'DELETE',
    });
  }

  // Plaid integration
  async createLinkToken(userId: string): Promise<{ link_token: string; expiration: string }> {
    return this.request('/plaid/link-token', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }

  async exchangePublicToken(publicToken: string): Promise<{ access_token_id: string; accounts: Account[] }> {
    return this.request('/plaid/exchange-token', {
      method: 'POST',
      body: JSON.stringify({ public_token: publicToken }),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string; timestamp: string }> {
    return this.request('/health');
  }
}

// Custom error class for API errors
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Create and export the API client instance
export const apiClient = new ApiClient(API_BASE_URL);

// Query keys for React Query
export const queryKeys = {
  users: ['users'] as const,
  user: (id: string) => ['users', id] as const,
  currentUser: ['users', 'current'] as const,
  
  accounts: ['accounts'] as const,
  account: (id: string) => ['accounts', id] as const,
  
  transactions: (params?: any) => ['transactions', params] as const,
  transaction: (id: string) => ['transactions', id] as const,
  
  budgets: ['budgets'] as const,
  budget: (id: string) => ['budgets', id] as const,
  
  goals: ['goals'] as const,
  goal: (id: string) => ['goals', id] as const,
  
  tithing: (year?: number) => ['tithing', year] as const,
  
  families: ['families'] as const,
  family: (id: string) => ['families', id] as const,
  
  subscriptions: ['subscriptions'] as const,
  subscription: (id: string) => ['subscriptions', id] as const,
  
  health: ['health'] as const,
} as const;