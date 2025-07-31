# State Management Design

## Overview

The Faithful Finances application uses a hybrid state management approach combining React Context for global application state, React Query for server state management, and local component state for UI-specific concerns. This design ensures optimal performance, maintainability, and user experience across all 8 personas.

## State Architecture Diagram

```
Application State
├── Client State (React Context + useState)
│   ├── AuthContext
│   │   ├── user: User | null
│   │   ├── isAuthenticated: boolean
│   │   ├── permissions: UserPermissions
│   │   └── authActions: AuthActions
│   ├── PersonaContext
│   │   ├── currentPersona: Persona
│   │   ├── personaConfig: PersonaConfiguration
│   │   ├── capabilities: PersonaCapabilities
│   │   └── personaActions: PersonaActions
│   ├── FamilyContext
│   │   ├── family: Family | null
│   │   ├── members: FamilyMember[]
│   │   ├── permissions: FamilyPermissions
│   │   └── familyActions: FamilyActions
│   ├── ThemeContext
│   │   ├── theme: Theme
│   │   ├── personaTheme: PersonaTheme
│   │   └── themeActions: ThemeActions
│   └── NotificationContext
│       ├── notifications: Notification[]
│       ├── preferences: NotificationPreferences
│       └── notificationActions: NotificationActions
└── Server State (React Query)
    ├── User Data
    │   ├── Profile
    │   ├── Preferences
    │   └── Settings
    ├── Financial Data
    │   ├── Accounts
    │   ├── Transactions
    │   ├── Budgets
    │   └── Savings Goals
    ├── Family Data
    │   ├── Family Members
    │   ├── Invitations
    │   └── Shared Goals
    └── External Integrations
        ├── Plaid Data
        ├── Auth0 Profile
        └── Notification Services
```

## Context Providers Implementation

### 1. AuthContext

```typescript
interface User {
  id: string;
  email: string;
  name: string;
  persona: Persona;
  familyId?: string;
  familyRole?: FamilyRole;
  preferences: UserPreferences;
  createdAt: Date;
  updatedAt: Date;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: AuthError | null;
}

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (updates: ProfileUpdates) => Promise<void>;
  refreshToken: () => Promise<void>;
  resetError: () => void;
}

interface AuthContextType extends AuthState, AuthActions {}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  const login = async (credentials: LoginCredentials) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const user = await authService.login(credentials);
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as AuthError,
      }));
    }
  };

  const logout = async () => {
    await authService.logout();
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  };

  const updateProfile = async (updates: ProfileUpdates) => {
    if (!state.user) return;
    const updatedUser = await authService.updateProfile(state.user.id, updates);
    setState(prev => ({ ...prev, user: updatedUser }));
  };

  const refreshToken = async () => {
    try {
      const user = await authService.refreshToken();
      setState(prev => ({ ...prev, user }));
    } catch (error) {
      await logout();
    }
  };

  const resetError = () => {
    setState(prev => ({ ...prev, error: null }));
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    updateProfile,
    refreshToken,
    resetError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

### 2. PersonaContext

```typescript
interface PersonaConfiguration {
  dashboardLayout: DashboardLayout;
  navigationItems: NavigationItem[];
  capabilities: PersonaCapabilities;
  theme: PersonaTheme;
  budgetTemplate: BudgetTemplate;
  emergencyFundTarget: EmergencyFundConfig;
}

interface PersonaCapabilities {
  canConnectAccounts: boolean;
  canSplitTransactions: boolean;
  canManageBudget: boolean;
  canInviteFamily: boolean;
  requiresParentalApproval: boolean;
  maxSpendingWithoutApproval?: number;
  hasAdvancedFeatures: boolean;
}

interface PersonaTheme {
  primaryColor: string;
  accentColor: string;
  backgroundColor: string;
  textSize: 'small' | 'medium' | 'large' | 'extra-large';
  iconStyle: 'minimal' | 'detailed' | 'colorful';
  animationLevel: 'none' | 'minimal' | 'enhanced';
}

interface PersonaState {
  currentPersona: Persona;
  personaConfig: PersonaConfiguration;
  isConfigLoading: boolean;
}

interface PersonaActions {
  switchPersona: (persona: Persona) => Promise<void>;
  updatePersonaConfig: (updates: Partial<PersonaConfiguration>) => void;
  getPersonaCapabilities: () => PersonaCapabilities;
  getPersonaTheme: () => PersonaTheme;
}

interface PersonaContextType extends PersonaState, PersonaActions {}

const PersonaContext = createContext<PersonaContextType | null>(null);

export const PersonaProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { user } = useAuth();
  const [state, setState] = useState<PersonaState>({
    currentPersona: user?.persona || 'single_adult',
    personaConfig: getDefaultPersonaConfig(user?.persona || 'single_adult'),
    isConfigLoading: false,
  });

  const switchPersona = async (persona: Persona) => {
    setState(prev => ({ ...prev, isConfigLoading: true }));
    try {
      const config = await personaService.getPersonaConfig(persona);
      setState({
        currentPersona: persona,
        personaConfig: config,
        isConfigLoading: false,
      });
    } catch (error) {
      setState(prev => ({ ...prev, isConfigLoading: false }));
    }
  };

  const updatePersonaConfig = (updates: Partial<PersonaConfiguration>) => {
    setState(prev => ({
      ...prev,
      personaConfig: { ...prev.personaConfig, ...updates },
    }));
  };

  const getPersonaCapabilities = (): PersonaCapabilities => {
    return state.personaConfig.capabilities;
  };

  const getPersonaTheme = (): PersonaTheme => {
    return state.personaConfig.theme;
  };

  const value: PersonaContextType = {
    ...state,
    switchPersona,
    updatePersonaConfig,
    getPersonaCapabilities,
    getPersonaTheme,
  };

  return (
    <PersonaContext.Provider value={value}>{children}</PersonaContext.Provider>
  );
};

export const usePersona = () => {
  const context = useContext(PersonaContext);
  if (!context) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
};
```

### 3. FamilyContext

```typescript
interface Family {
  id: string;
  name: string;
  administratorId: string;
  members: FamilyMember[];
  settings: FamilySettings;
  createdAt: Date;
  updatedAt: Date;
}

interface FamilyMember {
  id: string;
  userId: string;
  name: string;
  email: string;
  role: FamilyRole;
  permissions: FamilyPermissions;
  status: MemberStatus;
  joinedAt: Date;
}

interface FamilyPermissions {
  canViewAccounts: boolean;
  canViewTransactions: boolean;
  canManageBudget: boolean;
  canApproveSpending: boolean;
  requiresApprovalOver?: number;
  canInviteMembers: boolean;
}

interface FamilySettings {
  jointTithing: boolean;
  sharedEmergencyFund: boolean;
  notificationCoordination: boolean;
  parentalOversight: boolean;
}

interface FamilyState {
  family: Family | null;
  members: FamilyMember[];
  pendingInvitations: FamilyInvitation[];
  userPermissions: FamilyPermissions;
  isLoading: boolean;
}

interface FamilyActions {
  loadFamily: () => Promise<void>;
  inviteMember: (invitation: FamilyInvitation) => Promise<void>;
  updateMemberPermissions: (
    memberId: string,
    permissions: FamilyPermissions
  ) => Promise<void>;
  removeMember: (memberId: string) => Promise<void>;
  updateFamilySettings: (settings: Partial<FamilySettings>) => Promise<void>;
  acceptInvitation: (invitationId: string) => Promise<void>;
  declineInvitation: (invitationId: string) => Promise<void>;
}

interface FamilyContextType extends FamilyState, FamilyActions {}

const FamilyContext = createContext<FamilyContextType | null>(null);

export const FamilyProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { user } = useAuth();
  const [state, setState] = useState<FamilyState>({
    family: null,
    members: [],
    pendingInvitations: [],
    userPermissions: getDefaultPermissions(),
    isLoading: false,
  });

  const loadFamily = async () => {
    if (!user?.familyId) return;
    
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      const family = await familyService.getFamily(user.familyId);
      const invitations = await familyService.getPendingInvitations(user.familyId);
      const permissions = await familyService.getUserPermissions(user.id);
      
      setState({
        family,
        members: family.members,
        pendingInvitations: invitations,
        userPermissions: permissions,
        isLoading: false,
      });
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  const inviteMember = async (invitation: FamilyInvitation) => {
    const newInvitation = await familyService.inviteMember(invitation);
    setState(prev => ({
      ...prev,
      pendingInvitations: [...prev.pendingInvitations, newInvitation],
    }));
  };

  const updateMemberPermissions = async (
    memberId: string,
    permissions: FamilyPermissions
  ) => {
    await familyService.updateMemberPermissions(memberId, permissions);
    setState(prev => ({
      ...prev,
      members: prev.members.map(member =>
        member.id === memberId ? { ...member, permissions } : member
      ),
    }));
  };

  const removeMember = async (memberId: string) => {
    await familyService.removeMember(memberId);
    setState(prev => ({
      ...prev,
      members: prev.members.filter(member => member.id !== memberId),
    }));
  };

  const updateFamilySettings = async (settings: Partial<FamilySettings>) => {
    if (!state.family) return;
    
    const updatedFamily = await familyService.updateSettings(
      state.family.id,
      settings
    );
    setState(prev => ({ ...prev, family: updatedFamily }));
  };

  const acceptInvitation = async (invitationId: string) => {
    await familyService.acceptInvitation(invitationId);
    await loadFamily(); // Refresh family data
  };

  const declineInvitation = async (invitationId: string) => {
    await familyService.declineInvitation(invitationId);
    setState(prev => ({
      ...prev,
      pendingInvitations: prev.pendingInvitations.filter(
        inv => inv.id !== invitationId
      ),
    }));
  };

  // Load family data when user changes
  useEffect(() => {
    if (user?.familyId) {
      loadFamily();
    }
  }, [user?.familyId]);

  const value: FamilyContextType = {
    ...state,
    loadFamily,
    inviteMember,
    updateMemberPermissions,
    removeMember,
    updateFamilySettings,
    acceptInvitation,
    declineInvitation,
  };

  return (
    <FamilyContext.Provider value={value}>{children}</FamilyContext.Provider>
  );
};

export const useFamily = () => {
  const context = useContext(FamilyContext);
  if (!context) {
    throw new Error('useFamily must be used within a FamilyProvider');
  }
  return context;
};
```

## React Query Configuration

### 1. Query Client Setup

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      retry: (failureCount, error) => {
        if (error.status === 401) return false; // Don't retry auth errors
        return failureCount < 3;
      },
    },
    mutations: {
      retry: false,
    },
  },
});

export const QueryProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => (
  <QueryClientProvider client={queryClient}>
    {children}
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>
);
```

### 2. Query Keys Factory

```typescript
export const queryKeys = {
  // User queries
  user: (userId: string) => ['user', userId] as const,
  userProfile: (userId: string) => ['user', userId, 'profile'] as const,
  userPreferences: (userId: string) => ['user', userId, 'preferences'] as const,

  // Account queries
  accounts: (userId: string) => ['accounts', userId] as const,
  account: (accountId: string) => ['account', accountId] as const,
  accountBalance: (accountId: string) => ['account', accountId, 'balance'] as const,

  // Transaction queries
  transactions: (accountId: string) => ['transactions', accountId] as const,
  transaction: (transactionId: string) => ['transaction', transactionId] as const,
  transactionsByCategory: (userId: string, category: string) =>
    ['transactions', userId, 'category', category] as const,
  transactionsByDateRange: (userId: string, startDate: string, endDate: string) =>
    ['transactions', userId, 'dateRange', startDate, endDate] as const,

  // Budget queries
  budgets: (userId: string) => ['budgets', userId] as const,
  budget: (budgetId: string) => ['budget', budgetId] as const,
  currentBudget: (userId: string) => ['budget', userId, 'current'] as const,
  budgetAnalytics: (budgetId: string) => ['budget', budgetId, 'analytics'] as const,

  // Savings queries
  savingsGoals: (userId: string) => ['savingsGoals', userId] as const,
  savingsGoal: (goalId: string) => ['savingsGoal', goalId] as const,
  emergencyFund: (userId: string) => ['emergencyFund', userId] as const,

  // Family queries
  family: (familyId: string) => ['family', familyId] as const,
  familyMembers: (familyId: string) => ['family', familyId, 'members'] as const,
  familyInvitations: (familyId: string) => ['family', familyId, 'invitations'] as const,
  familyPermissions: (userId: string) => ['family', 'permissions', userId] as const,

  // Tithing queries
  tithingHistory: (userId: string) => ['tithing', userId] as const,
  tithingSummary: (userId: string, year: number) =>
    ['tithing', userId, 'summary', year] as const,

  // External service queries
  plaidAccounts: (userId: string) => ['plaid', 'accounts', userId] as const,
  plaidTransactions: (accountId: string) => ['plaid', 'transactions', accountId] as const,
} as const;
```

### 3. Custom Hooks for Data Fetching

```typescript
// Account hooks
export const useAccounts = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.accounts(userId),
    queryFn: () => accountService.getAccounts(userId),
    enabled: !!userId,
  });
};

export const useAccount = (accountId: string) => {
  return useQuery({
    queryKey: queryKeys.account(accountId),
    queryFn: () => accountService.getAccount(accountId),
    enabled: !!accountId,
  });
};

// Transaction hooks
export const useTransactions = (accountId: string) => {
  return useInfiniteQuery({
    queryKey: queryKeys.transactions(accountId),
    queryFn: ({ pageParam = 0 }) =>
      transactionService.getTransactions(accountId, {
        offset: pageParam,
        limit: 50,
      }),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.hasMore ? allPages.length * 50 : undefined,
    enabled: !!accountId,
  });
};

export const useTransactionsByCategory = (userId: string, category: string) => {
  return useQuery({
    queryKey: queryKeys.transactionsByCategory(userId, category),
    queryFn: () => transactionService.getTransactionsByCategory(userId, category),
    enabled: !!userId && !!category,
  });
};

// Budget hooks
export const useCurrentBudget = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.currentBudget(userId),
    queryFn: () => budgetService.getCurrentBudget(userId),
    enabled: !!userId,
  });
};

export const useBudgetAnalytics = (budgetId: string) => {
  return useQuery({
    queryKey: queryKeys.budgetAnalytics(budgetId),
    queryFn: () => budgetService.getBudgetAnalytics(budgetId),
    enabled: !!budgetId,
    staleTime: 2 * 60 * 1000, // 2 minutes for analytics
  });
};

// Savings hooks
export const useSavingsGoals = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.savingsGoals(userId),
    queryFn: () => savingsService.getSavingsGoals(userId),
    enabled: !!userId,
  });
};

export const useEmergencyFund = (userId: string) => {
  return useQuery({
    queryKey: queryKeys.emergencyFund(userId),
    queryFn: () => savingsService.getEmergencyFund(userId),
    enabled: !!userId,
  });
};

// Family hooks
export const useFamilyMembers = (familyId?: string) => {
  return useQuery({
    queryKey: queryKeys.familyMembers(familyId!),
    queryFn: () => familyService.getFamilyMembers(familyId!),
    enabled: !!familyId,
  });
};

export const useFamilyInvitations = (familyId?: string) => {
  return useQuery({
    queryKey: queryKeys.familyInvitations(familyId!),
    queryFn: () => familyService.getFamilyInvitations(familyId!),
    enabled: !!familyId,
  });
};
```

### 4. Mutation Hooks

```typescript
// Transaction mutations
export const useUpdateTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      transactionId,
      updates,
    }: {
      transactionId: string;
      updates: TransactionUpdates;
    }) => transactionService.updateTransaction(transactionId, updates),
    onSuccess: (updatedTransaction) => {
      // Update transaction cache
      queryClient.setQueryData(
        queryKeys.transaction(updatedTransaction.id),
        updatedTransaction
      );

      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: queryKeys.transactions(updatedTransaction.accountId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgets(updatedTransaction.userId),
      });
    },
  });
};

export const useSplitTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      transactionId,
      splitData,
    }: {
      transactionId: string;
      splitData: TransactionSplit;
    }) => transactionService.splitTransaction(transactionId, splitData),
    onSuccess: (updatedTransaction) => {
      queryClient.setQueryData(
        queryKeys.transaction(updatedTransaction.id),
        updatedTransaction
      );
      queryClient.invalidateQueries({
        queryKey: queryKeys.transactions(updatedTransaction.accountId),
      });
    },
  });
};

// Budget mutations
export const useCreateBudget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (budgetData: CreateBudgetData) =>
      budgetService.createBudget(budgetData),
    onSuccess: (newBudget) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgets(newBudget.userId),
      });
      queryClient.setQueryData(
        queryKeys.currentBudget(newBudget.userId),
        newBudget
      );
    },
  });
};

export const useUpdateBudget = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      budgetId,
      updates,
    }: {
      budgetId: string;
      updates: BudgetUpdates;
    }) => budgetService.updateBudget(budgetId, updates),
    onSuccess: (updatedBudget) => {
      queryClient.setQueryData(queryKeys.budget(updatedBudget.id), updatedBudget);
      queryClient.invalidateQueries({
        queryKey: queryKeys.budgets(updatedBudget.userId),
      });
    },
  });
};

// Family mutations
export const useInviteFamilyMember = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitation: FamilyInvitation) =>
      familyService.inviteMember(invitation),
    onSuccess: (newInvitation) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.familyInvitations(newInvitation.familyId),
      });
    },
  });
};

export const useUpdateMemberPermissions = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      memberId,
      permissions,
    }: {
      memberId: string;
      permissions: FamilyPermissions;
    }) => familyService.updateMemberPermissions(memberId, permissions),
    onSuccess: (updatedMember) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.familyMembers(updatedMember.familyId),
      });
    },
  });
};
```

## Local State Management

### 1. Component State Patterns

```typescript
// Simple component state
const TransactionRow: React.FC<TransactionRowProps> = ({ transaction }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  return (
    <div>
      {/* Component UI */}
    </div>
  );
};

// Complex component state with reducer
interface TransactionSplitState {
  splits: TransactionSplit[];
  totalAllocated: number;
  remainingAmount: number;
  isValid: boolean;
  errors: ValidationError[];
}

type TransactionSplitAction =
  | { type: 'ADD_SPLIT'; payload: TransactionSplit }
  | { type: 'REMOVE_SPLIT'; payload: string }
  | { type: 'UPDATE_SPLIT'; payload: { id: string; split: Partial<TransactionSplit> } }
  | { type: 'VALIDATE_SPLITS' }
  | { type: 'RESET' };

const transactionSplitReducer = (
  state: TransactionSplitState,
  action: TransactionSplitAction
): TransactionSplitState => {
  switch (action.type) {
    case 'ADD_SPLIT':
      return {
        ...state,
        splits: [...state.splits, action.payload],
      };
    case 'REMOVE_SPLIT':
      return {
        ...state,
        splits: state.splits.filter(split => split.id !== action.payload),
      };
    case 'UPDATE_SPLIT':
      return {
        ...state,
        splits: state.splits.map(split =>
          split.id === action.payload.id
            ? { ...split, ...action.payload.split }
            : split
        ),
      };
    case 'VALIDATE_SPLITS':
      const totalAllocated = state.splits.reduce(
        (sum, split) => sum + split.amount,
        0
      );
      const remainingAmount = state.transaction.amount - totalAllocated;
      const isValid = remainingAmount === 0;
      const errors = isValid ? [] : [{ message: 'Splits must equal transaction amount' }];
      
      return {
        ...state,
        totalAllocated,
        remainingAmount,
        isValid,
        errors,
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
};

const TransactionSplitModal: React.FC<TransactionSplitModalProps> = ({
  transaction,
}) => {
  const [state, dispatch] = useReducer(transactionSplitReducer, {
    splits: [],
    totalAllocated: 0,
    remainingAmount: transaction.amount,
    isValid: false,
    errors: [],
  });

  // Component logic
};
```

### 2. Custom Hooks for State Logic

```typescript
// Custom hook for form state management
export const useFormState = <T>(initialState: T, validationSchema?: ZodSchema<T>) => {
  const [values, setValues] = useState<T>(initialState);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const setValue = (name: keyof T, value: T[keyof T]) => {
    setValues(prev => ({ ...prev, [name]: value }));
    if (touched[name as string]) {
      validateField(name, value);
    }
  };

  const setTouched = (name: keyof T) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    validateField(name, values[name]);
  };

  const validateField = (name: keyof T, value: T[keyof T]) => {
    if (!validationSchema) return;

    try {
      validationSchema.pick({ [name]: true }).parse({ [name]: value });
      setErrors(prev => ({ ...prev, [name]: undefined }));
    } catch (error) {
      if (error instanceof ZodError) {
        setErrors(prev => ({
          ...prev,
          [name]: error.errors[0].message,
        }));
      }
    }
  };

  const validate = () => {
    if (!validationSchema) return true;

    try {
      validationSchema.parse(values);
      setErrors({});
      return true;
    } catch (error) {
      if (error instanceof ZodError) {
        const fieldErrors = error.errors.reduce(
          (acc, err) => ({
            ...acc,
            [err.path[0]]: err.message,
          }),
          {}
        );
        setErrors(fieldErrors);
      }
      return false;
    }
  };

  const handleSubmit = async (onSubmit: (values: T) => Promise<void>) => {
    setIsSubmitting(true);
    
    if (validate()) {
      try {
        await onSubmit(values);
      } catch (error) {
        console.error('Form submission error:', error);
      }
    }
    
    setIsSubmitting(false);
  };

  const reset = () => {
    setValues(initialState);
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
  };

  return {
    values,
    errors,
    touched,
    isSubmitting,
    setValue,
    setTouched,
    validate,
    handleSubmit,
    reset,
  };
};

// Custom hook for pagination state
export const usePagination = (initialPage = 0, pageSize = 50) => {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageSize, setPageSize] = useState(pageSize);

  const goToPage = (page: number) => setCurrentPage(page);
  const nextPage = () => setCurrentPage(prev => prev + 1);
  const previousPage = () => setCurrentPage(prev => Math.max(0, prev - 1));
  const reset = () => setCurrentPage(initialPage);

  const offset = currentPage * pageSize;

  return {
    currentPage,
    pageSize,
    offset,
    goToPage,
    nextPage,
    previousPage,
    setPageSize,
    reset,
  };
};

// Custom hook for search/filter state
export const useSearchFilter = <T>(
  data: T[],
  searchFields: (keyof T)[],
  initialFilters: Record<string, any> = {}
) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState(initialFilters);
  const [sortBy, setSortBy] = useState<keyof T | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const filteredData = useMemo(() => {
    let result = data;

    // Apply search filter
    if (searchTerm) {
      result = result.filter(item =>
        searchFields.some(field =>
          String(item[field]).toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    // Apply custom filters
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        result = result.filter(item => {
          const itemValue = item[key as keyof T];
          if (Array.isArray(value)) {
            return value.includes(itemValue);
          }
          return itemValue === value;
        });
      }
    });

    // Apply sorting
    if (sortBy) {
      result = [...result].sort((a, b) => {
        const aValue = a[sortBy];
        const bValue = b[sortBy];
        
        if (sortDirection === 'asc') {
          return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
        } else {
          return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
        }
      });
    }

    return result;
  }, [data, searchTerm, filters, sortBy, sortDirection]);

  const updateFilter = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilters(initialFilters);
    setSortBy(null);
  };

  const toggleSort = (field: keyof T) => {
    if (sortBy === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDirection('asc');
    }
  };

  return {
    searchTerm,
    setSearchTerm,
    filters,
    updateFilter,
    sortBy,
    sortDirection,
    toggleSort,
    filteredData,
    clearFilters,
  };
};
```

## State Synchronization Patterns

### 1. Optimistic Updates

```typescript
export const useOptimisticTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateTransaction,
    onMutate: async (variables) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: queryKeys.transaction(variables.transactionId),
      });

      // Snapshot previous value
      const previousTransaction = queryClient.getQueryData(
        queryKeys.transaction(variables.transactionId)
      );

      // Optimistically update
      queryClient.setQueryData(
        queryKeys.transaction(variables.transactionId),
        (old: Transaction) => ({ ...old, ...variables.updates })
      );

      return { previousTransaction };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      queryClient.setQueryData(
        queryKeys.transaction(variables.transactionId),
        context?.previousTransaction
      );
    },
    onSettled: (data, error, variables) => {
      // Always refetch after mutation
      queryClient.invalidateQueries({
        queryKey: queryKeys.transaction(variables.transactionId),
      });
    },
  });
};
```

### 2. Real-time Synchronization

```typescript
export const useRealTimeSync = (userId: string) => {
  const queryClient = useQueryClient();

  useEffect(() => {
    const eventSource = new EventSource(`/api/users/${userId}/events`);

    eventSource.addEventListener('transaction_updated', (event) => {
      const transaction = JSON.parse(event.data);
      
      // Update specific transaction
      queryClient.setQueryData(
        queryKeys.transaction(transaction.id),
        transaction
      );

      // Invalidate transaction list
      queryClient.invalidateQueries({
        queryKey: queryKeys.transactions(transaction.accountId),
      });
    });

    eventSource.addEventListener('account_balance_updated', (event) => {
      const { accountId, balance } = JSON.parse(event.data);
      
      queryClient.setQueryData(
        queryKeys.accountBalance(accountId),
        balance
      );
    });

    return () => {
      eventSource.close();
    };
  }, [userId, queryClient]);
};
```

### 3. Background Sync

```typescript
export const useBackgroundSync = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    const interval = setInterval(() => {
      // Refetch critical data in background
      queryClient.refetchQueries({
        queryKey: ['accounts'],
        type: 'active',
      });
      
      queryClient.refetchQueries({
        queryKey: ['transactions'],
        type: 'active',
      });
    }, 5 * 60 * 1000); // Every 5 minutes

    return () => clearInterval(interval);
  }, [queryClient]);
};
```

This comprehensive state management design ensures optimal performance, maintainability, and user experience across all persona types while providing robust data synchronization and error handling capabilities.