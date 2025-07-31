/**
 * Teen Dashboard - Age-appropriate financial management with educational focus
 * Features: Savings goals, job income tracking, basic budgeting, biblical stewardship
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { 
  Wallet, 
  TrendingUp, 
  Target, 
  BookOpen, 
  Heart, 
  Star,
  Gift,
  Banknote,
  GraduationCap,
  Users
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { TransactionCard } from '@/components/financial/TransactionCard';
import { EmergencyFundCard } from '@/components/financial/EmergencyFundCard';

export const TeenDashboard: React.FC = () => {
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

  // Teen-specific dashboard stats
  const dashboardStats = {
    totalBalance: accounts?.reduce((sum, acc) => sum + acc.balance, 0) || 850,
    monthlyIncome: 320, // Part-time job + allowance
    monthlyExpenses: 180,
    emergencyFundProgress: 45,
    budgetProgress: 78,
    tithingPercentage: 12,
    savingsRate: 44
  };

  // Teen-specific financial insights
  const teenInsights = [
    {
      title: "Great Job Tracking!",
      description: "You're saving 44% of your income - that's amazing for a teen!",
      icon: Star,
      color: "text-yellow-500",
      bgColor: "bg-yellow-50",
      borderColor: "border-yellow-200"
    },
    {
      title: "College Fund Progress",
      description: "You're $850 closer to your college dreams!",
      icon: GraduationCap,
      color: "text-blue-500",
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200"
    },
    {
      title: "Tithing Heart",
      description: "Giving 12% shows a generous spirit - keep it up!",
      icon: Heart,
      color: "text-red-500",
      bgColor: "bg-red-50",
      borderColor: "border-red-200"
    }
  ];

  // Learning modules for teens
  const learningModules = [
    {
      title: "First Job Finances",
      description: "Managing paychecks, taxes, and savings",
      progress: 75,
      badge: "In Progress"
    },
    {
      title: "College Planning",
      description: "Saving strategies and financial aid basics",
      progress: 30,
      badge: "Started"
    },
    {
      title: "Biblical Money Wisdom",
      description: "What does God say about money?",
      progress: 100,
      badge: "Complete"
    }
  ];

  return (
    <div className="container mx-auto p-6 space-y-6 bg-gradient-to-br from-blue-50 to-cyan-50 min-h-screen">
      {/* Teen-specific Header */}
      <div className="flex items-center justify-between bg-white rounded-lg p-6 border-2 border-blue-300 shadow-md">
        <div>
          <h1 className="text-3xl font-bold text-blue-800">
            Hey {profile?.display_name || 'Teen'}! 👋
          </h1>
          <p className="text-blue-600 mt-1">
            Building your financial future, one dollar at a time!
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Badge className="bg-blue-100 text-blue-800 border-blue-200 text-lg px-4 py-2">
            Teen Saver
          </Badge>
          <div className="text-right">
            <p className="text-sm text-gray-600">Total Savings</p>
            <p className="text-2xl font-bold text-blue-800">
              ${dashboardStats.totalBalance.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Dashboard Statistics */}
      <DashboardStats 
        persona="teen" 
        stats={dashboardStats}
        className="mb-6" 
      />

      {/* Teen Insights Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {teenInsights.map((insight, index) => {
          const Icon = insight.icon;
          return (
            <Card key={index} className={`${insight.bgColor} border-2 ${insight.borderColor}`}>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <Icon className={`h-8 w-8 ${insight.color}`} />
                  <div>
                    <h3 className="font-bold text-gray-800">{insight.title}</h3>
                    <p className="text-sm text-gray-700">{insight.description}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6 bg-white border-2 border-blue-200">
          <TabsTrigger value="overview" className="data-[state=active]:bg-blue-100">
            <Wallet className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="transactions" className="data-[state=active]:bg-blue-100">
            <Banknote className="h-4 w-4 mr-2" />
            Money
          </TabsTrigger>
          <TabsTrigger value="goals" className="data-[state=active]:bg-blue-100">
            <Target className="h-4 w-4 mr-2" />
            Goals
          </TabsTrigger>
          <TabsTrigger value="learning" className="data-[state=active]:bg-blue-100">
            <BookOpen className="h-4 w-4 mr-2" />
            Learn
          </TabsTrigger>
          <TabsTrigger value="giving" className="data-[state=active]:bg-blue-100">
            <Heart className="h-4 w-4 mr-2" />
            Giving
          </TabsTrigger>
          <TabsTrigger value="family" className="data-[state=active]:bg-blue-100">
            <Users className="h-4 w-4 mr-2" />
            Family
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Activity */}
            <Card className="border-2 border-blue-200 bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-blue-800">
                  <TrendingUp className="h-5 w-5" />
                  Recent Money Moves
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {transactions?.slice(0, 5).map((transaction) => (
                  <TransactionCard
                    key={transaction.id}
                    transaction={transaction}
                    persona="teen"
                    showSplitButton={false}
                  />
                ))}
                <Button variant="outline" className="w-full border-blue-200 text-blue-700">
                  View All Transactions
                </Button>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="border-2 border-blue-200 bg-white">
              <CardHeader>
                <CardTitle className="text-blue-800">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <Gift className="h-4 w-4 mr-2" />
                  Record Allowance
                </Button>
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  <Banknote className="h-4 w-4 mr-2" />
                  Add Job Income
                </Button>
                <Button className="w-full bg-purple-600 hover:bg-purple-700">
                  <Target className="h-4 w-4 mr-2" />
                  Update Savings Goal
                </Button>
                <Button variant="outline" className="w-full border-red-200 text-red-600">
                  <Heart className="h-4 w-4 mr-2" />
                  Record Tithe/Offering
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Transactions Tab */}
        <TabsContent value="transactions" className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            <Card className="border-2 border-blue-200 bg-white">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-blue-800">All Transactions</CardTitle>
                  <Badge className="bg-blue-100 text-blue-800">
                    This Month: ${Math.abs(dashboardStats.monthlyExpenses - dashboardStats.monthlyIncome).toLocaleString()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {transactions?.map((transaction) => (
                  <TransactionCard
                    key={transaction.id}
                    transaction={transaction}
                    persona="teen"
                    showCategory={true}
                    showSplitButton={false}
                  />
                ))}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Goals Tab */}
        <TabsContent value="goals" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {goals?.map((goal) => (
              <EmergencyFundCard
                key={goal.id}
                goal={goal}
                persona="teen"
                onAddFunds={() => toast({
                  title: "Add Funds",
                  description: "Feature coming soon! Keep saving!",
                })}
              />
            ))}
          </div>

          {/* Teen-specific goal suggestions */}
          <Card className="border-2 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-800">Suggested Goals for Teens</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-white rounded-lg border border-green-200">
                  <h4 className="font-bold text-green-800">College Fund</h4>
                  <p className="text-sm text-green-600">Start saving for your education</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="text-xs">Target: $5,000</Badge>
                  </div>
                </div>
                <div className="p-4 bg-white rounded-lg border border-green-200">
                  <h4 className="font-bold text-green-800">First Car</h4>
                  <p className="text-sm text-green-600">Save for reliable transportation</p>
                  <div className="mt-2">
                    <Badge variant="outline" className="text-xs">Target: $8,000</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Learning Tab */}
        <TabsContent value="learning" className="space-y-6">
          <Card className="border-2 border-purple-200 bg-white">
            <CardHeader>
              <CardTitle className="text-purple-800">Financial Learning Path</CardTitle>
              <p className="text-purple-600">Master these skills to build a strong financial foundation</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {learningModules.map((module, index) => (
                <div key={index} className="p-4 border border-purple-200 rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-bold text-purple-800">{module.title}</h4>
                      <p className="text-sm text-purple-600">{module.description}</p>
                    </div>
                    <Badge 
                      className={
                        module.badge === 'Complete' ? 'bg-green-100 text-green-800' :
                        module.badge === 'In Progress' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }
                    >
                      {module.badge}
                    </Badge>
                  </div>
                  <Progress value={module.progress} className="h-2" />
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-sm text-gray-600">{module.progress}% Complete</span>
                    <Button variant="outline" size="sm" className="border-purple-200">
                      {module.progress === 100 ? 'Review' : 'Continue'}
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Giving Tab */}
        <TabsContent value="giving" className="space-y-6">
          <Card className="border-2 border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="text-red-800">Generous Heart Tracker</CardTitle>
              <p className="text-red-600">Track your giving and grow in generosity</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-white rounded-lg border border-red-200">
                  <h4 className="font-bold text-red-800 mb-2">This Month's Giving</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Tithe (10%)</span>
                      <span className="font-bold">$32.00</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Special Offerings</span>
                      <span className="font-bold">$6.50</span>
                    </div>
                    <div className="flex justify-between font-bold text-red-800 border-t pt-2">
                      <span>Total Given</span>
                      <span>$38.50</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-white rounded-lg border border-red-200">
                  <h4 className="font-bold text-red-800 mb-2">Giving Goal</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Monthly Target</span>
                      <span className="font-bold">$40.00</span>
                    </div>
                    <Progress value={96} className="h-2" />
                    <p className="text-xs text-green-600">You're 96% to your giving goal!</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-white rounded-lg border border-red-200">
                <h4 className="font-bold text-red-800 mb-3">💝 Biblical Giving Wisdom</h4>
                <blockquote className="italic text-red-700 border-l-4 border-red-300 pl-4">
                  "Each of you should give what you have decided in your heart to give, 
                  not reluctantly or under compulsion, for God loves a cheerful giver."
                  <footer className="text-sm font-normal mt-1">- 2 Corinthians 9:7</footer>
                </blockquote>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Family Tab */}
        <TabsContent value="family" className="space-y-6">
          <Card className="border-2 border-orange-200 bg-orange-50">
            <CardHeader>
              <CardTitle className="text-orange-800">Family Financial Team</CardTitle>
              <p className="text-orange-600">Learn from parents and build together</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-white rounded-lg border border-orange-200">
                  <h4 className="font-bold text-orange-800 mb-3">Parent Guidance</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Spending approved for this month</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>Emergency fund goal updated</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span>Great job with last month's saving!</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-white rounded-lg border border-orange-200">
                  <h4 className="font-bold text-orange-800 mb-3">Family Challenges</h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-orange-100 rounded-lg">
                      <p className="text-sm font-medium">Save $200 as a family</p>
                      <Progress value={65} className="h-1 mt-2" />
                      <p className="text-xs text-orange-600 mt-1">$130 / $200</p>
                    </div>
                  </div>
                </div>
              </div>

              <Button className="w-full bg-orange-600 hover:bg-orange-700">
                Request Parent Review
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};