/**
 * Two Parent Family Dashboard - Comprehensive family financial management
 * Features: Multi-child coordination, family budgeting, collaborative goals, allowance management
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
  Home, 
  Users, 
  TrendingUp, 
  Baby,
  GraduationCap,
  DollarSign,
  PiggyBank,
  Calendar,
  MessageCircle,
  CheckCircle,
  AlertCircle,
  Wallet,
  Target,
  Heart,
  Car,
  Building,
  ShoppingCart,
  Award,
  Settings,
  Eye,
  Sparkles
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { TransactionCard } from '@/components/financial/TransactionCard';
import { BudgetCard } from '@/components/financial/BudgetCard';
import { EmergencyFundCard } from '@/components/financial/EmergencyFundCard';

export const TwoParentFamilyDashboard: React.FC = () => {
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

  // Two parent family specific dashboard stats
  const dashboardStats = {
    totalBalance: accounts?.reduce((sum, acc) => sum + acc.balance, 0) || 72850,
    monthlyIncome: 12500, // Combined dual income
    monthlyExpenses: 9800,
    emergencyFundProgress: 78,
    budgetProgress: 74,
    tithingPercentage: 12,
    savingsRate: 22
  };

  // Family member management
  const familyMembers = [
    {
      name: "David",
      role: "Dad",
      age: 42,
      permissions: "Full Access",
      avatar: "/api/placeholder/40/40",
      monthlyAllowance: 0,
      responsibilities: ["Income", "Investments", "Insurance"]
    },
    {
      name: "Sarah",
      role: "Mom", 
      age: 39,
      permissions: "Full Access",
      avatar: "/api/placeholder/40/40",
      monthlyAllowance: 0,
      responsibilities: ["Household", "Children", "Healthcare"]
    },
    {
      name: "Emma",
      role: "Daughter",
      age: 16,
      permissions: "View & Limited Spending",
      avatar: "/api/placeholder/40/40",
      monthlyAllowance: 80,
      responsibilities: ["Chores", "School supplies", "Personal care"]
    },
    {
      name: "Jake",
      role: "Son",
      age: 12,
      permissions: "View Only",
      avatar: "/api/placeholder/40/40",
      monthlyAllowance: 40,
      responsibilities: ["Chores", "Pet care", "Room maintenance"]
    },
    {
      name: "Lily",
      role: "Daughter",
      age: 8,
      permissions: "Supervised",
      avatar: "/api/placeholder/40/40",
      monthlyAllowance: 20,
      responsibilities: ["Simple chores", "Toy organization"]
    }
  ];

  // Family budget categories with responsibility assignment
  const familyBudgetCategories = [
    {
      name: "Housing & Utilities",
      budgeted: 3200,
      spent: 3180,
      manager: "David",
      children: 0,
      percentage: 99,
      color: "bg-blue-500"
    },
    {
      name: "Food & Groceries", 
      budgeted: 1200,
      spent: 1050,
      manager: "Sarah",
      children: 5,
      percentage: 88,
      color: "bg-green-500"
    },
    {
      name: "Children's Activities",
      budgeted: 800,
      spent: 720,
      manager: "Joint",
      children: 3,
      percentage: 90,
      color: "bg-purple-500"
    },
    {
      name: "Transportation", 
      budgeted: 650,
      spent: 580,
      manager: "David",
      children: 2,
      percentage: 89,
      color: "bg-orange-500"
    },
    {
      name: "Healthcare",
      budgeted: 450,
      spent: 385,
      manager: "Sarah",
      children: 5,
      percentage: 86,
      color: "bg-red-500"
    },
    {
      name: "Education",
      budgeted: 600,
      spent: 550,
      manager: "Joint",
      children: 3,
      percentage: 92,
      color: "bg-indigo-500"
    }
  ];

  // Family goals with multi-member contributions
  const familyGoals = [
    {
      name: "Family Vacation Fund",
      target: 8000,
      current: 5200,
      progress: 65,
      priority: "High",
      targetDate: "2025-07-15",
      contributors: {
        parents: 4800,
        children: 400
      },
      icon: Car
    },
    {
      name: "Children's College Fund",
      target: 50000,
      current: 28500,
      progress: 57,
      priority: "Critical",
      targetDate: "2030-08-31",
      contributors: {
        parents: 28000,
        children: 500
      },
      icon: GraduationCap
    },
    {
      name: "Home Renovation",
      target: 25000,
      current: 12750,
      progress: 51,
      priority: "Medium",
      targetDate: "2026-03-31",
      contributors: {
        parents: 12750,
        children: 0
      },
      icon: Building
    }
  ];

  // Family chore and allowance tracking
  const choreTracker = [
    {
      child: "Emma",
      choresCompleted: 8,
      choresTotal: 10,
      allowanceEarned: 64,
      allowanceTotal: 80,
      bonusOpportunities: 2
    },
    {
      child: "Jake", 
      choresCompleted: 6,
      choresTotal: 8,
      allowanceEarned: 30,
      allowanceTotal: 40,
      bonusOpportunities: 1
    },
    {
      child: "Lily",
      choresCompleted: 4,
      choresTotal: 5,
      allowanceEarned: 16,
      allowanceTotal: 20,
      bonusOpportunities: 3
    }
  ];

  // Recent family activity
  const familyActivity = [
    {
      member: "Sarah",
      action: "Approved Emma's school trip expense",
      amount: 45.00,
      time: "1 hour ago",
      category: "Education",
      avatar: "/api/placeholder/32/32"
    },
    {
      member: "Jake",
      action: "Completed weekly chores",
      amount: 10.00,
      time: "3 hours ago", 
      category: "Allowance",
      avatar: "/api/placeholder/32/32"
    },
    {
      member: "David",
      action: "Added to vacation fund",
      amount: 300.00,
      time: "Yesterday",
      category: "Savings",
      avatar: "/api/placeholder/32/32"
    },
    {
      member: "Emma",
      action: "Saved birthday money",
      amount: 75.00,
      time: "2 days ago",
      category: "Personal Savings",
      avatar: "/api/placeholder/32/32"
    }
  ];

  // Upcoming family expenses
  const upcomingFamilyExpenses = [
    {
      name: "Emma's School Dance",
      amount: 85,
      date: "2025-02-14",
      responsible: "Emma (pre-approved)",
      category: "Education",
      icon: Heart
    },
    {
      name: "Family Car Insurance",
      amount: 800,
      date: "2025-03-01",
      responsible: "David",
      category: "Transportation", 
      icon: Car
    },
    {
      name: "Jake's Soccer Registration",
      amount: 120,
      date: "2025-03-15",
      responsible: "Sarah",
      category: "Activities",
      icon: Award
    },
    {
      name: "Family Spring Break",
      amount: 2500,
      date: "2025-04-01",
      responsible: "Joint Planning",
      category: "Travel",
      icon: Car
    }
  ];

  return (
    <div className="container mx-auto p-6 space-y-6 bg-gradient-to-br from-emerald-50 to-teal-50 min-h-screen">
      {/* Family Header */}
      <div className="flex items-center justify-between bg-white rounded-lg p-6 border-2 border-emerald-300 shadow-md">
        <div className="flex items-center gap-4">
          <div className="flex -space-x-2">
            {familyMembers.slice(0, 4).map((member, index) => (
              <Avatar key={index} className="border-2 border-white">
                <AvatarImage src={member.avatar} />
                <AvatarFallback>{member.name[0]}</AvatarFallback>
              </Avatar>
            ))}
            {familyMembers.length > 4 && (
              <Avatar className="border-2 border-white">
                <AvatarFallback>+{familyMembers.length - 4}</AvatarFallback>
              </Avatar>
            )}
          </div>
          <div>
            <h1 className="text-3xl font-bold text-emerald-800">
              The Johnson Family! 👨‍👩‍👧‍👦
            </h1>
            <p className="text-emerald-600 mt-1">
              Working together toward our dreams - 5 members strong!
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 text-lg px-4 py-2">
            Two Parent Family
          </Badge>
          <div className="text-right">
            <p className="text-sm text-gray-600">Family Net Worth</p>
            <p className="text-2xl font-bold text-emerald-800">
              ${dashboardStats.totalBalance.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Dashboard Statistics */}
      <DashboardStats 
        persona="two_parent_family" 
        stats={dashboardStats}
        className="mb-6" 
      />

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6 bg-white border-2 border-emerald-200">
          <TabsTrigger value="overview" className="data-[state=active]:bg-emerald-100">
            <Home className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="family" className="data-[state=active]:bg-emerald-100">
            <Users className="h-4 w-4 mr-2" />
            Family
          </TabsTrigger>
          <TabsTrigger value="budget" className="data-[state=active]:bg-emerald-100">
            <Wallet className="h-4 w-4 mr-2" />
            Budget
          </TabsTrigger>
          <TabsTrigger value="goals" className="data-[state=active]:bg-emerald-100">
            <Target className="h-4 w-4 mr-2" />
            Goals
          </TabsTrigger>
          <TabsTrigger value="planning" className="data-[state=active]:bg-emerald-100">
            <Calendar className="h-4 w-4 mr-2" />
            Planning
          </TabsTrigger>
          <TabsTrigger value="giving" className="data-[state=active]:bg-emerald-100">
            <Heart className="h-4 w-4 mr-2" />
            Giving
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Family Financial Summary */}
            <Card className="border-2 border-emerald-200 bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-emerald-800">
                  <TrendingUp className="h-5 w-5" />
                  Family Financial Health
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="text-2xl font-bold text-green-800">$2,700</div>
                    <div className="text-sm text-green-600">Net Savings This Month</div>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="text-2xl font-bold text-blue-800">$1,500</div>
                    <div className="text-sm text-blue-600">Family Giving</div>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Emergency Fund Progress</span>
                    <span className="font-bold">{dashboardStats.emergencyFundProgress}%</span>
                  </div>
                  <Progress value={dashboardStats.emergencyFundProgress} className="h-2" indicatorClassName="bg-emerald-500" />
                  <p className="text-xs text-emerald-600">6 months of expenses saved - Excellent!</p>
                </div>
              </CardContent>
            </Card>

            {/* Quick Family Actions */}
            <Card className="border-2 border-emerald-200 bg-white">
              <CardHeader>
                <CardTitle className="text-emerald-800">Quick Family Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <DollarSign className="h-4 w-4 mr-2" />
                  Add Family Expense
                </Button>
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  <Target className="h-4 w-4 mr-2" />
                  Update Family Goal
                </Button>
                <Button className="w-full bg-purple-600 hover:bg-purple-700">
                  <Award className="h-4 w-4 mr-2" />
                  Manage Allowances
                </Button>
                <Button variant="outline" className="w-full border-emerald-200 text-emerald-700">
                  <Calendar className="h-4 w-4 mr-2" />
                  Plan Family Meeting
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Recent Family Activity */}
          <Card className="border-2 border-emerald-200 bg-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-emerald-800">
                <Users className="h-5 w-5" />
                Recent Family Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {familyActivity.map((activity, index) => (
                <div key={index} className="flex items-center justify-between p-3 border border-emerald-200 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={activity.avatar} />
                      <AvatarFallback>{activity.member[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium text-emerald-800">
                        <span className="font-bold">{activity.member}</span> {activity.action}
                      </p>
                      <p className="text-sm text-emerald-600">{activity.time} • {activity.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-emerald-800">
                      ${activity.amount.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Family Tab */}
        <TabsContent value="family" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Family Members Management */}
            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-800 flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  Family Members & Permissions
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {familyMembers.map((member, index) => (
                  <div key={index} className="p-4 bg-white rounded-lg border border-blue-200">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Avatar>
                          <AvatarImage src={member.avatar} />
                          <AvatarFallback>{member.name[0]}</AvatarFallback>
                        </Avatar>
                        <div>
                          <h4 className="font-bold text-blue-800">{member.name}</h4>
                          <p className="text-sm text-blue-600">{member.role}, Age {member.age}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        {member.monthlyAllowance > 0 && (
                          <p className="font-bold text-blue-800">${member.monthlyAllowance}/month</p>
                        )}
                        <Badge className={
                          member.permissions === 'Full Access' ? 'bg-green-100 text-green-800' :
                          member.permissions === 'View & Limited Spending' ? 'bg-yellow-100 text-yellow-800' :
                          member.permissions === 'View Only' ? 'bg-blue-100 text-blue-800' :
                          'bg-orange-100 text-orange-800'
                        }>
                          {member.permissions}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {member.responsibilities.map((responsibility, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {responsibility}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Chore & Allowance Tracker */}
            <Card className="border-2 border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="text-green-800 flex items-center gap-2">
                  <Award className="h-5 w-5" />
                  Chore & Allowance Tracker
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {choreTracker.map((child, index) => (
                  <div key={index} className="p-4 bg-white rounded-lg border border-green-200">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-bold text-green-800">{child.child}</h4>
                      <Badge className="bg-green-100 text-green-800">
                        ${child.allowanceEarned} earned
                      </Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Chores: {child.choresCompleted}/{child.choresTotal}</span>
                        <span>{Math.round((child.choresCompleted / child.choresTotal) * 100)}%</span>
                      </div>
                      <Progress 
                        value={(child.choresCompleted / child.choresTotal) * 100} 
                        className="h-2"
                        indicatorClassName="bg-green-500"
                      />
                      
                      <div className="flex justify-between text-sm">
                        <span>Allowance: ${child.allowanceEarned}/${child.allowanceTotal}</span>
                        <span className="text-blue-600">{child.bonusOpportunities} bonus tasks</span>
                      </div>
                    </div>
                  </div>
                ))}
                
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Update Chore Status
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Budget Tab */}
        <TabsContent value="budget" className="space-y-6">
          <Card className="border-2 border-emerald-200 bg-white">
            <CardHeader>
              <CardTitle className="text-emerald-800">Family Budget Management</CardTitle>
              <p className="text-emerald-600 text-sm">Coordinated spending across all family needs</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {familyBudgetCategories.map((category, index) => (
                <div key={index} className="p-4 border border-emerald-200 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-bold text-emerald-800">{category.name}</h4>
                      <p className="text-sm text-emerald-600">
                        Managed by: {category.manager} • Affects {category.children} children
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">${category.spent} / ${category.budgeted}</p>
                      <Badge 
                        className={`${
                          category.percentage > 95 ? 'bg-red-100 text-red-800' :
                          category.percentage > 85 ? 'bg-yellow-100 text-yellow-800' :
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
                    <span>
                      {category.manager === 'Joint' ? '👨‍👩' : category.manager === 'David' ? '👨' : '👩'} 
                      {category.children > 0 && ` +${category.children} kids`}
                    </span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Goals Tab */}
        <TabsContent value="goals" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {familyGoals.map((goal, index) => {
              const Icon = goal.icon;
              return (
                <Card key={index} className="border-2 border-emerald-200 bg-white">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Icon className="h-6 w-6 text-emerald-600" />
                        <div>
                          <CardTitle className="text-emerald-800">{goal.name}</CardTitle>
                          <p className="text-sm text-emerald-600">
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
                        <span className="font-bold text-emerald-800">{goal.progress}%</span>
                      </div>
                      <Progress value={goal.progress} className="h-3" indicatorClassName="bg-emerald-500" />
                      <div className="flex justify-between text-sm text-gray-600">
                        <span>${goal.current.toLocaleString()} saved</span>
                        <span>${goal.target.toLocaleString()} goal</span>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-blue-50 rounded-lg text-center">
                        <div className="font-bold text-blue-800">
                          ${goal.contributors.parents.toLocaleString()}
                        </div>
                        <div className="text-xs text-blue-600">Parents' Share</div>
                      </div>
                      <div className="p-3 bg-green-50 rounded-lg text-center">
                        <div className="font-bold text-green-800">
                          ${goal.contributors.children.toLocaleString()}
                        </div>
                        <div className="text-xs text-green-600">Children's Share</div>
                      </div>
                    </div>
                    
                    <Button className="w-full bg-emerald-600 hover:bg-emerald-700">
                      <DollarSign className="h-4 w-4 mr-2" />
                      Contribute to {goal.name}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Planning Tab */}
        <TabsContent value="planning" className="space-y-6">
          <Card className="border-2 border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-purple-800">Upcoming Family Expenses</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {upcomingFamilyExpenses.map((expense, index) => {
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

          {/* Family Planning Tools */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="border-2 border-emerald-200 bg-white">
              <CardHeader>
                <CardTitle className="text-emerald-800">Long-term Family Planning</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Children's Education Fund</span>
                    <Badge className="bg-green-100 text-green-800">On Track</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Family Emergency Fund (9 months)</span>
                    <Badge className="bg-green-100 text-green-800">78%</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Retirement Savings (Both Parents)</span>
                    <Badge className="bg-green-100 text-green-800">18%</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Home Maintenance Fund</span>
                    <Badge className="bg-yellow-100 text-yellow-800">Building</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-2 border-emerald-200 bg-white">
              <CardHeader>
                <CardTitle className="text-emerald-800">Family Meeting Scheduler</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 bg-emerald-50 rounded-lg">
                  <h4 className="font-bold text-emerald-800">Next Family Money Meeting:</h4>
                  <p className="text-emerald-700">Sunday, February 18th at 4:00 PM</p>
                  <p className="text-sm text-emerald-600">Monthly budget review & goal planning</p>
                </div>
                
                <div className="space-y-2">
                  <h5 className="font-medium text-emerald-800">Agenda Items:</h5>
                  <ul className="text-sm text-emerald-700 space-y-1">
                    <li>• Review allowance performance</li>
                    <li>• Plan summer vacation budget</li>
                    <li>• Discuss Emma's driving lessons fund</li>
                    <li>• Update college savings strategy</li>
                  </ul>
                </div>
                
                <Button className="w-full bg-emerald-600 hover:bg-emerald-700">
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Next Meeting
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
                Family Giving & Stewardship
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-white rounded-lg border border-rose-200">
                  <h4 className="font-bold text-rose-800 mb-2">This Month's Family Giving</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Regular Tithe (12%)</span>
                      <span className="font-bold">$1,500</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Children's Missions Support</span>
                      <span className="font-bold">$45</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Local Ministry Support</span>
                      <span className="font-bold">$200</span>
                    </div>
                    <div className="flex justify-between font-bold text-rose-800 border-t pt-2">
                      <span>Total Family Giving</span>
                      <span>$1,745</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-white rounded-lg border border-rose-200">
                  <h4 className="font-bold text-rose-800 mb-2">Children's Giving Tracker</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Emma's Tithe</span>
                      <span className="font-bold">$8.00</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Jake's Tithe</span>
                      <span className="font-bold">$4.00</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Lily's Tithe</span>
                      <span className="font-bold">$2.00</span>
                    </div>
                    <Progress value={85} className="h-2" />
                    <p className="text-xs text-green-600">All children consistently giving!</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-white rounded-lg border border-rose-200">
                <h4 className="font-bold text-rose-800 mb-3">👨‍👩‍👧‍👦 Family Stewardship Wisdom</h4>
                <blockquote className="italic text-rose-700 border-l-4 border-rose-300 pl-4">
                  "Train up a child in the way he should go; even when he is old he will not depart from it."
                  <footer className="text-sm font-normal mt-2">- Proverbs 22:6</footer>
                </blockquote>
                <p className="text-rose-600 mt-3">
                  By modeling faithful stewardship and involving children in giving decisions, 
                  you're building a legacy of generosity that will impact generations.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};