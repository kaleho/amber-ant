import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  DollarSign, 
  TrendingUp, 
  Target, 
  Heart, 
  CreditCard,
  PiggyBank,
  AlertTriangle,
  Plus
} from 'lucide-react';

export const SingleAdultDashboard: React.FC = () => {
  // Mock data for demonstration
  const mockData = {
    totalBalance: 15750.32,
    monthlyIncome: 5200.00,
    monthlyExpenses: 3850.50,
    emergencyFund: 12500.00,
    emergencyFundGoal: 15600.00,
    tithingThisMonth: 520.00,
    tithingYTD: 5200.00,
    budgetUtilization: 74
  };

  const quickActions = [
    { icon: Plus, label: 'Add Transaction', href: '/transactions/new' },
    { icon: PiggyBank, label: 'Update Budget', href: '/budgets' },
    { icon: Target, label: 'Set New Goal', href: '/goals/new' },
    { icon: Heart, label: 'Record Tithing', href: '/tithing/new' },
  ];

  const recentTransactions = [
    { date: '2024-01-15', description: 'Grocery Store', amount: -87.32, category: 'Food' },
    { date: '2024-01-14', description: 'Salary Deposit', amount: 2600.00, category: 'Income' },
    { date: '2024-01-13', description: 'Gas Station', amount: -45.20, category: 'Transportation' },
    { date: '2024-01-12', description: 'Electric Bill', amount: -120.50, category: 'Utilities' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Financial Dashboard</h1>
          <p className="text-muted-foreground">
            Welcome back! Here's your financial overview for January 2024.
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">Single Adult</Badge>
          <Badge variant="secondary">Professional</Badge>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Balance</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${mockData.totalBalance.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+2.5%</span> from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Income</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${mockData.monthlyIncome.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              After taxes and deductions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Emergency Fund</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${mockData.emergencyFund.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              {((mockData.emergencyFund / mockData.emergencyFundGoal) * 100).toFixed(0)}% of goal
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tithing YTD</CardTitle>
            <Heart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${mockData.tithingYTD.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              10% of gross income
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common tasks for busy professionals</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Button
                  key={action.label}
                  variant="outline"
                  className="justify-start h-auto p-3"
                  onClick={() => window.location.href = action.href}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {action.label}
                </Button>
              );
            })}
          </CardContent>
        </Card>

        {/* Budget Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Budget</CardTitle>
            <CardDescription>January 2024 spending</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm">Budget Utilization</span>
                <span className="text-sm font-medium">{mockData.budgetUtilization}%</span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${mockData.budgetUtilization}%` }}
                />
              </div>
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>Spent: ${mockData.monthlyExpenses.toFixed(2)}</span>
                <span>Budget: ${mockData.monthlyIncome.toFixed(2)}</span>
              </div>
              {mockData.budgetUtilization > 80 && (
                <div className="flex items-center gap-2 text-sm text-yellow-600">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Approaching budget limit</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Transactions</CardTitle>
            <CardDescription>Last 4 transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentTransactions.map((transaction, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{transaction.description}</span>
                    <span className="text-xs text-muted-foreground">{transaction.date}</span>
                  </div>
                  <div className="flex flex-col items-end">
                    <span className={`text-sm font-medium ${
                      transaction.amount > 0 ? 'text-green-600' : 'text-foreground'
                    }`}>
                      {transaction.amount > 0 ? '+' : ''}${Math.abs(transaction.amount).toFixed(2)}
                    </span>
                    <span className="text-xs text-muted-foreground">{transaction.category}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Goals Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Financial Goals Progress</CardTitle>
          <CardDescription>Track your progress toward financial milestones</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">Emergency Fund</span>
                <span className="text-sm text-muted-foreground">
                  ${mockData.emergencyFund.toFixed(2)} / ${mockData.emergencyFundGoal.toFixed(2)}
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div 
                  className="bg-green-500 h-2 rounded-full transition-all duration-300" 
                  style={{ width: `${(mockData.emergencyFund / mockData.emergencyFundGoal) * 100}%` }}
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">House Down Payment</span>
                <span className="text-sm text-muted-foreground">
                  $8,500 / $25,000
                </span>
              </div>
              <div className="w-full bg-secondary rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300" 
                  style={{ width: '34%' }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};