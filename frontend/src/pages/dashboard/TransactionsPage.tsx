import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Plus, 
  Search, 
  Filter, 
  Download, 
  TrendingUp, 
  TrendingDown,
  Calendar,
  ArrowUpDown,
  ChevronRight,
  Heart,
  Home,
  Car,
  ShoppingCart,
  Gamepad2
} from 'lucide-react';
import { useBudget } from '@/contexts/BudgetContext';

export const TransactionsPage: React.FC = () => {
  const { transactions, categories } = useBudget();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [dateRange, setDateRange] = useState<string>('30days');

  // Mock transaction data for demonstration
  const mockTransactions = [
    {
      id: '1',
      date: '2024-01-31',
      description: 'Grocery Store - Whole Foods',
      amount: -87.32,
      category: 'Food & Dining',
      budgetCategory: 'food',
      account: 'Chase Checking',
      needsCategory: 'need',
      tags: ['groceries', 'food'],
      status: 'cleared'
    },
    {
      id: '2',
      date: '2024-01-30',
      description: 'Church Tithe',
      amount: -500.00,
      category: 'Giving & Tithing',
      budgetCategory: 'tithing',
      account: 'Chase Checking',
      needsCategory: 'stewardship',
      tags: ['tithe', 'church'],
      status: 'cleared'
    },
    {
      id: '3',
      date: '2024-01-29',
      description: 'Payroll Deposit',
      amount: 2600.00,
      category: 'Income',
      budgetCategory: 'income',
      account: 'Chase Checking',
      needsCategory: 'income',
      tags: ['salary', 'payroll'],
      status: 'cleared'
    },
    {
      id: '4',
      date: '2024-01-28',
      description: 'Gas Station Shell',
      amount: -45.20,
      category: 'Transportation',
      budgetCategory: 'transportation',
      account: 'Chase Checking',
      needsCategory: 'need',
      tags: ['gas', 'transportation'],
      status: 'cleared'
    },
    {
      id: '5',
      date: '2024-01-27',
      description: 'Netflix Subscription',
      amount: -15.99,
      category: 'Entertainment',
      budgetCategory: 'entertainment',
      account: 'Chase Checking',
      needsCategory: 'want',
      tags: ['subscription', 'streaming'],
      status: 'cleared'
    },
    {
      id: '6',
      date: '2024-01-26',
      description: 'Electric Bill - PG&E',
      amount: -120.50,
      category: 'Utilities',
      budgetCategory: 'housing',
      account: 'Chase Checking',
      needsCategory: 'need',
      tags: ['utilities', 'electric'],
      status: 'cleared'
    },
    {
      id: '7',
      date: '2024-01-25',
      description: 'Coffee Shop - Starbucks',
      amount: -12.75,
      category: 'Food & Dining',
      budgetCategory: 'food',
      account: 'Chase Checking',
      needsCategory: 'want',
      tags: ['coffee', 'dining'],
      status: 'cleared'
    },
    {
      id: '8',
      date: '2024-01-24',
      description: 'Pharmacy - CVS',
      amount: -34.99,
      category: 'Healthcare',
      budgetCategory: 'healthcare',
      account: 'Chase Checking',
      needsCategory: 'need',
      tags: ['medicine', 'healthcare'],
      status: 'cleared'
    }
  ];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(Math.abs(amount));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: React.ElementType } = {
      'Food & Dining': ShoppingCart,
      'Transportation': Car,
      'Housing': Home,
      'Entertainment': Gamepad2,
      'Giving & Tithing': Heart,
    };
    return icons[category] || ShoppingCart;
  };

  const getNeedsCategoryColor = (category: string) => {
    const colors = {
      'need': 'bg-green-100 text-green-800',
      'want': 'bg-orange-100 text-orange-800',
      'stewardship': 'bg-purple-100 text-purple-800',
      'income': 'bg-blue-100 text-blue-800'
    };
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const filteredTransactions = mockTransactions.filter(transaction => {
    const matchesSearch = transaction.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         transaction.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || transaction.budgetCategory === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const totalIncome = mockTransactions
    .filter(t => t.amount > 0)
    .reduce((sum, t) => sum + t.amount, 0);
  
  const totalExpenses = mockTransactions
    .filter(t => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Transactions</h1>
          <p className="text-muted-foreground">
            Track your spending with biblical stewardship principles
          </p>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Transaction
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Income</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(totalIncome)}
            </div>
            <p className="text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(totalExpenses)}
            </div>
            <p className="text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Net Cash Flow</CardTitle>
            <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${totalIncome - totalExpenses >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(totalIncome - totalExpenses)}
            </div>
            <p className="text-xs text-muted-foreground">
              This month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters & Search</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search transactions..."
                  className="pl-8"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  <SelectItem value="food">Food & Dining</SelectItem>
                  <SelectItem value="transportation">Transportation</SelectItem>
                  <SelectItem value="housing">Housing</SelectItem>
                  <SelectItem value="entertainment">Entertainment</SelectItem>
                  <SelectItem value="tithing">Giving & Tithing</SelectItem>
                  <SelectItem value="healthcare">Healthcare</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Date Range</label>
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7days">Last 7 days</SelectItem>
                  <SelectItem value="30days">Last 30 days</SelectItem>
                  <SelectItem value="90days">Last 90 days</SelectItem>
                  <SelectItem value="year">This year</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Actions</label>
              <Button variant="outline" className="w-full">
                <Filter className="mr-2 h-4 w-4" />
                More Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transactions List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Transactions</CardTitle>
          <CardDescription>
            {filteredTransactions.length} transactions found
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredTransactions.map((transaction) => {
              const CategoryIcon = getCategoryIcon(transaction.category);
              
              return (
                <div key={transaction.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                  <div className="flex items-center space-x-4">
                    <div className="p-2 bg-muted rounded-full">
                      <CategoryIcon className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col">
                      <span className="font-medium">{transaction.description}</span>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(transaction.date)}</span>
                        <span>•</span>
                        <span>{transaction.account}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="flex flex-col items-center space-y-1">
                      <Badge variant="outline" className="text-xs">
                        {transaction.category}
                      </Badge>
                      <Badge 
                        className={`text-xs ${getNeedsCategoryColor(transaction.needsCategory)}`}
                        variant="secondary"
                      >
                        {transaction.needsCategory}
                      </Badge>
                    </div>

                    <div className="text-right">
                      <div className={`text-lg font-semibold ${
                        transaction.amount > 0 ? 'text-green-600' : 'text-foreground'
                      }`}>
                        {transaction.amount > 0 ? '+' : '-'}{formatCurrency(transaction.amount)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {transaction.status}
                      </div>
                    </div>

                    <Button variant="ghost" size="sm">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Biblical Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Stewardship Insights</CardTitle>
          <CardDescription>
            Biblical perspective on your spending patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="p-4 bg-green-50 rounded-lg">
              <h4 className="font-medium text-green-900 mb-2">Needs vs Wants</h4>
              <p className="text-sm text-green-700">
                {((mockTransactions.filter(t => t.needsCategory === 'need').length / mockTransactions.length) * 100).toFixed(0)}% 
                of your spending is on needs. Great job prioritizing essentials!
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <h4 className="font-medium text-purple-900 mb-2">Faithful Giving</h4>
              <p className="text-sm text-purple-700">
                Your tithing represents {((500 / totalIncome) * 100).toFixed(1)}% of your income. 
                "Honor the Lord with your wealth" - Proverbs 3:9
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};