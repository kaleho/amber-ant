/**
 * College Student Dashboard - Budget-focused financial management for irregular income
 * Features: Semester budgeting, textbook tracking, financial aid management, flexible tithing
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Wallet, 
  TrendingUp, 
  AlertTriangle, 
  BookOpen, 
  Heart, 
  GraduationCap,
  DollarSign,
  Coffee,
  ShoppingCart,
  Calendar,
  PiggyBank,
  CreditCard
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { TransactionCard } from '@/components/financial/TransactionCard';
import { BudgetCard } from '@/components/financial/BudgetCard';
import { EmergencyFundCard } from '@/components/financial/EmergencyFundCard';

export const CollegeStudentDashboard: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  // Mock data queries - replace with real API calls
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: () => apiClient.getProfile(),
  });

  const { data: transactions } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => apiClient.getTransactions({ limit: 10 }),
  });

  const { data: budgets } = useQuery({
    queryKey: ['budgets'],
    queryFn: () => apiClient.getBudgets(),
  });

  const { data: goals } = useQuery({
    queryKey: ['savings-goals'],
    queryFn: () => apiClient.getSavingsGoals(),
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => apiClient.getAccounts(),
  });

  // College-specific dashboard stats
  const dashboardStats = {
    totalBalance: accounts?.reduce((sum, acc) => sum + acc.balance, 0) || 432,
    monthlyIncome: 850, // Part-time job + financial aid distributed monthly
    monthlyExpenses: 780,
    emergencyFundProgress: 15,
    budgetProgress: 92, // Close to budget limit - typical for college students
    tithingPercentage: 8,
    savingsRate: 8
  };

  // Budget breakdown for college-specific categories
  const collegeBudgetCategories = [
    {
      name: "Tuition & Fees",
      budgeted: 800,
      spent: 800,
      percentage: 100,
      color: "bg-red-500",
      icon: GraduationCap
    },
    {
      name: "Textbooks",
      budgeted: 150,
      spent: 127,
      percentage: 85,
      color: "bg-blue-500",
      icon: BookOpen
    },
    {
      name: "Food & Dining",
      budgeted: 200,
      spent: 183,
      percentage: 92,
      color: "bg-orange-500",
      icon: Coffee
    },
    {
      name: "Transportation",
      budgeted: 80,
      spent: 65,
      percentage: 81,
      color: "bg-green-500",
      icon: ShoppingCart
    }
  ];

  // Financial aid tracking
  const financialAid = [
    {
      source: "Federal Pell Grant",
      amount: 3200,
      disbursed: 1600,
      remaining: 1600,
      nextDisbursement: "January 2025"
    },
    {
      source: "State Grant",
      amount: 1800,
      disbursed: 900,
      remaining: 900,
      nextDisbursement: "January 2025"
    },
    {
      source: "Work Study",
      amount: 2000,
      earned: 450,
      remaining: 1550,
      nextDisbursement: "Bi-weekly"
    }
  ];

  // Ramen mode calculator
  const ramenModeActive = dashboardStats.budgetProgress > 90;
  const daysUntilPayday = 12;
  const remainingBudget = dashboardStats.monthlyIncome - (dashboardStats.monthlyExpenses * (dashboardStats.budgetProgress / 100));

  return (
    <div className="container mx-auto p-6 space-y-6 bg-gradient-to-br from-purple-50 to-pink-50 min-h-screen">
      {/* College-specific Header */}
      <div className="flex items-center justify-between bg-white rounded-lg p-6 border-2 border-purple-300 shadow-md">
        <div>
          <h1 className="text-3xl font-bold text-purple-800">
            Hey {profile?.display_name || 'Student'}! 📚
          </h1>
          <p className="text-purple-600 mt-1">
            Mastering money while mastering your degree!
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Badge className="bg-purple-100 text-purple-800 border-purple-200 text-lg px-4 py-2">
            College Student
          </Badge>
          <div className="text-right">
            <p className="text-sm text-gray-600">Available Balance</p>
            <p className="text-2xl font-bold text-purple-800">
              ${dashboardStats.totalBalance.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Ramen Mode Alert */}
      {ramenModeActive && (
        <Alert className="border-yellow-300 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            <span className="font-bold">Ramen Mode Activated!</span> You've used {dashboardStats.budgetProgress}% of your budget. 
            ${remainingBudget.toFixed(2)} left for {daysUntilPayday} days. Time for creative meal planning! 🍜
          </AlertDescription>
        </Alert>
      )}

      {/* Dashboard Statistics */}
      <DashboardStats 
        persona="college_student" 
        stats={dashboardStats}
        className="mb-6" 
      />

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6 bg-white border-2 border-purple-200">
          <TabsTrigger value="overview" className="data-[state=active]:bg-purple-100">
            <Wallet className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="budget" className="data-[state=active]:bg-purple-100">
            <PiggyBank className="h-4 w-4 mr-2" />
            Budget
          </TabsTrigger>
          <TabsTrigger value="financial-aid" className="data-[state=active]:bg-purple-100">
            <GraduationCap className="h-4 w-4 mr-2" />
            Aid
          </TabsTrigger>
          <TabsTrigger value="transactions" className="data-[state=active]:bg-purple-100">
            <CreditCard className="h-4 w-4 mr-2" />
            Spending
          </TabsTrigger>
          <TabsTrigger value="goals" className="data-[state=active]:bg-purple-100">
            <DollarSign className="h-4 w-4 mr-2" />
            Goals
          </TabsTrigger>
          <TabsTrigger value="giving" className="data-[state=active]:bg-purple-100">
            <Heart className="h-4 w-4 mr-2" />
            Giving
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Monthly Budget Overview */}
            <Card className="border-2 border-purple-200 bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-purple-800">
                  <PiggyBank className="h-5 w-5" />
                  Monthly Budget Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Budget Used</span>
                    <span className={`font-bold ${dashboardStats.budgetProgress > 90 ? 'text-red-600' : 'text-purple-600'}`}>
                      {dashboardStats.budgetProgress}%
                    </span>
                  </div>
                  <Progress 
                    value={dashboardStats.budgetProgress} 
                    className="h-2"
                    indicatorClassName={dashboardStats.budgetProgress > 90 ? 'bg-red-500' : 'bg-purple-500'}
                  />
                  <div className="flex justify-between text-xs text-gray-600">
                    <span>Spent: ${(dashboardStats.monthlyExpenses * (dashboardStats.budgetProgress / 100)).toFixed(0)}</span>
                    <span>Budget: ${dashboardStats.monthlyIncome}</span>
                  </div>
                </div>
                
                <div className="pt-4 border-t">
                  <h4 className="font-medium text-purple-800 mb-3">Quick Actions</h4>
                  <div className="space-y-2">
                    <Button variant="outline" className="w-full justify-start">
                      <Coffee className="h-4 w-4 mr-2" />
                      Log Coffee Purchase
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                      <BookOpen className="h-4 w-4 mr-2" />
                      Add Textbook Expense
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Transactions */}
            <Card className="border-2 border-purple-200 bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-purple-800">
                  <TrendingUp className="h-5 w-5" />
                  Recent Spending
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {transactions?.slice(0, 4).map((transaction) => (
                  <TransactionCard
                    key={transaction.id}
                    transaction={transaction}
                    persona="college_student"
                    showSplitButton={false}
                    showCategory={true}
                  />
                ))}
                <Button variant="outline" className="w-full border-purple-200 text-purple-700">
                  View All Transactions
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Budget Tab */}
        <TabsContent value="budget" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Budget Categories */}
            <Card className="border-2 border-purple-200 bg-white">
              <CardHeader>
                <CardTitle className="text-purple-800">Semester Budget Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {collegeBudgetCategories.map((category, index) => {
                  const Icon = category.icon;
                  return (
                    <div key={index} className="p-4 border border-purple-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Icon className="h-5 w-5 text-purple-600" />
                          <span className="font-medium">{category.name}</span>
                        </div>
                        <span className="text-sm font-bold">
                          ${category.spent} / ${category.budgeted}
                        </span>
                      </div>
                      <Progress 
                        value={category.percentage} 
                        className="h-2"
                        indicatorClassName={category.percentage > 90 ? 'bg-red-500' : category.color}
                      />
                      <div className="flex justify-between text-xs text-gray-600 mt-1">
                        <span>{category.percentage}% used</span>
                        <span>${category.budgeted - category.spent} remaining</span>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Survival Mode Calculator */}
            <Card className="border-2 border-orange-200 bg-orange-50">
              <CardHeader>
                <CardTitle className="text-orange-800">Survival Calculator</CardTitle>
                <p className="text-orange-600 text-sm">Making your money last until next payday</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-white rounded-lg">
                    <p className="text-2xl font-bold text-orange-800">{daysUntilPayday}</p>
                    <p className="text-xs text-orange-600">Days Left</p>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <p className="text-2xl font-bold text-orange-800">${(remainingBudget / daysUntilPayday).toFixed(2)}</p>
                    <p className="text-xs text-orange-600">Per Day</p>
                  </div>
                </div>
                
                <div className="p-3 bg-white rounded-lg">
                  <h4 className="font-bold text-orange-800 mb-2">🍜 Ramen Mode Tips</h4>
                  <ul className="text-sm text-orange-700 space-y-1">
                    <li>• Cook at home: Save $10-15/day vs eating out</li>
                    <li>• Free campus events for entertainment</li>
                    <li>• Library instead of coffee shops</li>
                    <li>• Walk/bike instead of rideshare</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Financial Aid Tab */}
        <TabsContent value="financial-aid" className="space-y-6">
          <Card className="border-2 border-blue-200 bg-white">
            <CardHeader>
              <CardTitle className="text-blue-800">Financial Aid Tracking</CardTitle>
              <p className="text-blue-600 text-sm">Monitor your aid disbursements and work study earnings</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {financialAid.map((aid, index) => (
                <div key={index} className="p-4 border border-blue-200 rounded-lg">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-bold text-blue-800">{aid.source}</h4>
                      <p className="text-sm text-blue-600">Next: {aid.nextDisbursement}</p>
                    </div>
                    <Badge className="bg-blue-100 text-blue-800">
                      ${aid.remaining.toLocaleString()} left
                    </Badge>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Received: ${aid.disbursed.toLocaleString()}</span>
                      <span>Total: ${aid.amount.toLocaleString()}</span>
                    </div>
                    <Progress 
                      value={(aid.disbursed / aid.amount) * 100} 
                      className="h-2"
                      indicatorClassName="bg-blue-500"
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-6">
          <Card className="border-2 border-purple-200 bg-white">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-purple-800">All Transactions</CardTitle>
                <Badge className="bg-purple-100 text-purple-800">
                  This Month: ${(dashboardStats.monthlyExpenses * (dashboardStats.budgetProgress / 100)).toFixed(0)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {transactions?.map((transaction) => (
                <TransactionCard
                  key={transaction.id}
                  transaction={transaction}
                  persona="college_student"
                  showCategory={true}
                  showSplitButton={true}
                />
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Goals Tab */}
        <TabsContent value="goals" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {goals?.map((goal) => (
              <EmergencyFundCard
                key={goal.id}
                goal={goal}
                persona="college_student"
                onAddFunds={() => toast({
                  title: "Add Funds",
                  description: "Every dollar counts in college! Great job saving!",
                })}
              />
            ))}
          </div>

          {/* College-specific savings tips */}
          <Card className="border-2 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-800">College Savings Strategy</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-white rounded-lg border border-green-200">
                  <h4 className="font-bold text-green-800">Post-Graduation Fund</h4>
                  <p className="text-sm text-green-600">Save for job search & moving expenses</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="text-xs">Target: $2,000</Badge>
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border border-green-200">
                  <h4 className="font-bold text-green-800">Textbook Buffer</h4>
                  <p className="text-sm text-green-600">Avoid last-minute expensive purchases</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="text-xs">Target: $500</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Giving Tab */}
        <TabsContent value="giving" className="space-y-6">
          <Card className="border-2 border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="text-red-800">Flexible Giving</CardTitle>
              <p className="text-red-600">Give from your heart, even with limited income</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-white rounded-lg border border-red-200">
                  <h4 className="font-bold text-red-800 mb-2">This Month's Giving</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Regular Giving</span>
                      <span className="font-bold">$25.00</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Special Offering</span>
                      <span className="font-bold">$10.00</span>
                    </div>
                    <div className="flex justify-between font-bold text-red-800 border-t pt-2">
                      <span>Total Given</span>
                      <span>$35.00</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-white rounded-lg border border-red-200">
                  <h4 className="font-bold text-red-800 mb-2">Flexible Goal</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">When I can afford</span>
                      <span className="font-bold">$40.00</span>
                    </div>
                    <Progress value={87} className="h-2" />
                    <p className="text-xs text-green-600">You're doing great with flexible giving!</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-white rounded-lg border border-red-200">
                <h4 className="font-bold text-red-800 mb-3">💝 Student Giving Wisdom</h4>
                <blockquote className="italic text-red-700 border-l-4 border-red-300 pl-4">
                  "Remember this: Whoever sows sparingly will also reap sparingly, and whoever sows generously will also reap generously."
                  <footer className="text-sm font-normal mt-1">- 2 Corinthians 9:6</footer>
                </blockquote>
                <p className="text-sm text-red-600 mt-2">
                  Even small amounts given consistently show a generous heart. God values the widow's mite!
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};