/**
 * Application Configuration Constants
 * Environment-specific settings and feature flags
 */

import { PersonaType, PlaidProduct, SubscriptionPlan } from '../types';

// ==================== API CONFIGURATION ====================

export const API_CONFIG = {
  BASE_URL: import.meta.env.DEV 
    ? 'http://localhost:3000/api' 
    : 'https://api.faithfulfinances.com',
  
  TIMEOUT: 10000, // 10 seconds
  RETRY_ATTEMPTS: 3,
  
  ENDPOINTS: {
    // Authentication
    AUTH: {
      LOGIN: '/auth/login',
      REGISTER: '/auth/register',
      REFRESH: '/auth/refresh',
      LOGOUT: '/auth/logout',
      VERIFY: '/auth/verify',
    },
    
    // User Management
    USERS: {
      PROFILE: '/users/profile',
      PREFERENCES: '/users/preferences',
      SUBSCRIPTION: '/users/subscription',
    },
    
    // Accounts & Banking
    ACCOUNTS: {
      LIST: '/accounts',
      CONNECT: '/accounts/connect',
      DISCONNECT: '/accounts/disconnect',
      BALANCES: '/accounts/balances',
      SYNC: '/accounts/sync',
    },
    
    // Transactions
    TRANSACTIONS: {
      LIST: '/transactions',
      CATEGORIZE: '/transactions/categorize',
      SPLIT: '/transactions/split',
      SYNC: '/transactions/sync',
      ANALYTICS: '/transactions/analytics',
    },
    
    // Budgets
    BUDGETS: {
      LIST: '/budgets',
      CREATE: '/budgets',
      UPDATE: '/budgets',
      DELETE: '/budgets',
      TEMPLATES: '/budgets/templates',
    },
    
    // Savings Goals
    GOALS: {
      LIST: '/goals',
      CREATE: '/goals',
      UPDATE: '/goals',
      DELETE: '/goals',
      PROGRESS: '/goals/progress',
    },
    
    // Tithing
    TITHING: {
      SUMMARY: '/tithing/summary',
      PAYMENTS: '/tithing/payments',
      CALCULATE: '/tithing/calculate',
      TRACK: '/tithing/track',
    },
    
    // Family Management
    FAMILY: {
      CREATE: '/family',
      MEMBERS: '/family/members',
      INVITE: '/family/invite',
      PERMISSIONS: '/family/permissions',
      SETTINGS: '/family/settings',
    },
    
    // Plaid Integration
    PLAID: {
      LINK_TOKEN: '/plaid/link-token',
      EXCHANGE_TOKEN: '/plaid/exchange-token',
      ACCOUNTS: '/plaid/accounts',
      TRANSACTIONS: '/plaid/transactions',
      WEBHOOKS: '/plaid/webhooks',
    },
    
    // Stripe Integration
    STRIPE: {
      CUSTOMER: '/stripe/customer',
      SUBSCRIPTION: '/stripe/subscription',
      PAYMENT_METHODS: '/stripe/payment-methods',
      INVOICES: '/stripe/invoices',
    },
  },
};

// ==================== AUTHENTICATION CONFIGURATION ====================

export const AUTH0_CONFIG = {
  domain: import.meta.env.DEV 
    ? 'faithful-finances-dev.us.auth0.com' 
    : 'faithful-finances.us.auth0.com',
  
  clientId: import.meta.env.DEV 
    ? 'YOUR_DEV_CLIENT_ID' 
    : 'YOUR_PROD_CLIENT_ID',
  
  audience: 'https://api.faithfulfinances.com',
  scope: 'openid profile email offline_access',
  
  // Additional Auth0 settings
  customScheme: 'com.faithfulfinances',
  additionalParameters: {},
  
  // Leeway for token validation (in seconds)
  leeway: 60,
};

// ==================== PLAID CONFIGURATION ====================

export const PLAID_CONFIG = {
  environment: import.meta.env.DEV ? 'sandbox' : 'production',
  
  publicKey: import.meta.env.DEV 
    ? 'YOUR_SANDBOX_PUBLIC_KEY' 
    : 'YOUR_PRODUCTION_PUBLIC_KEY',
  
  clientName: 'Faithful Finances',
  
  products: [
    'transactions',
    'auth',
    'identity',
  ] as PlaidProduct[],
  
  countryCodes: ['US'],
  language: 'en',
  
  // Institution filtering (optional)
  institutionIds: [], // Empty means all institutions
  
  // Link customization
  linkCustomization: {
    title: 'Connect Your Bank Account',
    subtitle: 'Faithful Finances uses bank-level security to connect to your account.',
    primaryColor: '#2E7D32',
    logo: 'https://faithfulfinances.com/logo.png',
  },
  
  // Webhook configuration
  webhook: {
    url: import.meta.env.DEV 
      ? 'https://dev-api.faithfulfinances.com/plaid/webhooks'
      : 'https://api.faithfulfinances.com/plaid/webhooks',
    
    // Webhook verification token
    verification_key: 'YOUR_WEBHOOK_VERIFICATION_KEY',
  },
};

// ==================== STRIPE CONFIGURATION ====================

export const STRIPE_CONFIG = {
  publishableKey: import.meta.env.DEV 
    ? 'pk_test_YOUR_TEST_KEY' 
    : 'pk_live_YOUR_LIVE_KEY',
  
  merchantId: 'merchant.com.faithfulfinances',
  urlScheme: 'faithful-finances',
  
  // Subscription plans
  plans: {
    free_individual: {
      priceId: import.meta.env.DEV ? 'price_test_free_individual' : 'price_prod_free_individual',
      features: [
        'Basic budgeting',
        'Transaction categorization',
        'Tithing tracking',
        '1 bank account connection',
        'Email support',
      ],
    },
    premium_individual: {
      priceId: import.meta.env.DEV ? 'price_test_premium_individual' : 'price_prod_premium_individual',
      features: [
        'Advanced budgeting',
        'Unlimited bank connections',
        'Investment tracking',
        'Export capabilities',
        'Priority support',
        'Advanced analytics',
      ],
    },
    free_family: {
      priceId: import.meta.env.DEV ? 'price_test_free_family' : 'price_prod_free_family',
      features: [
        'All individual features',
        'Up to 4 family members',
        'Parental controls',
        'Shared goals tracking',
        'Family budget coordination',
      ],
    },
    premium_family: {
      priceId: import.meta.env.DEV ? 'price_test_premium_family' : 'price_prod_premium_family',
      features: [
        'All premium individual features',
        'Unlimited family members',
        'Advanced parental controls',
        'Family financial education',
        'Dedicated family support',
        'Custom family reports',
      ],
    },
  } as Record<SubscriptionPlan, { priceId: string; features: string[] }>,
};

// ==================== PERSONA CONFIGURATION ====================

export const PERSONA_CONFIG: Record<PersonaType, {
  name: string;
  description: string;
  ageRange: string;
  features: string[];
  restrictions: string[];
  defaultSubscription: SubscriptionPlan;
}> = {
  pre_teen: {
    name: 'Pre-Teen (8-14)',
    description: 'Learning basic money management with parental guidance',
    ageRange: '8-14 years',
    features: [
      'Simple budgeting interface',
      'Gamified learning',
      'Parental oversight',
      'Basic savings goals',
      'Tithing education',
    ],
    restrictions: [
      'No bank account connections',
      'Requires parental approval',
      'Limited transaction types',
      'Educational content only',
    ],
    defaultSubscription: 'free_family',
  },
  
  teen: {
    name: 'Teen (15-17)',
    description: 'Building financial independence with guidance',
    ageRange: '15-17 years',
    features: [
      'Student bank account integration',
      'Achievement system',
      'Educational resources',
      'Basic investment tracking',
      'Part-time job income tracking',
    ],
    restrictions: [
      'Requires parental consent',
      'Limited account types',
      'Spending approval workflows',
    ],
    defaultSubscription: 'free_family',
  },
  
  college_student: {
    name: 'College Student (18-22)',
    description: 'Managing limited resources efficiently',
    ageRange: '18-22 years',
    features: [
      'Semester-based budgeting',
      'Student loan tracking',
      'Irregular income management',
      'Campus-specific features',
      'Academic calendar integration',
    ],
    restrictions: [
      'Limited premium features',
    ],
    defaultSubscription: 'free_individual',
  },
  
  single_adult: {
    name: 'Single Adult (25-40)',
    description: 'Comprehensive financial management',
    ageRange: '25-40 years',
    features: [
      'Full feature access',
      'Investment tracking',
      'Career-focused budgeting',
      'Advanced analytics',
      'Tax optimization',
    ],
    restrictions: [],
    defaultSubscription: 'premium_individual',
  },
  
  married_couple: {
    name: 'Married Couple',
    description: 'Joint financial coordination',
    ageRange: '25-65 years',
    features: [
      'Joint account management',
      'Shared goal tracking',
      'Spouse coordination tools',
      'Family planning features',
      'Communication tools',
    ],
    restrictions: [],
    defaultSubscription: 'premium_family',
  },
  
  single_parent: {
    name: 'Single Parent',
    description: 'Priority-focused financial management',
    ageRange: '25-45 years',
    features: [
      'Crisis prevention tools',
      'Child-focused budgeting',
      'Enhanced emergency planning',
      'Time-efficient interface',
      'Community resources',
    ],
    restrictions: [],
    defaultSubscription: 'premium_family',
  },
  
  two_parent_family: {
    name: 'Two Parent Family',
    description: 'Complex family financial coordination',
    ageRange: '30-50 years',
    features: [
      'Dual-income management',
      'Children education planning',
      'Family goal coordination',
      'Extended family planning',
      'Legacy planning tools',
    ],
    restrictions: [],
    defaultSubscription: 'premium_family',
  },
  
  fixed_income: {
    name: 'Fixed Income (55+)',
    description: 'Retirement-focused financial management',
    ageRange: '55+ years',
    features: [
      'Healthcare expense tracking',
      'Retirement income management',
      'Simplified interface',
      'Legacy planning',
      'Healthcare integration',
    ],
    restrictions: [],
    defaultSubscription: 'premium_individual',
  },
};

// ==================== FEATURE FLAGS ====================

export const FEATURE_FLAGS = {
  // Core Features
  PLAID_INTEGRATION: true,
  STRIPE_PAYMENTS: true,
  FAMILY_MANAGEMENT: true,
  OFFLINE_SUPPORT: true,
  
  // Advanced Features
  INVESTMENT_TRACKING: true,
  TAX_OPTIMIZATION: true,
  VOICE_COMMANDS: import.meta.env.DEV ? true : false, // Beta feature
  AI_CATEGORIZATION: true,
  
  // Persona-specific Features
  GAMIFICATION: true,
  PARENTAL_CONTROLS: true,
  ACCESSIBILITY_FEATURES: true,
  
  // Experimental Features
  CRYPTO_TRACKING: false,
  INTERNATIONAL_ACCOUNTS: false,
  BUSINESS_FEATURES: false,
  
  // Development Features
  DEBUG_MODE: import.meta.env.DEV,
  MOCK_DATA: import.meta.env.DEV,
  ANALYTICS_LOGGING: !import.meta.env.DEV,
};

// ==================== UI CONFIGURATION ====================

export const UI_CONFIG = {
  // Animation timings (in milliseconds)
  ANIMATION: {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500,
    VERY_SLOW: 1000,
  },
  
  // Layout dimensions
  LAYOUT: {
    HEADER_HEIGHT: 60,
    TAB_BAR_HEIGHT: 60,
    CARD_BORDER_RADIUS: 12,
    BUTTON_BORDER_RADIUS: 8,
    INPUT_BORDER_RADIUS: 8,
  },
  
  // Typography scaling
  TYPOGRAPHY: {
    SCALE_FACTOR: 1.0, // Can be adjusted for accessibility
    LINE_HEIGHT_RATIO: 1.4,
  },
  
  // Haptic feedback patterns
  HAPTICS: {
    LIGHT: 'light',
    MEDIUM: 'medium',
    HEAVY: 'heavy',
    SUCCESS: 'notificationSuccess',
    WARNING: 'notificationWarning',
    ERROR: 'notificationError',
  },
  
  // Loading states
  LOADING: {
    SKELETON_ANIMATION_SPEED: 1000,
    MINIMUM_LOADING_TIME: 500,
    TIMEOUT_DURATION: 30000,
  },
};

// ==================== BUSINESS RULES ====================

export const BUSINESS_RULES = {
  // Tithing calculation
  TITHING: {
    DEFAULT_PERCENTAGE: 0.10, // 10%
    MINIMUM_AMOUNT: 0.01,
    CALCULATION_BASIS: 'gross_income', // or 'net_income'
  },
  
  // Budget recommendations
  BUDGET: {
    EMERGENCY_FUND_MONTHS: {
      single_adult: 6,
      married_couple: 6,
      single_parent: 9,
      two_parent_family: 6,
      fixed_income: 12,
      college_student: 3,
      teen: 1,
      pre_teen: 0.5,
    },
    
    MAX_DISCRETIONARY_PERCENTAGE: 0.30, // 30% max for wants
    FIXED_EXPENSES_PRIORITY: ['tithing', 'housing', 'utilities', 'groceries', 'transportation'],
  },
  
  // Transaction categorization
  CATEGORIZATION: {
    AUTO_CATEGORIZE_CONFIDENCE_THRESHOLD: 0.85,
    LEARNING_SAMPLE_SIZE: 10,
    SPLIT_SUGGESTIONS_MIN_AMOUNT: 25.00,
  },
  
  // Family permissions
  FAMILY: {
    MAX_FAMILY_MEMBERS: {
      free_family: 4,
      premium_family: 20,
    },
    APPROVAL_THRESHOLDS: {
      pre_teen: 0.01, // Requires approval for any amount
      teen: 50.00,
      college_student: 100.00,
    },
  },
  
  // Account limits
  ACCOUNTS: {
    MAX_CONNECTIONS: {
      free_individual: 1,
      premium_individual: 10,
      free_family: 2,
      premium_family: 20,
    },
  },
};

// ==================== ANALYTICS CONFIGURATION ====================

export const ANALYTICS_CONFIG = {
  // Event tracking
  EVENTS: {
    USER_SIGNUP: 'user_signup',
    ACCOUNT_CONNECTED: 'account_connected',
    TRANSACTION_CATEGORIZED: 'transaction_categorized',
    BUDGET_CREATED: 'budget_created',
    GOAL_ACHIEVED: 'goal_achieved',
    FAMILY_INVITED: 'family_invited',
    SUBSCRIPTION_UPGRADED: 'subscription_upgraded',
  },
  
  // Performance monitoring
  PERFORMANCE: {
    TRACK_USER_TIMING: true,
    TRACK_NETWORK_REQUESTS: true,
    TRACK_ERROR_RATES: true,
    SAMPLE_RATE: import.meta.env.DEV ? 1.0 : 0.1,
  },
  
  // Privacy settings
  PRIVACY: {
    ANONYMIZE_PII: true,
    RESPECT_DO_NOT_TRACK: true,
    DATA_RETENTION_DAYS: 365,
  },
};

// ==================== NOTIFICATION CONFIGURATION ====================

export const NOTIFICATION_CONFIG = {
  // Default notification settings by persona
  DEFAULTS: {
    pre_teen: {
      email: false,
      push: false,
      sms: false,
      frequency: 'weekly',
    },
    teen: {
      email: false,
      push: true,
      sms: false,
      frequency: 'immediate',
    },
    college_student: {
      email: true,
      push: true,
      sms: false,
      frequency: 'daily',
    },
    single_adult: {
      email: true,
      push: true,
      sms: false,
      frequency: 'immediate',
    },
    married_couple: {
      email: true,
      push: true,
      sms: false,
      frequency: 'immediate',
    },
    single_parent: {
      email: true,
      push: true,
      sms: true,
      frequency: 'immediate',
    },
    two_parent_family: {
      email: true,
      push: true,
      sms: false,
      frequency: 'immediate',
    },
    fixed_income: {
      email: true,
      push: false,
      sms: true,
      frequency: 'weekly',
    },
  },
  
  // Notification categories
  CATEGORIES: {
    FINANCIAL_ALERTS: 'financial_alerts',
    BUDGET_UPDATES: 'budget_updates',
    GOAL_PROGRESS: 'goal_progress',
    FAMILY_ACTIVITIES: 'family_activities',
    EDUCATIONAL_CONTENT: 'educational_content',
    SYSTEM_UPDATES: 'system_updates',
  },
  
  // Quiet hours (24-hour format)
  QUIET_HOURS: {
    DEFAULT_START: 22, // 10 PM
    DEFAULT_END: 7,    // 7 AM
  },
};