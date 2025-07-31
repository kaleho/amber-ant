/**
 * Married Couple Dashboard - Joint financial management and coordination
 * Features: Joint budgeting, shared goals, spouse coordination, combined stewardship
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  Heart, 
  Users, 
  TrendingUp, 
  Home, 
  Target,
  DollarSign,
  PiggyBank,
  Calendar,
  MessageCircle,
  CheckCircle,
  AlertCircle,
  Wallet,
  CreditCard,
  Gift,
  Baby,
  Car,
  Building,
  Sparkles
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { TransactionCard } from '@/components/financial/TransactionCard';
import { BudgetCard } from '@/components/financial/BudgetCard';
import { EmergencyFundCard } from '@/components/financial/EmergencyFundCard';

export const MarriedCoupleDashboard: React.FC = () => {
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

  // Married couple specific dashboard stats
  const dashboardStats = {
    totalBalance: accounts?.reduce((sum, acc) => sum + acc.balance, 0) || 45600,
    monthlyIncome: 8500, // Combined income
    monthlyExpenses: 6800,
    emergencyFundProgress: 68,
    budgetProgress: 80,
    tithingPercentage: 10,
    savingsRate: 20
  };

  // Joint financial goals
  const jointGoals = [
    {
      name: "House Down Payment",
      target: 60000,
      current: 42500,
      progress: 71,
      priority: "High",
      targetDate: "2025-12-31",
      contributions: { spouse1: 22500, spouse2: 20000 },
      icon: Home
    },
    {
      name: "Emergency Fund",
      target: 25000,
      current: 17000,
      progress: 68,
      priority: "Critical",
      targetDate: "2025-06-30",
      contributions: { spouse1: 8500, spouse2: 8500 },
      icon: PiggyBank
    },
    {
      name: "New Car Fund",
      target: 25000,
      current: 8200,
      progress: 33,
      priority: "Medium",
      targetDate: "2026-03-31",
      contributions: { spouse1: 4200, spouse2: 4000 },
      icon: Car
    }
  ];

  // Budget categories with spouse responsibility
  const budgetCategories = [
    {
      name: "Housing",
      budgeted: 2200,
      spent: 2200,
      responsible: "Joint",
      percentage: 100,
      color: "bg-blue-500"
    },
    {
      name: "Food & Dining",
      budgeted: 800,
      spent: 720,
      responsible: "Sarah",
      percentage: 90,
      color: "bg-green-500"
    },
    {
      name: "Transportation",
      budgeted: 600,
      spent: 580,
      responsible: "Mike",
      percentage: 97,
      color: "bg-orange-500"
    },
    {
      name: "Utilities",
      budgeted: 350,
      spent: 340,
      responsible: "Mike",
      percentage: 97,
      color: "bg-purple-500"
    },
    {
      name: "Entertainment",
      budgeted: 400,
      spent: 320,
      responsible: "Joint",
      percentage: 80,
      color: "bg-pink-500"
    },
    {
      name: "Personal Care",
      budgeted: 200,
      spent: 180,
      responsible: "Sarah",
      percentage: 90,
      color: "bg-indigo-500"
    }
  ];

  // Recent spouse activity
  const spouseActivity = [
    {
      spouse: "Sarah",
      action: "Added grocery expense",
      amount: 127.45,
      time: "2 hours ago",
      category: "Food & Dining",
      avatar: "/api/placeholder/32/32"
    },
    {
      spouse: "Mike",
      action: "Paid electricity bill",
      amount: 185.00,
      time: "Yesterday",
      category: "Utilities",
      avatar: "/api/placeholder/32/32"
    },
    {
      spouse: "Sarah",
      action: "Contributed to House Fund",
      amount: 500.00,
      time: "2 days ago",
      category: "Savings",
      avatar: "/api/placeholder/32/32"
    }
  ];

  // Upcoming joint expenses
  const upcomingExpenses = [
    {
      name: "Anniversary Dinner",
      amount: 150,
      date: "2025-02-14",
      responsible: "Mike",
      category: "Entertainment",
      icon: Heart
    },
    {
      name: "Home Insurance",
      amount: 1200,
      date: "2025-03-15",
      responsible: "Joint",
      category: "Housing",
      icon: Building
    },
    {
      name: "Car Registration",
      amount: 180,
      date: "2025-04-01",
      responsible: "Sarah",
      category: "Transportation",
      icon: Car
    }
  ];

  return (
    <div className="container mx-auto p-6 space-y-6 bg-gradient-to-br from-indigo-50 to-purple-50 min-h-screen">
      {/* Couple Header */}
      <div className="flex items-center justify-between bg-white rounded-lg p-6 border-2 border-indigo-300 shadow-md">
        <div className="flex items-center gap-4">
          <div className="flex -space-x-2">
            <Avatar className="border-2 border-white">
              <AvatarImage src="/api/placeholder/40/40" />
              <AvatarFallback>M</AvatarFallback>
            </Avatar>
            <Avatar className="border-2 border-white">
              <AvatarImage src="/api/placeholder/40/40" />
              <AvatarFallback>S</AvatarFallback>
            </Avatar>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-indigo-800">
              Building Together! 💑
            </h1>
            <p className="text-indigo-600 mt-1">
              Mike & Sarah - United in faith and finances
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200 text-lg px-4 py-2">
            Married Couple
          </Badge>
          <div className="text-right">
            <p className="text-sm text-gray-600">Combined Net Worth</p>
            <p className="text-2xl font-bold text-indigo-800">
              ${dashboardStats.totalBalance.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Dashboard Statistics */}
      <DashboardStats 
        persona="married_couple" 
        stats={dashboardStats}
        className="mb-6" 
      />

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6 bg-white border-2 border-indigo-200">
          <TabsTrigger value="overview" className="data-[state=active]:bg-indigo-100">
            <Home className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="goals" className="data-[state=active]:bg-indigo-100">
            <Target className="h-4 w-4 mr-2" />
            Joint Goals
          </TabsTrigger>
          <TabsTrigger value="budget" className="data-[state=active]:bg-indigo-100">
            <Wallet className="h-4 w-4 mr-2" />
            Budget
          </TabsTrigger>
          <TabsTrigger value="activity" className="data-[state=active]:bg-indigo-100">
            <Users className="h-4 w-4 mr-2" />
            Activity
          </TabsTrigger>
          <TabsTrigger value="planning" className="data-[state=active]:bg-indigo-100">
            <Calendar className="h-4 w-4 mr-2" />
            Planning
          </TabsTrigger>
          <TabsTrigger value="giving" className="data-[state=active]:bg-indigo-100">
            <Heart className="h-4 w-4 mr-2" />
            Giving
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Joint Progress Summary */}
            <Card className="border-2 border-indigo-200 bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-indigo-800">
                  <TrendingUp className="h-5 w-5" />
                  This Month's Progress
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="text-2xl font-bold text-green-800">$1,700</div>
                    <div className="text-sm text-green-600">Savings This Month</div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="text-2xl font-bold text-blue-800">$850</div>
                    <div className="text-sm text-blue-600">Tithing & Giving</div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Monthly Savings Goal</span>
                    <span className="font-bold">85%</span>
                  </div>
                  <Progress value={85} className="h-2" indicatorClassName="bg-green-500" />
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="border-2 border-indigo-200 bg-white">
              <CardHeader>
                <CardTitle className="text-indigo-800">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <DollarSign className="h-4 w-4 mr-2" />
                  Add Joint Expense
                </Button>
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  <Target className="h-4 w-4 mr-2" />
                  Contribute to Goal
                </Button>
                <Button className="w-full bg-purple-600 hover:bg-purple-700">
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Send Spouse Note
                </Button>
                <Button variant="outline" className="w-full border-indigo-200 text-indigo-700">
                  <Calendar className="h-4 w-4 mr-2" />
                  Plan Budget Meeting
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Recent Joint Activity */}
          <Card className="border-2 border-indigo-200 bg-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-indigo-800">
                <Users className="h-5 w-5" />
                Recent Joint Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {spouseActivity.map((activity, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-indigo-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={activity.avatar} />
                      <AvatarFallback>{activity.spouse[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium text-indigo-800">
                        <span className="font-bold">{activity.spouse}</span> {activity.action}
                      </p>
                      <p className="text-sm text-indigo-600">{activity.time} • {activity.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-indigo-800">
                      ${activity.amount.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Joint Goals Tab */}
        <TabsContent value="goals" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {jointGoals.map((goal, index) => {
              const Icon = goal.icon;
              return (
                <Card key={index} className="border-2 border-indigo-200 bg-white">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Icon className="h-6 w-6 text-indigo-600" />
                        <div>
                          <CardTitle className="text-indigo-800">{goal.name}</CardTitle>
                          <p className="text-sm text-indigo-600">
                            Target: {new Date(goal.targetDate).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <Badge 
                        className={`${
                          goal.priority === 'Critical' ? 'bg-red-100 text-red-800' :
                          goal.priority === 'High' ? 'bg-orange-100 text-orange-800' :
                          'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {goal.priority}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="font-medium">Progress</span>
                        <span className="font-bold text-indigo-800">{goal.progress}%</span>
                      </div>
                      <Progress value={goal.progress} className="h-3" indicatorClassName="bg-indigo-500" />
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>${goal.current.toLocaleString()} saved</span>
                        <span>${goal.target.toLocaleString()} goal</span>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-blue-50 rounded-lg text-center">
                        <div className="font-bold text-blue-800">
                          ${goal.contributions.spouse1.toLocaleString()}
                        </div>
                        <div className="text-xs text-blue-600">Mike's Share</div>
                      </div>
                      <div className="p-3 bg-pink-50 rounded-lg text-center">
                        <div className="font-bold text-pink-800">
                          ${goal.contributions.spouse2.toLocaleString()}
                        </div>
                        <div className="text-xs text-pink-600">Sarah's Share</div>
                      </div>
                    </div>
                    
                    <Button className="w-full bg-indigo-600 hover:bg-indigo-700">
                      <DollarSign className="h-4 w-4 mr-2" />
                      Contribute to {goal.name}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Budget Tab */}
        <TabsContent value="budget" className="space-y-6">
          <Card className="border-2 border-indigo-200 bg-white">
            <CardHeader>
              <CardTitle className="text-indigo-800">Joint Budget Management</CardTitle>
              <p className="text-indigo-600 text-sm">Coordinated spending with shared responsibility</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {budgetCategories.map((category, index) => (
                <div key={index} className="p-4 border border-indigo-200 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-bold text-indigo-800">{category.name}</h4>
                      <p className="text-sm text-indigo-600">Managed by: {category.responsible}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">${category.spent} / ${category.budgeted}</p>
                      <Badge 
                        className={`${
                          category.percentage > 95 ? 'bg-red-100 text-red-800' :
                          category.percentage > 80 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}
                      >
                        {category.percentage}% Used
                      </Badge>
                    </div>
                  </div>
                  
                  <Progress 
                    value={category.percentage} 
                    className="h-3"
                    indicatorClassName={category.percentage > 95 ? 'bg-red-500' : category.color}
                  />
                  
                  <div className="flex justify-between text-sm text-gray-600 mt-2">
                    <span>${category.budgeted - category.spent} remaining</span>
                    <span>{category.responsible === 'Joint' ? '👫' : category.responsible === 'Mike' ? '👨' : '👩'}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Spouse Coordination */}
            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-800 flex items-center gap-2">
                  <MessageCircle className="h-5 w-5" />
                  Spouse Communication
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-white rounded-lg border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Avatar className="h-6 w-6">
                      <AvatarFallback>S</AvatarFallback>
                    </Avatar>
                    <span className="font-bold text-blue-800">Sarah</span>
                    <span className="text-xs text-gray-500">2 hours ago</span>
                  </div>
                  <p className="text-sm text-blue-700">
                    "Groceries were $30 over budget this week due to dinner party supplies. 
                    Should we adjust entertainment budget?"
                  </p>
                </div>
                
                <div className="p-3 bg-white rounded-lg border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Avatar className="h-6 w-6">
                      <AvatarFallback>M</AvatarFallback>
                    </Avatar>
                    <span className="font-bold text-blue-800">Mike</span>
                    <span className="text-xs text-gray-500">Yesterday</span>
                  </div>
                  <p className="text-sm text-blue-700">
                    "Great news! Got a bonus this month. Let's put $1000 toward the house fund!"
                  </p>
                </div>
                
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Send Message to Spouse
                </Button>
              </CardContent>
            </Card>

            {/* Task Assignment */}
            <Card className="border-2 border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="text-green-800 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Financial Tasks
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-green-800">Pay utilities bill</span>
                  </div>
                  <Badge className="bg-blue-100 text-blue-800">Mike</Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200">
                  <div className="flex items-center gap-3">
                    <AlertCircle className="h-5 w-5 text-orange-500" />
                    <span className="text-green-800">Review insurance policy</span>
                  </div>
                  <Badge className="bg-pink-100 text-pink-800">Sarah</Badge>
                </div>
                
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200">
                  <div className="flex items-center gap-3">
                    <AlertCircle className="h-5 w-5 text-orange-500" />
                    <span className="text-green-800">Plan retirement contribution</span>
                  </div>
                  <Badge className="bg-purple-100 text-purple-800">Joint</Badge>
                </div>
                
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Add New Task
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Planning Tab */}
        <TabsContent value="planning" className="space-y-6">
          <Card className="border-2 border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-purple-800">Upcoming Joint Expenses</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {upcomingExpenses.map((expense, index) => {
                const Icon = expense.icon;
                return (
                  <div key={index} className="p-4 bg-white rounded-lg border border-purple-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Icon className="h-6 w-6 text-purple-600" />
                        <div>
                          <h4 className="font-bold text-purple-800">{expense.name}</h4>
                          <p className="text-sm text-purple-600">
                            {new Date(expense.date).toLocaleDateString()} • {expense.category}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-purple-800">
                          ${expense.amount}
                        </p>
                        <Badge className="bg-purple-100 text-purple-800">
                          {expense.responsible}
                        </Badge>
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Future Planning */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-2 border-indigo-200 bg-white">
              <CardHeader>
                <CardTitle className="text-indigo-800">5-Year Financial Plan</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>House Purchase</span>
                    <Badge className="bg-green-100 text-green-800">On Track</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Emergency Fund (6 months)</span>
                    <Badge className="bg-yellow-100 text-yellow-800">68%</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Retirement Contributions</span>
                    <Badge className="bg-green-100 text-green-800">15%</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Children's Education Fund</span>
                    <Badge className="bg-blue-100 text-blue-800">Planning</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-indigo-200 bg-white">
              <CardHeader>
                <CardTitle className="text-indigo-800">Budget Meeting Scheduler</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-indigo-50 rounded-lg">
                  <h4 className="font-bold text-indigo-800">Next Meeting:</h4>
                  <p className="text-indigo-700">Sunday, February 15th at 7:00 PM</p>
                  <p className="text-sm text-indigo-600">Monthly budget review & planning</p>
                </div>
                
                <Button className="w-full bg-indigo-600 hover:bg-indigo-700">
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Budget Meeting
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Giving Tab */}
        <TabsContent value="giving" className="space-y-6">
          <Card className="border-2 border-rose-200 bg-rose-50">
            <CardHeader>
              <CardTitle className="text-rose-800 flex items-center gap-2">
                <Heart className="h-5 w-5" />
                Joint Giving & Stewardship
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-white rounded-lg border border-rose-200">
                  <h4 className="font-bold text-rose-800 mb-2">This Month's Giving</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Regular Tithe (10%)</span>
                      <span className="font-bold">$850</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Missions Support</span>
                      <span className="font-bold">$100</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Local Ministry</span>
                      <span className="font-bold">$75</span>
                    </div>
                    <div className="flex justify-between font-bold text-rose-800 border-t pt-2">
                      <span>Total Given</span>
                      <span>$1,025</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-white rounded-lg border border-rose-200">
                  <h4 className="font-bold text-rose-800 mb-2">Giving Goals</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Monthly Target</span>
                      <span className="font-bold">$850</span>
                    </div>
                    <Progress value={120} className="h-2" />
                    <p className="text-xs text-green-600">You've exceeded your giving goal by 20%!</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-white rounded-lg border border-rose-200">
                <h4 className="font-bold text-rose-800 mb-3">💕 Marriage & Money Wisdom</h4>
                <blockquote className="italic text-rose-700 border-l-4 border-rose-300 pl-4">
                  "Two are better than one, because they have a good return for their labor: 
                  If either of them falls down, one can help the other up."
                  <footer className="text-sm font-normal mt-2">- Ecclesiastes 4:9-10</footer>
                </blockquote>
                <p className="text-rose-600 mt-3">
                  Together you're building a legacy of faithful stewardship and generous giving.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};