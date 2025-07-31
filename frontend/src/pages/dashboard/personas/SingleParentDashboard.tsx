/**
 * Single Parent Dashboard - Enhanced security and family-focused financial management
 * Features: Priority emergency fund, child expense tracking, crisis prevention, enhanced security
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
  Shield, 
  AlertTriangle, 
  Heart, 
  Home, 
  Baby,
  GraduationCap,
  TrendingUp,
  Calendar,
  Phone,
  Lock,
  Eye,
  Users,
  DollarSign,
  Wallet,
  Target,
  Stethoscope,
  ShoppingCart
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { TransactionCard } from '@/components/financial/TransactionCard';
import { BudgetCard } from '@/components/financial/BudgetCard';
import { EmergencyFundCard } from '@/components/financial/EmergencyFundCard';

export const SingleParentDashboard: React.FC = () => {
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

  // Single parent specific dashboard stats
  const dashboardStats = {
    totalBalance: accounts?.reduce((sum, acc) => sum + acc.balance, 0) || 8450,
    monthlyIncome: 4200, // Single income household
    monthlyExpenses: 3800,
    emergencyFundProgress: 35, // Critical - needs improvement
    budgetProgress: 90,
    tithingPercentage: 8,
    savingsRate: 9
  };

  // Priority expense categories for single parents
  const priorityExpenses = [
    {
      category: "Children's Needs",
      budgeted: 1200,
      spent: 1050,
      priority: "Critical",
      color: "bg-red-500",
      icon: Baby,
      items: ["Childcare", "School supplies", "Healthcare", "Clothing"]
    },
    {
      category: "Housing & Utilities",
      budgeted: 1500,
      spent: 1485,
      priority: "Critical",
      color: "bg-red-500",
      icon: Home,
      items: ["Rent/Mortgage", "Utilities", "Insurance", "Maintenance"]
    },
    {
      category: "Education & Activities",
      budgeted: 300,
      spent: 275,
      priority: "High",
      color: "bg-orange-500",
      icon: GraduationCap,
      items: ["School fees", "Extracurriculars", "Tutoring", "Books"]
    },
    {
      category: "Healthcare",
      budgeted: 250,
      spent: 230,
      priority: "High",
      color: "bg-orange-500",
      icon: Stethoscope,
      items: ["Doctor visits", "Prescriptions", "Dental", "Vision"]
    }
  ];

  // Emergency contacts and support network
  const emergencyContacts = [
    { name: "Mom", phone: "(555) 123-4567", type: "Family", available: true },
    { name: "Sister Sarah", phone: "(555) 234-5678", type: "Family", available: true },
    { name: "Best Friend Lisa", phone: "(555) 345-6789", type: "Friend", available: true },
    { name: "Neighbor Tom", phone: "(555) 456-7890", type: "Neighbor", available: false },
    { name: "Childcare Provider", phone: "(555) 567-8901", type: "Care", available: true }
  ];

  // Financial security alerts
  const securityAlerts = [
    {
      type: "warning",
      title: "Emergency Fund Below Recommended",
      message: "Your emergency fund is only at 35%. As a single parent, aim for 9 months of expenses.",
      action: "Increase Emergency Savings",
      priority: "high"
    },
    {
      type: "info",
      title: "Budget Almost Reached",
      message: "You've used 90% of this month's budget. Monitor spending closely.",
      action: "Review Expenses",
      priority: "medium"
    }
  ];

  const isEmergencyFundCritical = dashboardStats.emergencyFundProgress < 50;
  const isBudgetTight = dashboardStats.budgetProgress > 85;

  return (
    <div className="container mx-auto p-6 space-y-6 bg-gradient-to-br from-pink-50 to-rose-50 min-h-screen">
      {/* Empowering Header */}
      <div className="flex items-center justify-between bg-white rounded-lg p-6 border-2 border-pink-300 shadow-md">
        <div>
          <h1 className="text-3xl font-bold text-pink-800">
            You're doing amazing, {profile?.display_name || 'Supermom'}! 💪
          </h1>
          <p className="text-pink-600 mt-1">
            Managing it all with strength and wisdom
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Badge className="bg-pink-100 text-pink-800 border-pink-200 text-lg px-4 py-2">
            Single Parent Warrior
          </Badge>
          <div className="text-right">
            <p className="text-sm text-gray-600">Family Funds</p>
            <p className="text-2xl font-bold text-pink-800">
              ${dashboardStats.totalBalance.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Security Alerts */}
      {(isEmergencyFundCritical || isBudgetTight) && (
        <div className="space-y-3">
          {securityAlerts.map((alert, index) => (
            <Alert key={index} className={`border-2 ${alert.priority === 'high' ? 'border-red-300 bg-red-50' : 'border-yellow-300 bg-yellow-50'}`}>
              <AlertTriangle className={`h-4 w-4 ${alert.priority === 'high' ? 'text-red-600' : 'text-yellow-600'}`} />
              <div className="flex justify-between items-start">
                <div>
                  <AlertDescription className={alert.priority === 'high' ? 'text-red-800' : 'text-yellow-800'}>
                    <span className="font-bold">{alert.title}:</span> {alert.message}
                  </AlertDescription>
                </div>
                <Button variant="outline" size="sm" className="ml-4">
                  {alert.action}
                </Button>
              </div>
            </Alert>
          ))}
        </div>
      )}

      {/* Dashboard Statistics */}
      <DashboardStats 
        persona="single_parent" 
        stats={dashboardStats}
        className="mb-6" 
      />

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6 bg-white border-2 border-pink-200">
          <TabsTrigger value="overview" className="data-[state=active]:bg-pink-100">
            <Home className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="children" className="data-[state=active]:bg-pink-100">
            <Baby className="h-4 w-4 mr-2" />
            Children
          </TabsTrigger>
          <TabsTrigger value="budget" className="data-[state=active]:bg-pink-100">
            <Wallet className="h-4 w-4 mr-2" />
            Budget
          </TabsTrigger>
          <TabsTrigger value="emergency" className="data-[state=active]:bg-pink-100">
            <Shield className="h-4 w-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="support" className="data-[state=active]:bg-pink-100">
            <Users className="h-4 w-4 mr-2" />
            Support
          </TabsTrigger>
          <TabsTrigger value="faith" className="data-[state=active]:bg-pink-100">
            <Heart className="h-4 w-4 mr-2" />
            Faith
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Priority Expenses Dashboard */}
            <Card className="border-2 border-pink-200 bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-pink-800">
                  <Target className="h-5 w-5" />
                  Priority Expenses This Month
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {priorityExpenses.slice(0, 3).map((expense, index) => {
                  const Icon = expense.icon;
                  const percentage = (expense.spent / expense.budgeted) * 100;
                  
                  return (
                    <div key={index} className="p-3 border border-pink-200 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Icon className="h-5 w-5 text-pink-600" />
                          <div>
                            <p className="font-medium">{expense.category}</p>
                            <p className="text-sm text-gray-600">{expense.priority} Priority</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold">${expense.spent} / ${expense.budgeted}</p>
                          <Badge 
                            className={`text-xs ${
                              percentage > 90 ? 'bg-red-100 text-red-800' :
                              percentage > 75 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}
                          >
                            {Math.round(percentage)}%
                          </Badge>
                        </div>
                      </div>
                      <Progress 
                        value={percentage} 
                        className="h-2"
                        indicatorClassName={percentage > 90 ? 'bg-red-500' : expense.color}
                      />
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="border-2 border-pink-200 bg-white">
              <CardHeader>
                <CardTitle className="text-pink-800">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button className="w-full bg-red-600 hover:bg-red-700">
                  <Shield className="h-4 w-4 mr-2" />
                  Add to Emergency Fund
                </Button>
                <Button className="w-full bg-blue-600 hover:bg-blue-700">
                  <Baby className="h-4 w-4 mr-2" />
                  Log Child Expense
                </Button>
                <Button className="w-full bg-green-600 hover:bg-green-700">
                  <Calendar className="h-4 w-4 mr-2" />
                  Schedule Bill Payment
                </Button>
                <Button variant="outline" className="w-full border-pink-200 text-pink-700">
                  <Eye className="h-4 w-4 mr-2" />
                  Review Security Settings
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Recent Transactions */}
          <Card className="border-2 border-pink-200 bg-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-pink-800">
                <TrendingUp className="h-5 w-5" />
                Recent Family Expenses
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {transactions?.slice(0, 5).map((transaction) => (
                <TransactionCard
                  key={transaction.id}
                  transaction={transaction}
                  persona="single_parent"
                  showSplitButton={true}
                  showCategory={true}
                />
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Children Tab */}
        <TabsContent value="children" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Child Expense Tracking */}
            <Card className="border-2 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-800 flex items-center gap-2">
                  <Baby className="h-5 w-5" />
                  Children's Expenses This Month
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {priorityExpenses[0].items.map((item, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-white rounded-lg border border-blue-200">
                    <span className="font-medium text-blue-800">{item}</span>
                    <span className="font-bold text-blue-600">${(Math.random() * 300 + 50).toFixed(0)}</span>
                  </div>
                ))}
                <div className="pt-3 border-t border-blue-200">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-blue-800">Total Children's Expenses</span>
                    <span className="text-xl font-bold text-blue-600">$1,050</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Education Planning */}
            <Card className="border-2 border-purple-200 bg-purple-50">
              <CardHeader>
                <CardTitle className="text-purple-800 flex items-center gap-2">
                  <GraduationCap className="h-5 w-5" />
                  Education Savings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">College Fund Progress</span>
                    <span className="font-bold">$12,500</span>
                  </div>
                  <Progress value={42} className="h-3" indicatorClassName="bg-purple-500" />
                  <p className="text-sm text-purple-600">42% toward $30,000 goal</p>
                </div>
                
                <div className="p-3 bg-white rounded-lg border border-purple-200">
                  <h4 className="font-bold text-purple-800 mb-2">Education Priority Tips</h4>
                  <ul className="text-sm text-purple-700 space-y-1">
                    <li>• 529 plans offer tax advantages</li>
                    <li>• Start early for compound growth</li>
                    <li>• Consider matching family contributions</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Child Activity Planner */}
          <Card className="border-2 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-800">Upcoming Child Expenses</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 bg-white rounded-lg border border-green-200">
                  <div className="flex items-center gap-3 mb-2">
                    <Calendar className="h-5 w-5 text-green-600" />
                    <span className="font-bold">School Registration</span>
                  </div>
                  <p className="text-sm text-gray-600">Due: March 15</p>
                  <p className="font-bold text-green-600">$150</p>
                </div>
                
                <div className="p-4 bg-white rounded-lg border border-green-200">
                  <div className="flex items-center gap-3 mb-2">
                    <Stethoscope className="h-5 w-5 text-green-600" />
                    <span className="font-bold">Annual Checkup</span>
                  </div>
                  <p className="text-sm text-gray-600">Due: April 1</p>
                  <p className="font-bold text-green-600">$80</p>
                </div>
                
                <div className="p-4 bg-white rounded-lg border border-green-200">
                  <div className="flex items-center gap-3 mb-2">
                    <ShoppingCart className="h-5 w-5 text-green-600" />
                    <span className="font-bold">Summer Clothes</span>
                  </div>
                  <p className="text-sm text-gray-600">Due: May 1</p>
                  <p className="font-bold text-green-600">$200</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Budget Tab */}
        <TabsContent value="budget" className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            <Card className="border-2 border-pink-200 bg-white">
              <CardHeader>
                <CardTitle className="text-pink-800">Priority-Based Budget</CardTitle>
                <p className="text-pink-600 text-sm">Expenses organized by family priority level</p>
              </CardHeader>
              <CardContent className="space-y-6">
                {priorityExpenses.map((expense, index) => {
                  const Icon = expense.icon;
                  const percentage = (expense.spent / expense.budgeted) * 100;
                  
                  return (
                    <div key={index} className="p-4 border border-pink-200 rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <Icon className="h-6 w-6 text-pink-600" />
                          <div>
                            <h4 className="font-bold text-pink-800">{expense.category}</h4>
                            <p className="text-sm text-pink-600">{expense.priority} Priority</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold">${expense.spent} / ${expense.budgeted}</p>
                          <Badge 
                            className={`${
                              percentage > 90 ? 'bg-red-100 text-red-800' :
                              percentage > 75 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-green-100 text-green-800'
                            }`}
                          >
                            {Math.round(percentage)}% Used
                          </Badge>
                        </div>
                      </div>
                      
                      <Progress 
                        value={percentage} 
                        className="h-3 mb-3"
                        indicatorClassName={percentage > 90 ? 'bg-red-500' : expense.color}
                      />
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        {expense.items.map((item, itemIndex) => (
                          <Badge key={itemIndex} variant="outline" className="text-xs">
                            {item}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Emergency/Security Tab */}
        <TabsContent value="emergency" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Emergency Fund - Critical for Single Parents */}
            <Card className="border-2 border-red-200 bg-red-50">
              <CardHeader>
                <CardTitle className="text-red-800 flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Emergency Fund (Critical Priority)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Current Progress</span>
                    <span className="font-bold text-red-800">{dashboardStats.emergencyFundProgress}%</span>
                  </div>
                  <Progress 
                    value={dashboardStats.emergencyFundProgress} 
                    className="h-4"
                    indicatorClassName="bg-red-500"
                  />
                  <div className="flex justify-between text-sm">
                    <span>Current: $8,450</span>
                    <span>Goal: $25,000 (9 months)</span>
                  </div>
                </div>
                
                <Alert className="border-red-300 bg-red-100">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <AlertDescription className="text-red-800">
                    <strong>Action Needed:</strong> Single parents need 9 months of expenses saved. 
                    You're currently at only 3.2 months coverage.
                  </AlertDescription>
                </Alert>
                
                <Button className="w-full bg-red-600 hover:bg-red-700">
                  <DollarSign className="h-4 w-4 mr-2" />
                  Set Up Auto-Transfer to Emergency Fund
                </Button>
              </CardContent>
            </Card>

            {/* Security Settings */}
            <Card className="border-2 border-gray-200 bg-white">
              <CardHeader>
                <CardTitle className="text-gray-800 flex items-center gap-2">
                  <Lock className="h-5 w-5" />
                  Account Security
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span>Two-Factor Authentication</span>
                    <Badge className="bg-green-100 text-green-800">Active</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Account Alerts</span>
                    <Badge className="bg-green-100 text-green-800">On</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Emergency Contacts</span>
                    <Badge className="bg-blue-100 text-blue-800">5 Added</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Budget Alerts</span>
                    <Badge className="bg-green-100 text-green-800">On</Badge>
                  </div>
                </div>
                
                <Button variant="outline" className="w-full">
                  <Eye className="h-4 w-4 mr-2" />
                  Review All Security Settings
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Crisis Prevention Plan */}
          <Card className="border-2 border-orange-200 bg-orange-50">
            <CardHeader>
              <CardTitle className="text-orange-800">Financial Crisis Prevention Plan</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <h4 className="font-bold text-orange-800">If Income is Lost:</h4>
                  <ul className="space-y-2 text-sm text-orange-700">
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Apply for unemployment benefits immediately</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Contact mortgage/rent for payment options</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Review all non-essential subscriptions</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Activate support network</span>
                    </li>
                  </ul>
                </div>
                
                <div className="space-y-3">
                  <h4 className="font-bold text-orange-800">Emergency Resources:</h4>
                  <ul className="space-y-2 text-sm text-orange-700">
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Local food banks and assistance programs</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Utility assistance programs</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Childcare assistance programs</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-orange-500 rounded-full" />
                      <span>Community support groups</span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Support Tab */}
        <TabsContent value="support" className="space-y-6">
          <Card className="border-2 border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800 flex items-center gap-2">
                <Phone className="h-5 w-5" />
                Emergency Contact Network
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {emergencyContacts.map((contact, index) => (
                <div key={index} className={`p-4 rounded-lg border-2 ${contact.available ? 'bg-white border-blue-200' : 'bg-gray-100 border-gray-300'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full ${contact.available ? 'bg-green-500' : 'bg-gray-400'}`} />
                      <div>
                        <p className="font-bold text-blue-800">{contact.name}</p>
                        <p className="text-sm text-blue-600">{contact.type}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-blue-800">{contact.phone}</p>
                      <Badge className={contact.available ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}>
                        {contact.available ? 'Available' : 'Unavailable'}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
              
              <Button variant="outline" className="w-full border-blue-200 text-blue-700">
                <Users className="h-4 w-4 mr-2" />
                Add Emergency Contact
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Faith Tab */}
        <TabsContent value="faith" className="space-y-6">
          <Card className="border-2 border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-purple-800 flex items-center gap-2">
                <Heart className="h-5 w-5" />
                Faith & Stewardship
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-white rounded-lg border border-purple-200">
                  <h4 className="font-bold text-purple-800 mb-2">This Month's Giving</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Regular Tithe</span>
                      <span className="font-bold">$336</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Special Offering</span>
                      <span className="font-bold">$50</span>
                    </div>
                    <div className="flex justify-between font-bold text-purple-800 border-t pt-2">
                      <span>Total Given</span>
                      <span>$386</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-white rounded-lg border border-purple-200">
                  <h4 className="font-bold text-purple-800 mb-2">Giving Goal</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">Monthly Target (8%)</span>
                      <span className="font-bold">$400</span>
                    </div>
                    <Progress value={96} className="h-2" />
                    <p className="text-xs text-green-600">You're 96% to your giving goal!</p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-white rounded-lg border border-purple-200">
                <h4 className="font-bold text-purple-800 mb-3">💜 Encouragement for Single Parents</h4>
                <blockquote className="italic text-purple-700 border-l-4 border-purple-300 pl-4">
                  "She is clothed with strength and dignity; she can laugh at the days to come. 
                  She speaks with wisdom, and faithful instruction is on her tongue."
                  <footer className="text-sm font-normal mt-2">- Proverbs 31:25-26</footer>
                </blockquote>
                <p className="text-purple-600 mt-3">
                  You are strong, capable, and blessed. God sees your efforts and provides for your family's needs.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};