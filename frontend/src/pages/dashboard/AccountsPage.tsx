/**
 * Accounts Page - Complete Biblical Stewardship Account Management
 * Comprehensive account management with biblical financial wisdom
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Plus,
  CreditCard, 
  Building, 
  PiggyBank, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  RefreshCw,
  Link,
  Unlink,
  DollarSign,
  Calendar,
  Shield,
  BookOpen,
  Heart,
  Star,
  Activity,
  Wallet,
  Home,
  Car,
  GraduationCap,
  Users,
  Edit,
  Trash2,
  Info
} from 'lucide-react';
import { usePersona } from '@/contexts/PersonaContext';
import { useBudget } from '@/contexts/BudgetContext';
import { ThemeToggle } from '@/components/ui/theme-toggle';

interface Account {
  id: string;
  name: string;
  type: 'checking' | 'savings' | 'credit_card' | 'investment' | 'retirement' | 'loan' | 'mortgage';
  institution: string;
  balance: number;
  available?: number;
  lastUpdated: string;
  isConnected: boolean;
  accountNumber: string;
  interestRate?: number;
  creditLimit?: number;
  minimumPayment?: number;
  dueDate?: string;
  biblicalPurpose?: string;
  stewardshipGoal?: string;
}

export const AccountsPage: React.FC = () => {
  const { currentPersona } = usePersona();
  const { budgets } = useBudget();

  const [showBalances, setShowBalances] = useState(true);
  const [isAddingAccount, setIsAddingAccount] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  // Sample accounts data - in real app this would come from context/API
  const [accounts, setAccounts] = useState<Account[]>([
    {
      id: '1',
      name: 'Primary Checking',
      type: 'checking',
      institution: 'Christian Community Bank',
      balance: 3250.45,
      available: 3250.45,
      lastUpdated: '2024-08-01T08:30:00Z',
      isConnected: true,
      accountNumber: '****1234',
      biblicalPurpose: 'Daily stewardship and faithful money management',
      stewardshipGoal: 'Maintain 2-3 months of expenses for wise financial planning'
    },
    {
      id: '2',
      name: 'Emergency Savings',
      type: 'savings',
      institution: 'Faith First Savings',
      balance: 12500.00,
      lastUpdated: '2024-08-01T08:30:00Z',
      isConnected: true,
      accountNumber: '****5678',
      interestRate: 2.5,
      biblicalPurpose: 'Emergency fund for unexpected needs',
      stewardshipGoal: 'Build to 6 months of expenses as biblical wisdom teaches'
    },
    {
      id: '3',
      name: 'Tithing & Giving',
      type: 'savings',
      institution: 'Kingdom Builders Credit Union',
      balance: 1200.00,
      lastUpdated: '2024-08-01T08:30:00Z',
      isConnected: true,
      accountNumber: '****9101',
      interestRate: 1.8,
      biblicalPurpose: 'Dedicated account for tithes and charitable giving',
      stewardshipGoal: 'Set aside 10% of income for faithful giving'
    },
    {
      id: '4',
      name: 'Stewardship Credit Card',
      type: 'credit_card',
      institution: 'Faithful Finances Credit',
      balance: -850.25,
      available: 4149.75,
      lastUpdated: '2024-08-01T08:30:00Z',
      isConnected: true,
      accountNumber: '****2468',
      creditLimit: 5000,
      minimumPayment: 35.00,
      dueDate: '2024-08-15',
      biblicalPurpose: 'Emergency expenses and building credit responsibly',
      stewardshipGoal: 'Pay in full each month, avoid debt accumulation'
    },
    {
      id: '5',
      name: 'Retirement - 401k',
      type: 'retirement',
      institution: 'Christian Investment Services',
      balance: 45600.00,
      lastUpdated: '2024-07-31T17:00:00Z',
      isConnected: true,
      accountNumber: '****7890',
      biblicalPurpose: 'Long-term stewardship and retirement planning',
      stewardshipGoal: 'Faithful saving for future needs and continued giving ability'
    },
    {
      id: '6',
      name: 'Home Mortgage',
      type: 'mortgage',
      institution: 'Cornerstone Home Loans',
      balance: -185000.00,
      lastUpdated: '2024-08-01T08:30:00Z',
      isConnected: true,
      accountNumber: '****3456',
      minimumPayment: 1250.00,
      dueDate: '2024-08-01',
      biblicalPurpose: 'Shelter for family - a fundamental need',
      stewardshipGoal: 'Pay consistently, consider extra principal payments when possible'
    }
  ]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(Math.abs(amount));
  };

  const getAccountIcon = (type: Account['type']) => {
    switch (type) {
      case 'checking': return <Building className="h-5 w-5 text-blue-600" />;
      case 'savings': return <PiggyBank className="h-5 w-5 text-green-600" />;
      case 'credit_card': return <CreditCard className="h-5 w-5 text-purple-600" />;
      case 'investment': return <TrendingUp className="h-5 w-5 text-orange-600" />;
      case 'retirement': return <Shield className="h-5 w-5 text-indigo-600" />;
      case 'loan': return <DollarSign className="h-5 w-5 text-red-600" />;
      case 'mortgage': return <Home className="h-5 w-5 text-amber-600" />;
      default: return <Wallet className="h-5 w-5 text-gray-600" />;
    }
  };

  const getAccountTypeLabel = (type: Account['type']) => {
    const labels = {
      checking: 'Checking Account',
      savings: 'Savings Account',
      credit_card: 'Credit Card',
      investment: 'Investment Account',
      retirement: 'Retirement Account',
      loan: 'Loan',
      mortgage: 'Mortgage'
    };
    return labels[type] || type;
  };

  const getBalanceColor = (account: Account) => {
    if (account.type === 'credit_card' || account.type === 'loan' || account.type === 'mortgage') {
      return account.balance < 0 ? 'text-red-600' : 'text-green-600';
    }
    return account.balance > 0 ? 'text-green-600' : 'text-red-600';
  };

  const totalAssets = accounts
    .filter(acc => ['checking', 'savings', 'investment', 'retirement'].includes(acc.type))
    .reduce((sum, acc) => sum + acc.balance, 0);

  const totalLiabilities = accounts
    .filter(acc => ['credit_card', 'loan', 'mortgage'].includes(acc.type))
    .reduce((sum, acc) => sum + Math.abs(acc.balance), 0);

  const netWorth = totalAssets - totalLiabilities;

  const connectedAccounts = accounts.filter(acc => acc.isConnected).length;
  const totalAccounts = accounts.length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Financial Accounts</h1>
          <p className="text-muted-foreground">
            "The plans of the diligent lead to profit as surely as haste leads to poverty." - Proverbs 21:5
          </p>
        </div>
        <div className="flex gap-2">
          <ThemeToggle />
          <Button
            variant="outline"
            onClick={() => setShowBalances(!showBalances)}
            className="flex items-center gap-2"
          >
            {showBalances ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            {showBalances ? 'Hide Balances' : 'Show Balances'}
          </Button>
          <Button 
            onClick={() => setIsAddingAccount(true)}
            className="flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Account
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Assets</p>
                <p className="text-2xl font-bold text-green-600">
                  {showBalances ? formatCurrency(totalAssets) : '••••••'}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Liabilities</p>
                <p className="text-2xl font-bold text-red-600">
                  {showBalances ? formatCurrency(totalLiabilities) : '••••••'}
                </p>
              </div>
              <CreditCard className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Net Worth</p>
                <p className={`text-2xl font-bold ${netWorth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {showBalances ? formatCurrency(netWorth) : '••••••'}
                </p>
              </div>
              <Shield className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Connected Accounts</p>
                <p className="text-2xl font-bold">{connectedAccounts}/{totalAccounts}</p>
              </div>
              <Link className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="accounts" className="space-y-6">
        <TabsList>
          <TabsTrigger value="accounts">
            <Wallet className="mr-2 h-4 w-4" />
            All Accounts ({accounts.length})
          </TabsTrigger>
          <TabsTrigger value="assets">
            <TrendingUp className="mr-2 h-4 w-4" />
            Assets
          </TabsTrigger>
          <TabsTrigger value="liabilities">
            <CreditCard className="mr-2 h-4 w-4" />
            Liabilities
          </TabsTrigger>
          <TabsTrigger value="stewardship">
            <BookOpen className="mr-2 h-4 w-4" />
            Biblical Stewardship
          </TabsTrigger>
        </TabsList>

        {/* All Accounts Tab */}
        <TabsContent value="accounts" className="space-y-4">
          {accounts.map((account) => (
            <Card key={account.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    {getAccountIcon(account.type)}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{account.name}</h3>
                        {account.isConnected ? (
                          <Badge variant="default" className="text-xs">
                            <CheckCircle className="mr-1 h-3 w-3" />
                            Connected
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-xs">
                            <AlertTriangle className="mr-1 h-3 w-3" />
                            Disconnected
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{account.institution}</p>
                      <p className="text-xs text-muted-foreground">{getAccountTypeLabel(account.type)} • {account.accountNumber}</p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className={`text-xl font-bold ${getBalanceColor(account)}`}>
                      {showBalances ? (
                        <>
                          {account.balance < 0 && account.type !== 'credit_card' && account.type !== 'loan' && account.type !== 'mortgage' ? '-' : ''}
                          {formatCurrency(account.balance)}
                        </>
                      ) : '••••••'}
                    </p>
                    {account.available && account.available !== account.balance && (
                      <p className="text-sm text-muted-foreground">
                        Available: {showBalances ? formatCurrency(account.available) : '••••••'}
                      </p>
                    )}
                    {account.creditLimit && (
                      <p className="text-sm text-muted-foreground">
                        Limit: {showBalances ? formatCurrency(account.creditLimit) : '••••••'}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Updated: {new Date(account.lastUpdated).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {account.minimumPayment && account.dueDate && (
                  <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-amber-600" />
                        <span className="text-sm font-medium">Payment Due</span>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">
                          {showBalances ? formatCurrency(account.minimumPayment) : '••••••'}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          Due: {new Date(account.dueDate).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {account.biblicalPurpose && (
                  <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Heart className="h-4 w-4 text-blue-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-blue-800">Biblical Purpose</p>
                        <p className="text-sm text-blue-700">{account.biblicalPurpose}</p>
                        {account.stewardshipGoal && (
                          <p className="text-xs text-blue-600 mt-1">Goal: {account.stewardshipGoal}</p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex justify-end gap-2 mt-4">
                  <Button variant="ghost" size="sm">
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Refresh
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Edit className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button variant="ghost" size="sm">
                    <Activity className="h-4 w-4 mr-1" />
                    Transactions
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Assets Tab */}
        <TabsContent value="assets" className="space-y-4">
          {accounts.filter(acc => ['checking', 'savings', 'investment', 'retirement'].includes(acc.type)).map((account) => (
            <Card key={account.id}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getAccountIcon(account.type)}
                    <div>
                      <h3 className="font-semibold">{account.name}</h3>
                      <p className="text-sm text-muted-foreground">{account.institution}</p>
                      {account.interestRate && (
                        <p className="text-xs text-green-600">APY: {account.interestRate}%</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-green-600">
                      {showBalances ? formatCurrency(account.balance) : '••••••'}
                    </p>
                    <p className="text-xs text-muted-foreground">{getAccountTypeLabel(account.type)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
          
          <Card>
            <CardHeader>
              <CardTitle>Asset Summary</CardTitle>
              <CardDescription>Your faithful stewardship asset overview</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <p className="text-3xl font-bold text-green-600 mb-2">
                  {showBalances ? formatCurrency(totalAssets) : '••••••'}
                </p>
                <p className="text-muted-foreground">Total Assets</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Liabilities Tab */}
        <TabsContent value="liabilities" className="space-y-4">
          {accounts.filter(acc => ['credit_card', 'loan', 'mortgage'].includes(acc.type)).map((account) => (
            <Card key={account.id}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getAccountIcon(account.type)}
                    <div>
                      <h3 className="font-semibold">{account.name}</h3>
                      <p className="text-sm text-muted-foreground">{account.institution}</p>
                      {account.minimumPayment && (
                        <p className="text-xs text-amber-600">
                          Min Payment: {showBalances ? formatCurrency(account.minimumPayment) : '••••••'}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold text-red-600">
                      {showBalances ? formatCurrency(Math.abs(account.balance)) : '••••••'}
                    </p>
                    <p className="text-xs text-muted-foreground">{getAccountTypeLabel(account.type)}</p>
                    {account.dueDate && (
                      <p className="text-xs text-amber-600">
                        Due: {new Date(account.dueDate).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          <Card>
            <CardHeader>
              <CardTitle>Liability Summary</CardTitle>
              <CardDescription>Debt stewardship and payment obligations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <p className="text-3xl font-bold text-red-600 mb-2">
                  {showBalances ? formatCurrency(totalLiabilities) : '••••••'}
                </p>
                <p className="text-muted-foreground">Total Liabilities</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Biblical Stewardship Tab */}
        <TabsContent value="stewardship" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Biblical Account Wisdom</CardTitle>
                <CardDescription>Scripture-based guidance for account management</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 border-l-4 border-green-500 bg-green-50">
                  <p className="text-sm italic mb-2">
                    "The plans of the diligent lead to profit as surely as haste leads to poverty."
                  </p>
                  <p className="text-xs text-muted-foreground">Proverbs 21:5</p>
                </div>
                <div className="p-4 border-l-4 border-blue-500 bg-blue-50">
                  <p className="text-sm italic mb-2">
                    "Be sure you know the condition of your flocks, give careful attention to your herds."
                  </p>
                  <p className="text-xs text-muted-foreground">Proverbs 27:23</p>
                </div>
                <div className="p-4 border-l-4 border-purple-500 bg-purple-50">
                  <p className="text-sm italic mb-2">
                    "The wise store up choice food and olive oil, but fools gulp theirs down."
                  </p>
                  <p className="text-xs text-muted-foreground">Proverbs 21:20</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Stewardship Account Types</CardTitle>
                <CardDescription>Biblical purposes for different accounts</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-green-50">
                  <PiggyBank className="h-5 w-5 text-green-600" />
                  <div>
                    <h4 className="font-medium">Emergency Savings</h4>
                    <p className="text-sm text-muted-foreground">Prepare for unexpected needs</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-purple-50">
                  <Heart className="h-5 w-5 text-purple-600" />
                  <div>
                    <h4 className="font-medium">Tithing & Giving</h4>
                    <p className="text-sm text-muted-foreground">Dedicated funds for faithful giving</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-50">
                  <Building className="h-5 w-5 text-blue-600" />
                  <div>
                    <h4 className="font-medium">Daily Operations</h4>
                    <p className="text-sm text-muted-foreground">Checking for regular expenses</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-indigo-50">
                  <Shield className="h-5 w-5 text-indigo-600" />
                  <div>
                    <h4 className="font-medium">Future Planning</h4>
                    <p className="text-sm text-muted-foreground">Retirement and long-term goals</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Stewardship Account Health</CardTitle>
              <CardDescription>Biblical financial health indicators</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center p-4 border rounded-lg">
                  <Star className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
                  <h4 className="font-medium">Debt-to-Asset Ratio</h4>
                  <p className="text-2xl font-bold text-blue-600">
                    {totalAssets > 0 ? ((totalLiabilities / totalAssets) * 100).toFixed(1) : 0}%
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {(totalLiabilities / totalAssets) < 0.3 ? 'Excellent stewardship!' : 'Room for improvement'}
                  </p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <Shield className="h-8 w-8 text-green-600 mx-auto mb-2" />
                  <h4 className="font-medium">Emergency Fund</h4>
                  <p className="text-2xl font-bold text-green-600">
                    {formatCurrency(accounts.find(acc => acc.name.includes('Emergency'))?.balance || 0)}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Financial security foundation
                  </p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <Heart className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                  <h4 className="font-medium">Giving Fund</h4>
                  <p className="text-2xl font-bold text-purple-600">
                    {formatCurrency(accounts.find(acc => acc.name.includes('Tithing'))?.balance || 0)}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Faithful generosity ready
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};