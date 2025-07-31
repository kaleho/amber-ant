/**
 * Fixed Income Dashboard - Accessible financial management for seniors and retirees
 * Features: Healthcare expense tracking, simplified UI, legacy planning, accessibility focus
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
  Home, 
  Heart, 
  Shield, 
  Stethoscope,
  DollarSign,
  PiggyBank,
  Calendar,
  Users,
  Phone,
  AlertTriangle,
  CheckCircle,
  Info,
  Building,
  FileText,
  Gift,
  BookOpen,
  Car,
  Wallet,
  TrendingUp,
  Settings
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { TransactionCard } from '@/components/financial/TransactionCard';
import { BudgetCard } from '@/components/financial/BudgetCard';
import { EmergencyFundCard } from '@/components/financial/EmergencyFundCard';

export const FixedIncomeDashboard: React.FC = () => {
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

  // Fixed income specific dashboard stats
  const dashboardStats = {
    totalBalance: accounts?.reduce((sum, acc) => sum + acc.balance, 0) || 284500,
    monthlyIncome: 3200, // Fixed income from pensions, social security
    monthlyExpenses: 2850,
    emergencyFundProgress: 95, // Well-funded for security
    budgetProgress: 89, // Close monitoring needed
    tithingPercentage: 15, // Higher percentage as stewardship focus
    savingsRate: 11
  };

  // Healthcare and essential expenses for fixed income
  const fixedIncomeCategories = [
    {
      name: "Healthcare & Medical",
      budgeted: 800,
      spent: 735,
      priority: "Critical",
      percentage: 92,
      color: "bg-red-500",
      icon: Stethoscope,
      description: "Doctor visits, prescriptions, insurance premiums"
    },
    {
      name: "Housing & Utilities",
      budgeted: 950,
      spent: 950,
      priority: "Critical", 
      percentage: 100,
      color: "bg-blue-500",
      icon: Home,
      description: "Mortgage/rent, utilities, property taxes"
    },
    {
      name: "Food & Essentials",
      budgeted: 400,
      spent: 375,
      priority: "Critical",
      percentage: 94,
      color: "bg-green-500",
      icon: ShoppingCart,
      description: "Groceries, household necessities"
    },
    {
      name: "Transportation",
      budgeted: 200,
      spent: 180,
      priority: "Important",
      percentage: 90,
      color: "bg-orange-500",
      icon: Car,
      description: "Car maintenance, gas, public transport"
    },
    {
      name: "Family & Giving",
      budgeted: 500,
      spent: 480,
      priority: "Important",
      percentage: 96,
      color: "bg-purple-500",
      icon: Heart,
      description: "Church giving, family support, gifts"
    }
  ];

  // Income sources tracking
  const incomeStreams = [
    {
      source: "Social Security",
      amount: 1850,
      frequency: "Monthly",
      reliable: true,
      nextPayment: "February 3rd",
      icon: Shield
    },
    {
      source: "Retirement Pension",
      amount: 1200,
      frequency: "Monthly", 
      reliable: true,
      nextPayment: "February 1st",
      icon: Building
    },
    {
      source: "Investment Income",
      amount: 150,
      frequency: "Quarterly",
      reliable: false,
      nextPayment: "March 31st",
      icon: TrendingUp
    }
  ];

  // Healthcare alerts and reminders
  const healthcareAlerts = [
    {
      type: "reminder",
      title: "Annual Physical Exam Due",
      message: "Your annual checkup with Dr. Smith is coming up next month.",
      dueDate: "March 15, 2025",
      priority: "medium"
    },
    {
      type: "info",
      title: "Prescription Refill Available",
      message: "Your blood pressure medication can be refilled starting February 10th.",
      dueDate: "February 10, 2025",
      priority: "high"
    },
    {
      type: "warning",
      title: "Healthcare Budget Alert",
      message: "You've used 92% of your healthcare budget this month.",
      dueDate: "Now",
      priority: "high"
    }
  ];

  // Legacy and estate planning items
  const legacyItems = [
    {
      item: "Will & Testament",
      status: "Updated",
      lastUpdate: "June 2024",
      nextReview: "June 2025",
      icon: FileText
    },
    {
      item: "Power of Attorney",
      status: "Current",
      lastUpdate: "March 2024",
      nextReview: "March 2027",
      icon: Shield
    },
    {
      item: "Healthcare Directive", 
      status: "Needs Review",
      lastUpdate: "January 2022",
      nextReview: "Overdue",
      icon: Stethoscope
    },
    {
      item: "Beneficiary Designations",
      status: "Current",
      lastUpdate: "August 2024",
      nextReview: "August 2025",
      icon: Users
    }
  ];

  // Emergency contacts with relationship info
  const emergencyContacts = [
    {
      name: "Sarah (Daughter)",
      phone: "(555) 123-4567",
      relationship: "Primary Contact",
      hasKeys: true,
      medicalContact: true
    },
    {
      name: "Dr. Robert Smith",
      phone: "(555) 234-5678", 
      relationship: "Primary Care Doctor",
      hasKeys: false,
      medicalContact: true
    },
    {
      name: "Michael (Son)",
      phone: "(555) 345-6789",
      relationship: "Secondary Contact",
      hasKeys: true,
      medicalContact: false
    },
    {
      name: "Elder John at Church",
      phone: "(555) 456-7890",
      relationship: "Spiritual Care",
      hasKeys: false,
      medicalContact: false
    }
  ];

  const isHealthcareBudgetHigh = dashboardStats.budgetProgress > 85;
  const isIncomeSecure = incomeStreams.every(stream => stream.reliable || stream.amount < 200);

  return (
    <div className="container mx-auto p-8 space-y-8 bg-gradient-to-br from-amber-50 to-orange-50 min-h-screen">
      {/* Senior-Friendly Header with Large Text */}
      <div className="flex items-center justify-between bg-white rounded-xl p-8 border-4 border-amber-300 shadow-lg">
        <div>
          <h1 className="text-4xl font-bold text-amber-800">
            Welcome, {profile?.display_name || 'Friend'}! 🌅
          </h1>
          <p className="text-amber-600 text-xl mt-2">
            Your trusted financial companion in retirement
          </p>
        </div>
        <div className="flex items-center gap-6">
          <Badge className="bg-amber-100 text-amber-800 border-amber-200 text-xl px-6 py-3">
            Fixed Income
          </Badge>
          <div className="text-right">
            <p className="text-lg text-gray-600">Total Assets</p>
            <p className="text-3xl font-bold text-amber-800">
              ${dashboardStats.totalBalance.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Health & Budget Alerts */}
      {(isHealthcareBudgetHigh || !isIncomeSecure) && (
        <div className="space-y-4">
          {healthcareAlerts.filter(alert => alert.priority === 'high').map((alert, index) => (
            <Alert key={index} className={`border-3 ${alert.type === 'warning' ? 'border-red-300 bg-red-50' : 'border-blue-300 bg-blue-50'}`}>
              <AlertTriangle className={`h-6 w-6 ${alert.type === 'warning' ? 'text-red-600' : 'text-blue-600'}`} />
              <div className="flex justify-between items-start">
                <div>
                  <AlertDescription className={`text-lg ${alert.type === 'warning' ? 'text-red-800' : 'text-blue-800'}`}>
                    <span className="font-bold">{alert.title}:</span> {alert.message}
                  </AlertDescription>
                </div>
                <Button variant="outline" size="lg" className="ml-6 text-lg">
                  Review
                </Button>
              </div>
            </Alert>
          ))}
        </div>
      )}

      {/* Dashboard Statistics */}
      <DashboardStats 
        persona="fixed_income" 
        stats={dashboardStats}
        className="mb-8" 
      />

      {/* Main Dashboard Tabs with Large, Clear Labels */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 bg-white border-4 border-amber-200 h-20">
          <TabsTrigger value="overview" className="data-[state=active]:bg-amber-100 text-lg">
            <Home className="h-6 w-6 mr-3" />
            Home
          </TabsTrigger>
          <TabsTrigger value="healthcare" className="data-[state=active]:bg-amber-100 text-lg">
            <Stethoscope className="h-6 w-6 mr-3" />
            Healthcare
          </TabsTrigger>
          <TabsTrigger value="budget" className="data-[state=active]:bg-amber-100 text-lg">
            <Wallet className="h-6 w-6 mr-3" />
            Budget
          </TabsTrigger>
          <TabsTrigger value="legacy" className="data-[state=active]:bg-amber-100 text-lg">
            <FileText className="h-6 w-6 mr-3" />
            Legacy
          </TabsTrigger>
          <TabsTrigger value="faith" className="data-[state=active]:bg-amber-100 text-lg">
            <Heart className="h-6 w-6 mr-3" />
            Faith
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Monthly Income Summary */}
            <Card className="border-4 border-amber-200 bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-3 text-amber-800 text-2xl">
                  <DollarSign className="h-8 w-8" />
                  Monthly Income Sources
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {incomeStreams.map((income, index) => {
                  const Icon = income.icon;
                  return (
                    <div key={index} className="p-4 border-2 border-amber-200 rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <Icon className="h-6 w-6 text-amber-600" />
                          <div>
                            <h4 className="text-lg font-bold text-amber-800">{income.source}</h4>
                            <p className="text-amber-600">Next: {income.nextPayment}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-amber-800">${income.amount}</p>
                          <Badge className={income.reliable ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                            {income.reliable ? 'Guaranteed' : 'Variable'}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div className="pt-4 border-t-2 border-amber-200">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-amber-800">Total Monthly Income</span>
                    <span className="text-2xl font-bold text-amber-600">
                      ${incomeStreams.reduce((sum, income) => sum + income.amount, 0)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions with Large Buttons */}
            <Card className="border-4 border-amber-200 bg-white">
              <CardHeader>
                <CardTitle className="text-amber-800 text-2xl">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full h-16 text-xl bg-red-600 hover:bg-red-700">
                  <Stethoscope className="h-6 w-6 mr-3" />
                  Log Healthcare Expense
                </Button>
                <Button className="w-full h-16 text-xl bg-blue-600 hover:bg-blue-700">
                  <Calendar className="h-6 w-6 mr-3" />
                  Schedule Appointment
                </Button>
                <Button className="w-full h-16 text-xl bg-green-600 hover:bg-green-700">
                  <Heart className="h-6 w-6 mr-3" />
                  Record Tithe/Offering
                </Button>
                <Button variant="outline" className="w-full h-16 text-xl border-amber-200 text-amber-700">
                  <Phone className="h-6 w-6 mr-3" />
                  Call Family Member
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Recent Transactions with Large Text */}
          <Card className="border-4 border-amber-200 bg-white">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-amber-800 text-2xl">
                <TrendingUp className="h-8 w-8" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {transactions?.slice(0, 5).map((transaction) => (
                <div key={transaction.id} className="p-4 border-2 border-amber-200 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-3xl">
                        {transaction.amount > 0 ? '💰' : transaction.category?.includes('Health') ? '🏥' : '🛒'}
                      </div>
                      <div>
                        <p className="text-lg font-bold text-amber-800">{transaction.description}</p>
                        <p className="text-amber-600">
                          {new Date(transaction.date).toLocaleDateString()} • {transaction.category}
                        </p>
                      </div>
                    </div>
                    <div className={`text-xl font-bold ${transaction.amount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {transaction.amount > 0 ? '+' : ''}${Math.abs(transaction.amount).toFixed(2)}
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Healthcare Tab */}
        <TabsContent value="healthcare" className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Healthcare Budget Tracking */}
            <Card className="border-4 border-red-200 bg-red-50">
              <CardHeader>
                <CardTitle className="text-red-800 text-2xl flex items-center gap-3">
                  <Stethoscope className="h-8 w-8" />
                  Healthcare Budget
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-medium">Monthly Healthcare Budget</span>
                    <span className="text-xl font-bold text-red-800">92%</span>
                  </div>
                  <Progress value={92} className="h-4" indicatorClassName="bg-red-500" />
                  <div className="flex justify-between text-lg">
                    <span>Spent: $735</span>
                    <span>Budget: $800</span>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <h4 className="text-lg font-bold text-red-800">This Month's Healthcare Expenses:</h4>
                  <div className="space-y-2 text-lg">
                    <div className="flex justify-between">
                      <span>Doctor Visits</span>
                      <span className="font-bold">$180</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Prescriptions</span>
                      <span className="font-bold">$285</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Insurance Premiums</span>
                      <span className="font-bold">$270</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Healthcare Reminders */}
            <Card className="border-4 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-blue-800 text-2xl flex items-center gap-3">
                  <Calendar className="h-8 w-8" />
                  Healthcare Reminders
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {healthcareAlerts.map((alert, index) => (
                  <div key={index} className="p-4 bg-white rounded-lg border-2 border-blue-200">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${
                          alert.priority === 'high' ? 'bg-red-100' : 
                          alert.priority === 'medium' ? 'bg-yellow-100' : 'bg-blue-100'
                        }`}>
                          {alert.type === 'warning' ? 
                            <AlertTriangle className={`h-6 w-6 ${alert.priority === 'high' ? 'text-red-600' : 'text-yellow-600'}`} /> :
                            <Info className="h-6 w-6 text-blue-600" />
                          }
                        </div>
                        <div>
                          <h4 className="text-lg font-bold text-blue-800">{alert.title}</h4>
                          <p className="text-blue-700">{alert.message}</p>
                          <p className="text-sm text-blue-600 mt-1">Due: {alert.dueDate}</p>
                        </div>
                      </div>
                      <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                        Action
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Emergency Contacts */}
          <Card className="border-4 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-green-800 text-2xl flex items-center gap-3">
                <Phone className="h-8 w-8" />
                Emergency Contacts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {emergencyContacts.map((contact, index) => (
                <div key={index} className="p-4 bg-white rounded-lg border-2 border-green-200">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xl font-bold text-green-800">{contact.name}</h4>
                      <p className="text-green-600 text-lg">{contact.relationship}</p>
                      <div className="flex gap-4 mt-2">
                        {contact.hasKeys && (
                          <Badge className="bg-blue-100 text-blue-800">Has Keys</Badge>
                        )}
                        {contact.medicalContact && (
                          <Badge className="bg-red-100 text-red-800">Medical Contact</Badge>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-mono text-green-800">{contact.phone}</p>
                      <Button className="mt-2 bg-green-600 hover:bg-green-700">
                        <Phone className="h-4 w-4 mr-2" />
                        Call
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Budget Tab */}
        <TabsContent value="budget" className="space-y-8">
          <Card className="border-4 border-amber-200 bg-white">
            <CardHeader>
              <CardTitle className="text-amber-800 text-2xl">Fixed Income Budget Management</CardTitle>
              <p className="text-amber-600 text-lg">Essential expenses prioritized for financial security</p>
            </CardHeader>
            <CardContent className="space-y-6">
              {fixedIncomeCategories.map((category, index) => {
                const Icon = category.icon;
                return (
                  <div key={index} className="p-6 border-3 border-amber-200 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <Icon className="h-8 w-8 text-amber-600" />
                        <div>
                          <h4 className="text-xl font-bold text-amber-800">{category.name}</h4>
                          <p className="text-amber-600">{category.description}</p>
                          <Badge className={
                            category.priority === 'Critical' ? 'bg-red-100 text-red-800 text-sm' :
                            'bg-orange-100 text-orange-800 text-sm'
                          }>
                            {category.priority} Priority
                          </Badge>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold">${category.spent} / ${category.budgeted}</p>
                        <Badge 
                          className={`text-lg ${
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
                      className="h-4"
                      indicatorClassName={category.percentage > 95 ? 'bg-red-500' : category.color}
                    />
                    
                    <div className="flex justify-between text-lg text-gray-600 mt-3">
                      <span>${category.budgeted - category.spent} remaining</span>
                      <span>{Math.round((category.budgeted - category.spent) / 30 * 10) / 10} days left</span>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Legacy Tab */}
        <TabsContent value="legacy" className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Estate Planning Checklist */}
            <Card className="border-4 border-purple-200 bg-purple-50">
              <CardHeader>
                <CardTitle className="text-purple-800 text-2xl flex items-center gap-3">
                  <FileText className="h-8 w-8" />
                  Estate Planning Checklist
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {legacyItems.map((item, index) => {
                  const Icon = item.icon;
                  return (
                    <div key={index} className="p-4 bg-white rounded-lg border-2 border-purple-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Icon className="h-6 w-6 text-purple-600" />
                          <div>
                            <h4 className="text-lg font-bold text-purple-800">{item.item}</h4>
                            <p className="text-purple-600">Last Updated: {item.lastUpdate}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge className={
                            item.status === 'Needs Review' ? 'bg-yellow-100 text-yellow-800' :
                            item.status === 'Updated' ? 'bg-green-100 text-green-800' :
                            'bg-blue-100 text-blue-800'
                          }>
                            {item.status}
                          </Badge>
                          <p className="text-sm text-purple-600 mt-1">
                            Next Review: {item.nextReview}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
                
                <Button className="w-full bg-purple-600 hover:bg-purple-700 text-lg h-12">
                  <FileText className="h-5 w-5 mr-2" />
                  Schedule Legal Review
                </Button>
              </CardContent>
            </Card>

            {/* Legacy Giving */}
            <Card className="border-4 border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="text-green-800 text-2xl flex items-center gap-3">
                  <Gift className="h-8 w-8" />
                  Legacy & Charitable Giving
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="p-4 bg-white rounded-lg border-2 border-green-200">
                  <h4 className="text-lg font-bold text-green-800 mb-3">Annual Giving Summary</h4>
                  <div className="space-y-2 text-lg">
                    <div className="flex justify-between">
                      <span>Church Tithe</span>
                      <span className="font-bold">$5,760</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Missions Support</span>
                      <span className="font-bold">$1,200</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Charitable Organizations</span>
                      <span className="font-bold">$800</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Family Support</span>
                      <span className="font-bold">$2,400</span>
                    </div>
                    <div className="flex justify-between font-bold text-green-800 border-t pt-2">
                      <span>Total Annual Giving</span>
                      <span>$10,160</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 bg-white rounded-lg border-2 border-green-200">
                  <h4 className="text-lg font-bold text-green-800 mb-2">Legacy Goals</h4>
                  <ul className="space-y-2 text-green-700">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span>Establish scholarship fund at church</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span>Provide for grandchildren's education</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      <span>Update charitable beneficiaries</span>
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Faith Tab */}
        <TabsContent value="faith" className="space-y-8">
          <Card className="border-4 border-rose-200 bg-rose-50">
            <CardHeader>
              <CardTitle className="text-rose-800 text-2xl flex items-center gap-3">
                <Heart className="h-8 w-8" />
                Faith & Stewardship in Retirement
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="p-6 bg-white rounded-lg border-2 border-rose-200">
                  <h4 className="text-xl font-bold text-rose-800 mb-4">Monthly Giving</h4>
                  <div className="space-y-3 text-lg">
                    <div className="flex justify-between">
                      <span>Church Tithe (15%)</span>
                      <span className="font-bold">$480</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Missions Support</span>
                      <span className="font-bold">$100</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Family Assistance</span>
                      <span className="font-bold">$200</span>
                    </div>
                    <div className="flex justify-between font-bold text-rose-800 border-t pt-3">
                      <span>Total Monthly Giving</span>
                      <span>$780</span>
                    </div>
                  </div>
                </div>
                
                <div className="p-6 bg-white rounded-lg border-2 border-rose-200">
                  <h4 className="text-xl font-bold text-rose-800 mb-4">Giving Progress</h4>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-lg">Annual Giving Goal</span>
                      <span className="text-xl font-bold">105%</span>
                    </div>
                    <Progress value={105} className="h-3" />
                    <p className="text-green-600 text-lg">You've exceeded your giving goal by 5%!</p>
                  </div>
                </div>
              </div>

              <div className="p-6 bg-white rounded-lg border-2 border-rose-200">
                <h4 className="text-xl font-bold text-rose-800 mb-4">🌅 Wisdom for Later Years</h4>
                <blockquote className="italic text-rose-700 border-l-4 border-rose-300 pl-6 text-lg">
                  "Gray hair is a crown of splendor; it is attained in the way of righteousness. 
                  Better a patient person than a warrior, one with self-control than one who takes a city."
                  <footer className="text-lg font-normal mt-3">- Proverbs 16:31-32</footer>
                </blockquote>
                <p className="text-rose-600 mt-4 text-lg">
                  Your years of faithful stewardship are a testimony to God's goodness. 
                  Continue to bless others as you have been blessed, trusting in His provision for all your needs.
                </p>
              </div>

              <div className="p-6 bg-white rounded-lg border-2 border-rose-200">
                <h4 className="text-xl font-bold text-rose-800 mb-4">Ministry Opportunities</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-rose-50 rounded-lg">
                    <h5 className="font-bold text-rose-800">Mentoring Ministry</h5>
                    <p className="text-rose-700">Share your wisdom with younger church members</p>
                  </div>
                  <div className="p-4 bg-rose-50 rounded-lg">
                    <h5 className="font-bold text-rose-800">Prayer Ministry</h5>
                    <p className="text-rose-700">Lead prayer groups and intercession efforts</p>
                  </div>
                  <div className="p-4 bg-rose-50 rounded-lg">
                    <h5 className="font-bold text-rose-800">Hospitality Ministry</h5>
                    <p className="text-rose-700">Open your home for fellowship and study</p>
                  </div>
                  <div className="p-4 bg-rose-50 rounded-lg">
                    <h5 className="font-bold text-rose-800">Legacy Projects</h5>
                    <p className="text-rose-700">Document your faith journey for family</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};