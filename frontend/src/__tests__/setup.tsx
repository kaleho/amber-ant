import '@testing-library/jest-dom';
import React from 'react';
import { expect, afterEach, beforeAll, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { server } from './mocks/server';
import { AuthProvider } from '../contexts/AuthContext';
import { BudgetProvider } from '../contexts/BudgetContext';
import { FamilyProvider } from '../contexts/FamilyContext';
import { TithingProvider } from '../contexts/TithingContext';

// Extend Vitest's expect with jest-dom matchers
expect.extend({});

// Setup MSW server for API mocking
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  disconnect() {}
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() {}
  disconnect() {}
  unobserve() {}
};

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock as any;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock as any;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock scrollTo
global.scrollTo = vi.fn();

// Mock Auth0
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    user: {
      sub: 'user123',
      name: 'Test User',
      email: 'test@example.com',
    },
    isAuthenticated: true,
    isLoading: false,
    loginWithRedirect: vi.fn(),
    logout: vi.fn(),
  }),
  Auth0Provider: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/' }),
    useParams: () => ({}),
  };
});

// Performance monitoring for tests
const originalConsoleError = console.error;
console.error = (...args) => {
  if (args[0]?.includes?.('Warning: ReactDOM.render is no longer supported')) {
    return;
  }
  originalConsoleError(...args);
};

// Global test utilities
global.testUtils = {
  // Mock user with different roles
  mockUser: (role: 'parent' | 'teen' | 'pre_teen' | 'child' = 'parent') => ({
    sub: 'test-user-id',
    name: 'Test User',
    email: 'test@example.com',
    role,
  }),
  
  // Mock budget data
  mockBudgetCategory: (overrides = {}) => ({
    id: 'category-123',
    name: 'Test Category',
    budgetedAmount: 500,
    spentAmount: 200,
    period: 'monthly' as const,
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    color: '#3B82F6',
    isActive: true,
    tags: ['test'],
    priority: 'medium' as const,
    rollover: false,
    alerts: {
      at50Percent: false,
      at75Percent: true,
      at90Percent: true,
      at100Percent: true,
      customAlerts: []
    },
    ...overrides
  }),
  
  // Mock family member
  mockFamilyMember: (role: 'parent' | 'teen' | 'pre_teen' | 'child' = 'parent', overrides = {}) => ({
    id: 'member-123',
    name: 'Test Member',
    email: 'member@example.com',
    role,
    age: role === 'parent' ? 35 : 15,
    permissions: {
      canViewFamilyFinances: role === 'parent',
      canMakeTransactions: true,
      canViewOwnTransactions: true,
      canSetSavingsGoals: true,
      canReceiveAllowance: role !== 'parent',
      canGiveTithe: role !== 'child',
      maxTransactionAmount: role === 'parent' ? 10000 : role === 'teen' ? 200 : 50,
      requiresParentalApproval: role !== 'parent',
      canInviteMembers: role === 'parent',
      canManageFamily: role === 'parent',
      canViewReports: role === 'parent',
      canExportData: role === 'parent',
    },
    savings: {
      balance: 0,
      goals: []
    },
    ...overrides
  }),
  
  // Mock tithing record
  mockTithingRecord: (overrides = {}) => ({
    id: 'tithe-123',
    amount: 100,
    date: new Date().toISOString(),
    source: 'salary' as const,
    paymentMethod: 'check' as const,
    status: 'completed' as const,
    taxDeductible: true,
    ...overrides
  }),
  
  // Create test wrapper with providers
  createTestWrapper: (initialData = {}) => {
    return ({ children }: { children: React.ReactNode }) => (
      <BrowserRouter>
        <AuthProvider>
          <BudgetProvider initialData={initialData}>
            <FamilyProvider initialData={initialData}>
              <TithingProvider initialData={initialData}>
                {children}
              </TithingProvider>
            </FamilyProvider>
          </BudgetProvider>
        </AuthProvider>
      </BrowserRouter>
    );
  }
};

// Custom render function for testing components with contexts
export const renderWithProviders = (
  ui: React.ReactElement,
  options: {
    initialData?: any;
    route?: string;
  } = {}
) => {
  const { initialData = {}, route = '/' } = options;
  
  window.history.pushState({}, 'Test page', route);
  
  const Wrapper = global.testUtils.createTestWrapper(initialData);
  
  return {
    ...render(ui, { wrapper: Wrapper }),
    // Re-export utilities
    ...screen,
  };
};