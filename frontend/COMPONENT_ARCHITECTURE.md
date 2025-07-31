# Component Architecture Design

## Component Hierarchy Diagram

```
App
├── AuthContext.Provider
├── PersonaContext.Provider
├── FamilyContext.Provider
├── ThemeContext.Provider
└── QueryClient.Provider
    └── Router
        ├── AuthLayout
        │   ├── LoginPage
        │   ├── OnboardingWizard
        │   │   ├── PersonaSelector
        │   │   ├── PersonaSetup
        │   │   └── AccountConnection
        │   └── PersonaSetupPage
        └── AppLayout
            ├── NavigationBar
            │   ├── PersonaNavigation
            │   ├── QuickActions
            │   └── NotificationBadge
            ├── Sidebar (Desktop)
            │   ├── NavigationMenu
            │   ├── QuickStats
            │   └── FamilyIndicator
            ├── MobileNav (Mobile)
            │   └── BottomNavigation
            └── MainContent
                ├── DashboardPage
                │   ├── DashboardContainer
                │   │   ├── PersonaDashboard
                │   │   ├── QuickStatsWidget
                │   │   ├── TithingCalculatorWidget
                │   │   ├── RecentTransactions
                │   │   └── SavingsProgress
                │   └── NotificationToasts
                ├── AccountsPage
                │   ├── PlaidConnectionManager
                │   ├── AccountOverview
                │   └── AccountList
                ├── TransactionsPage
                │   ├── TransactionHistory
                │   │   ├── TransactionCategorizationRow
                │   │   ├── TransactionSplitModal
                │   │   └── QuickSplitPresets
                │   ├── TransactionFilters
                │   └── BulkActions
                ├── BudgetPage
                │   ├── BudgetPlannerWizard
                │   ├── BudgetTracker
                │   │   ├── CategoryProgressBars
                │   │   └── OverspendingAlerts
                │   └── ExpenseCategorizationTool
                ├── SavingsPage
                │   ├── SavingsGoalTracker
                │   ├── EmergencyFundCalculator
                │   └── GoalProgressVisualization
                ├── TithingPage
                │   ├── TithingCalculator
                │   ├── TithingHistory
                │   └── GivingInsights
                ├── FamilyPage
                │   ├── FamilyMemberManager
                │   ├── ParentalControls
                │   ├── SpouseCoordination
                │   └── FamilyInvitation
                └── SettingsPage
                    ├── ProfileSettings
                    ├── NotificationSettings
                    ├── PrivacyControls
                    └── SecuritySettings
```

## Core Component Specifications

### 1. AppLayout Component

```typescript
interface AppLayoutProps {
  children: React.ReactNode;
}

interface AppLayoutState {
  sidebarCollapsed: boolean;
  mobileMenuOpen: boolean;
  notificationsPanelOpen: boolean;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  // Responsive layout management
  // Theme switching capability
  // Notification system integration
  // Accessibility features
};
```

**Features:**
- **Responsive Grid System**: CSS Grid with Tailwind breakpoints
- **Theme Provider Integration**: Light/dark/auto theme switching
- **Notification Toast Container**: Global notification system
- **Focus Management**: Keyboard navigation and skip links
- **Loading States**: Global loading indicators

### 2. NavigationBar Component

```typescript
interface NavigationBarProps {
  persona: Persona;
  family?: Family;
  notifications: Notification[];
}

const NavigationBar: React.FC<NavigationBarProps> = ({
  persona,
  family,
  notifications,
}) => {
  // Persona-specific navigation items
  // Family context indicators
  // Quick action buttons
  // Notification badge
};
```

**Persona Adaptations:**
- **Pre-Teen**: 4 large icon buttons with text labels
- **Teen**: Modern icon-based navigation with 5-6 items
- **College Student**: Mobile-optimized bottom navigation
- **Single Adult**: Comprehensive sidebar with categories
- **Married Couple**: Joint/individual view toggle
- **Single Parent**: Priority-based navigation with shortcuts
- **Two Parent Family**: Family overview prominent
- **Fixed-Income**: Large text, simplified 4-item navigation

### 3. DashboardContainer Component

```typescript
interface DashboardContainerProps {
  persona: Persona;
  userId: string;
  familyId?: string;
}

interface DashboardConfig {
  widgets: WidgetConfig[];
  layout: LayoutConfig;
  theme: PersonaTheme;
}

const DashboardContainer: React.FC<DashboardContainerProps> = ({
  persona,
  userId,
  familyId,
}) => {
  // Load persona-specific dashboard configuration
  // Render appropriate widgets based on persona
  // Handle real-time data updates
  // Manage loading and error states
};
```

**Widget System:**
- **Modular Architecture**: Independent widget components
- **Drag-and-Drop**: Customizable layout (advanced personas)
- **Real-time Updates**: WebSocket or polling for live data
- **Responsive Design**: Adaptive grid based on screen size

### 4. TransactionSplitModal Component

```typescript
interface TransactionSplitModalProps {
  transaction: Transaction;
  isOpen: boolean;
  onClose: () => void;
  onSave: (splitData: TransactionSplit) => Promise<void>;
}

interface TransactionSplit {
  fixedCategories: CategoryAllocation[];
  discretionaryCategories: CategoryAllocation[];
  totalAllocated: number;
}

const TransactionSplitModal: React.FC<TransactionSplitModalProps> = ({
  transaction,
  isOpen,
  onClose,
  onSave,
}) => {
  // Interactive split interface with drag-and-drop
  // Smart suggestions based on merchant and history
  // Real-time validation and total checking
  // Stewardship guidance integration
};
```

**Features:**
- **Dual Categorization**: Plaid category + Fixed/Discretionary
- **Smart Suggestions**: ML-powered split recommendations
- **Visual Validation**: Real-time total validation with error states
- **Preset Options**: Common split ratios (70/30, 80/20, etc.)
- **Stewardship Guidance**: Biblical principles panel

### 5. FamilyMemberManager Component

```typescript
interface FamilyMemberManagerProps {
  family: Family;
  currentUser: User;
  permissions: UserPermissions;
}

interface FamilyMember {
  id: string;
  userId: string;
  name: string;
  email: string;
  role: FamilyRole;
  permissions: FamilyPermissions;
  status: MemberStatus;
}

const FamilyMemberManager: React.FC<FamilyMemberManagerProps> = ({
  family,
  currentUser,
  permissions,
}) => {
  // Family member invitation system
  // Role and permission management
  // Activity monitoring and audit trails
  // Emergency access protocols
};
```

**Security Features:**
- **Secure Invitations**: Email-based with token verification
- **Permission Matrix**: Granular access control
- **Audit Logging**: All family activities tracked
- **Emergency Access**: Time-bound support access

## Persona-Specific Component Variations

### Pre-Teen Components

#### GameifiedProgressTracker
```typescript
interface GameifiedProgressTrackerProps {
  userId: string;
  parentId: string;
  achievements: Achievement[];
  currentGoals: SavingsGoal[];
}

const GameifiedProgressTracker: React.FC<GameifiedProgressTrackerProps> = ({
  userId,
  parentId,
  achievements,
  currentGoals,
}) => {
  // Achievement badge system
  // Progress animations and celebrations
  // Parent-child collaboration interface
  // Educational content delivery
};
```

#### ParentChildCollaboration
```typescript
interface ParentChildCollaborationProps {
  childId: string;
  parentId: string;
  pendingApprovals: ApprovalRequest[];
  sharedGoals: SharedGoal[];
}

const ParentChildCollaboration: React.FC<ParentChildCollaborationProps> = ({
  childId,
  parentId,
  pendingApprovals,
  sharedGoals,
}) => {
  // Shared financial goal interface
  // Parent approval workflow
  // Educational discussion prompts
  // Achievement sharing system
};
```

### Single Parent Components

#### CrisisPreventionSystem
```typescript
interface CrisisPreventionSystemProps {
  userId: string;
  accounts: Account[];
  emergencyFund: SavingsGoal;
  children: FamilyMember[];
}

const CrisisPreventionSystem: React.FC<CrisisPreventionSystemProps> = ({
  userId,
  accounts,
  emergencyFund,
  children,
}) => {
  // Early warning system for financial stress
  // Emergency fund depletion alerts
  // Community resource integration
  // Crisis intervention workflow
};
```

#### TimeEfficientInterface
```typescript
interface TimeEfficientInterfaceProps {
  userId: string;
  quickActions: QuickAction[];
  batchDecisions: BatchDecision[];
}

const TimeEfficientInterface: React.FC<TimeEfficientInterfaceProps> = ({
  userId,
  quickActions,
  batchDecisions,
}) => {
  // Batched decision-making interface
  // Quick-action buttons for common tasks
  // Voice command integration
  // Mobile-optimized for busy parents
};
```

### Fixed-Income Components

#### AccessibilityInterface
```typescript
interface AccessibilityInterfaceProps {
  userId: string;
  fontSize: 'large' | 'extra-large';
  highContrast: boolean;
  voiceEnabled: boolean;
}

const AccessibilityInterface: React.FC<AccessibilityInterfaceProps> = ({
  userId,
  fontSize,
  highContrast,
  voiceEnabled,
}) => {
  // Large fonts and high contrast themes
  // Voice-activated navigation
  // Simplified language and instructions
  // Phone support integration
};
```

#### HealthcareExpenseTracker
```typescript
interface HealthcareExpenseTrackerProps {
  userId: string;
  healthcareAccounts: Account[];
  insuranceInfo: InsuranceInfo;
  prescriptions: Prescription[];
}

const HealthcareExpenseTracker: React.FC<HealthcareExpenseTrackerProps> = ({
  userId,
  healthcareAccounts,
  insuranceInfo,
  prescriptions,
}) => {
  // Medicare and insurance integration
  // Prescription cost tracking
  // Healthcare provider expense sharing
  // Medical emergency fund management
};
```

## Component Communication Patterns

### 1. Parent-Child Communication
```typescript
// Parent passes data down
<TransactionHistory
  transactions={transactions}
  onTransactionSelect={handleTransactionSelect}
  onBulkAction={handleBulkAction}
/>

// Child communicates up via callbacks
const TransactionRow: React.FC<TransactionRowProps> = ({
  transaction,
  onSelect,
  onEdit,
}) => {
  return (
    <div onClick={() => onSelect(transaction.id)}>
      {/* Transaction content */}
    </div>
  );
};
```

### 2. Context-Based Communication
```typescript
// Provider makes data available globally
const PersonaContext = createContext<PersonaContextType>();

// Components consume context data
const Dashboard: React.FC = () => {
  const { currentPersona, personaConfig } = useContext(PersonaContext);
  // Use persona data to customize interface
};
```

### 3. Event-Based Communication
```typescript
// Custom event system for loose coupling
const useEventBus = () => {
  const emit = (event: string, data: any) => {
    window.dispatchEvent(new CustomEvent(event, { detail: data }));
  };

  const listen = (event: string, callback: (data: any) => void) => {
    window.addEventListener(event, (e) => callback(e.detail));
  };

  return { emit, listen };
};
```

## Component Lifecycle Management

### 1. Loading States
```typescript
const ComponentWithLoading: React.FC = () => {
  const { data, isLoading, error } = useQuery('key', fetchData);

  if (isLoading) return <SkeletonLoader />;
  if (error) return <ErrorBoundary error={error} />;
  return <ComponentContent data={data} />;
};
```

### 2. Error Boundaries
```typescript
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback onRetry={this.handleRetry} />;
    }

    return this.props.children;
  }
}
```

### 3. Performance Optimization
```typescript
// Memoization for expensive components
const ExpensiveComponent = React.memo<ExpensiveComponentProps>(
  ({ data, onAction }) => {
    const processedData = useMemo(() => processData(data), [data]);
    return <div>{/* Expensive rendering */}</div>;
  },
  (prevProps, nextProps) => {
    // Custom comparison function
    return prevProps.data.id === nextProps.data.id;
  }
);

// Virtual scrolling for large lists
const VirtualizedTransactionList: React.FC = () => {
  const { data } = useInfiniteQuery('transactions', fetchTransactions);
  
  return (
    <FixedSizeList
      height={600}
      itemCount={data.length}
      itemSize={80}
      itemData={data}
    >
      {TransactionRow}
    </FixedSizeList>
  );
};
```

## Component Testing Strategy

### 1. Unit Testing
```typescript
describe('TransactionSplitModal', () => {
  it('validates split amounts correctly', () => {
    render(
      <TransactionSplitModal
        transaction={mockTransaction}
        isOpen={true}
        onClose={jest.fn()}
        onSave={jest.fn()}
      />
    );

    // Test split validation logic
    const fixedInput = screen.getByLabelText('Fixed Amount');
    fireEvent.change(fixedInput, { target: { value: '50' } });

    expect(screen.getByText('Remaining: $50.00')).toBeInTheDocument();
  });
});
```

### 2. Integration Testing
```typescript
describe('Dashboard Integration', () => {
  it('loads persona-specific dashboard correctly', async () => {
    const mockUser = { persona: 'single_adult' };
    
    render(
      <PersonaContext.Provider value={{ currentPersona: 'single_adult' }}>
        <DashboardContainer userId="test-user" />
      </PersonaContext.Provider>
    );

    await waitFor(() => {
      expect(screen.getByText('Professional Dashboard')).toBeInTheDocument();
    });
  });
});
```

### 3. Visual Regression Testing
```typescript
// Storybook stories for visual testing
export default {
  title: 'Components/TransactionSplitModal',
  component: TransactionSplitModal,
};

export const Default = () => (
  <TransactionSplitModal
    transaction={mockTransaction}
    isOpen={true}
    onClose={action('close')}
    onSave={action('save')}
  />
);

export const PreTeenVersion = () => (
  <PersonaContext.Provider value={{ currentPersona: 'pre_teen' }}>
    <TransactionSplitModal
      transaction={mockTransaction}
      isOpen={true}
      onClose={action('close')}
      onSave={action('save')}
    />
  </PersonaContext.Provider>
);
```

This component architecture provides a robust foundation for building a scalable, maintainable, and user-friendly application that serves each persona's unique needs while maintaining consistency and code reusability.