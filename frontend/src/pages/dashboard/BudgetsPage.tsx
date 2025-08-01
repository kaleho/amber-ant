import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Plus, 
  Edit, 
  Trash2, 
  AlertTriangle, 
  CheckCircle, 
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
  PieChart
} from 'lucide-react';
import { useBudget } from '@/contexts/BudgetContext';

export const BudgetsPage: React.FC = () => {
  const { 
    activeCategories, 
    totalBudgeted, 
    totalSpent, 
    activeAlerts,
    currentPeriod,
    getBudgetUtilization,
    getRemainingBudget,
    getDaysUntilBudgetExhausted
  } = useBudget();

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const getUtilizationColor = (utilization: number) => {
    if (utilization >= 100) return 'text-red-600';
    if (utilization >= 90) return 'text-orange-600';
    if (utilization >= 75) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getProgressColor = (utilization: number) => {
    if (utilization >= 100) return 'bg-red-500';
    if (utilization >= 90) return 'bg-orange-500';
    if (utilization >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getPriorityBadge = (priority: string) => {
    const variants = {
      critical: 'destructive',
      high: 'default',
      medium: 'secondary',
      low: 'outline'
    };
    return variants[priority as keyof typeof variants] || 'outline';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Budget Management</h1>
          <p className="text-muted-foreground">
            Track your spending with biblical stewardship principles for {currentPeriod}
          </p>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Category
          </Button>
          <Button variant="outline">
            <PieChart className="mr-2 h-4 w-4" />
            View Reports
          </Button>
        </div>
      </div>

      {/* Budget Overview */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Budgeted</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalBudgeted)}</div>
            <p className="text-xs text-muted-foreground">
              Across {activeCategories.length} categories
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Spent</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalSpent)}</div>
            <p className="text-xs text-muted-foreground">
              {((totalSpent / totalBudgeted) * 100).toFixed(1)}% of budget
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Remaining</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalBudgeted - totalSpent)}</div>
            <p className="text-xs text-muted-foreground">
              Available to spend
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              Budget Alerts ({activeAlerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {activeAlerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="flex items-start justify-between p-3 bg-white rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-orange-900">{alert.title}</h4>
                    <p className="text-sm text-orange-700">{alert.message}</p>
                  </div>
                  <Button size="sm" variant="ghost" className="text-orange-600">
                    Dismiss
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Budget Categories */}
      <Card>
        <CardHeader>
          <CardTitle>Budget Categories</CardTitle>
          <CardDescription>
            Manage your spending categories with biblical priorities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activeCategories.map((category) => {
              const utilization = getBudgetUtilization(category.id);
              const remaining = getRemainingBudget(category.id);
              const daysLeft = getDaysUntilBudgetExhausted(category.id);
              
              return (
                <div key={category.id} className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-lg">{category.name}</h3>
                        <Badge variant={getPriorityBadge(category.priority)}>
                          {category.priority}
                        </Badge>
                        {category.tags.includes('giving') && (
                          <Badge variant="outline" className="text-purple-600 border-purple-600">
                            Giving
                          </Badge>
                        )}
                      </div>
                      {category.description && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {category.description}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="ghost">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Budgeted:</span>
                        <span className="font-medium">{formatCurrency(category.budgetedAmount)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Spent:</span>
                        <span className="font-medium">{formatCurrency(category.spentAmount)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Remaining:</span>
                        <span className={`font-medium ${remaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(remaining)}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Usage</span>
                        <span className={`text-sm font-medium ${getUtilizationColor(utilization)}`}>
                          {utilization.toFixed(1)}%
                        </span>
                      </div>
                      <Progress 
                        value={Math.min(utilization, 100)} 
                        className="h-2"
                      />
                      {utilization > 100 && (
                        <p className="text-xs text-red-600 flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3" />
                          Over budget by {formatCurrency(category.spentAmount - category.budgetedAmount)}
                        </p>
                      )}
                    </div>

                    <div className="space-y-2">
                      <div className="text-sm">
                        <Calendar className="inline h-3 w-3 mr-1" />
                        Period: {category.period}
                      </div>
                      {daysLeft !== Infinity && daysLeft > 0 && (
                        <div className="text-sm text-muted-foreground">
                          ~{daysLeft} days at current rate
                        </div>
                      )}
                      {category.rollover && (
                        <div className="text-xs text-blue-600">
                          <CheckCircle className="inline h-3 w-3 mr-1" />
                          Unused budget rolls over
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Budget Insights */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Biblical Stewardship Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="p-3 bg-purple-50 rounded-lg">
                <h4 className="font-medium text-purple-900">Tithing & Giving</h4>
                <p className="text-sm text-purple-700">
                  "Honor the Lord with your wealth, with the firstfruits of all your crops" - Proverbs 3:9
                </p>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900">Budget Discipline</h4>
                <p className="text-sm text-blue-700">
                  You're maintaining good spending discipline across most categories
                </p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-900">Emergency Preparedness</h4>
                <p className="text-sm text-green-700">
                  Consider building your emergency fund to cover 3-6 months of expenses
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              <Button variant="outline" className="justify-start">
                <Plus className="mr-2 h-4 w-4" />
                Add New Budget Category
              </Button>
              <Button variant="outline" className="justify-start">
                <TrendingUp className="mr-2 h-4 w-4" />
                Adjust Budget Amounts
              </Button>
              <Button variant="outline" className="justify-start">
                <Calendar className="mr-2 h-4 w-4" />
                Set Budget Alerts
              </Button>
              <Button variant="outline" className="justify-start">
                <PieChart className="mr-2 h-4 w-4" />
                View Detailed Report
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};