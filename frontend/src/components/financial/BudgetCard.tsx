/**
 * Budget Card Component
 * Displays budget information with progress tracking and persona-specific styling
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TrendingUp, TrendingDown, AlertTriangle, Target, Edit3 } from 'lucide-react';
import { Budget, PersonaType } from '@/types';
import { cn } from '@/lib/utils';

interface BudgetCardProps {
  budget: Budget;
  persona: PersonaType;
  onEdit?: (budgetId: string) => void;
  className?: string;
}

export const BudgetCard: React.FC<BudgetCardProps> = ({
  budget,
  persona,
  onEdit,
  className
}) => {
  // Calculate budget progress
  const progressPercentage = budget.total_budget > 0 
    ? (budget.total_spent / budget.total_budget) * 100 
    : 0;
  
  const isOverBudget = progressPercentage > 100;
  const isNearLimit = progressPercentage > 80 && !isOverBudget;

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  // Get progress color based on percentage
  const getProgressColor = () => {
    if (isOverBudget) return 'bg-red-500';
    if (isNearLimit) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // Get status icon and message
  const getStatusInfo = () => {
    if (isOverBudget) {
      return {
        icon: <AlertTriangle className="h-4 w-4 text-red-600" />,
        message: 'Over budget',
        color: 'text-red-600'
      };
    }
    if (isNearLimit) {
      return {
        icon: <TrendingUp className="h-4 w-4 text-yellow-600" />,
        message: 'Near limit',
        color: 'text-yellow-600'
      };
    }
    return {
      icon: <Target className="h-4 w-4 text-green-600" />,
      message: 'On track',
      color: 'text-green-600'
    };
  };

  // Get persona-specific styling
  const getPersonaCardStyle = () => {
    switch (persona) {
      case 'pre_teen':
        return 'border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-yellow-50';
      case 'teen':
        return 'border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-purple-50';
      case 'college_student':
        return 'border border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50';
      case 'fixed_income':
        return 'border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50';
      case 'single_parent':
        return 'border-2 border-pink-200 bg-gradient-to-br from-pink-50 to-rose-50';
      default:
        return 'border border-gray-200 bg-gradient-to-br from-gray-50 to-slate-50 hover:shadow-lg';
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <Card className={cn(
      'transition-all duration-300 hover:shadow-md',
      getPersonaCardStyle(),
      className
    )}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className={cn(
          'font-semibold',
          persona === 'fixed_income' ? 'text-lg' : 'text-base'
        )}>
          {budget.name}
        </CardTitle>
        
        <div className="flex items-center gap-2">
          <Badge 
            variant="outline"
            className={cn(
              'capitalize',
              persona === 'fixed_income' ? 'text-sm px-3 py-1' : 'text-xs'
            )}
          >
            {budget.period}
          </Badge>
          
          {onEdit && !['pre_teen'].includes(persona) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(budget.id)}
              className="h-8 w-8 p-0"
            >
              <Edit3 className="h-3 w-3" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Budget Overview */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className={cn(
              'text-muted-foreground',
              persona === 'fixed_income' ? 'text-base' : 'text-sm'
            )}>
              Total Budget
            </span>
            <span className={cn(
              'font-bold',
              persona === 'fixed_income' ? 'text-lg' : 'text-base'
            )}>
              {formatCurrency(budget.total_budget)}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className={cn(
              'text-muted-foreground',
              persona === 'fixed_income' ? 'text-base' : 'text-sm'
            )}>
              Spent
            </span>
            <span className={cn(
              'font-bold',
              isOverBudget ? 'text-red-600' : 'text-gray-900',
              persona === 'fixed_income' ? 'text-lg' : 'text-base'
            )}>
              {formatCurrency(budget.total_spent)}
            </span>
          </div>
          
          <div className="flex items-center justify-between">
            <span className={cn(
              'text-muted-foreground',
              persona === 'fixed_income' ? 'text-base' : 'text-sm'
            )}>
              Remaining
            </span>
            <span className={cn(
              'font-bold',
              (budget.total_budget - budget.total_spent) < 0 ? 'text-red-600' : 'text-green-600',
              persona === 'fixed_income' ? 'text-lg' : 'text-base'
            )}>
              {formatCurrency(budget.total_budget - budget.total_spent)}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {statusInfo.icon}
              <span className={cn(
                'font-medium',
                statusInfo.color,
                persona === 'fixed_income' ? 'text-base' : 'text-sm'
              )}>
                {statusInfo.message}
              </span>
            </div>
            <span className={cn(
              'font-bold',
              statusInfo.color,
              persona === 'fixed_income' ? 'text-base' : 'text-sm'
            )}>
              {Math.round(progressPercentage)}%
            </span>
          </div>
          
          <Progress 
            value={Math.min(progressPercentage, 100)} 
            className={cn(
              'h-2',
              persona === 'fixed_income' && 'h-3'
            )}
            indicatorClassName={getProgressColor()}
          />
        </div>

        {/* Category Breakdown */}
        <div className="space-y-2">
          <h4 className={cn(
            'font-medium text-muted-foreground',
            persona === 'fixed_income' ? 'text-base' : 'text-sm'
          )}>
            Categories ({budget.categories.length})
          </h4>
          
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {budget.categories.map((category, index) => {
              const categoryProgress = category.budgeted_amount > 0 
                ? (category.spent_amount / category.budgeted_amount) * 100 
                : 0;
              
              return (
                <div key={index} className="flex items-center justify-between text-xs bg-white/50 rounded p-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <Badge 
                      variant="outline"
                      className={cn(
                        'text-xs capitalize',
                        category.expense_type === 'fixed' 
                          ? 'bg-blue-50 text-blue-700 border-blue-200'
                          : 'bg-purple-50 text-purple-700 border-purple-200'
                      )}
                    >
                      {category.expense_type === 'fixed' ? 'Need' : 'Want'}
                    </Badge>
                    <span className="truncate capitalize">
                      {category.category.replace(/_/g, ' ')}
                    </span>
                  </div>
                  
                  <div className="text-right ml-2">
                    <div className="font-medium">
                      {formatCurrency(category.spent_amount)} / {formatCurrency(category.budgeted_amount)}
                    </div>
                    <div className={cn(
                      'text-xs',
                      categoryProgress > 100 ? 'text-red-600' : 'text-gray-500'
                    )}>
                      {Math.round(categoryProgress)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Biblical Insight for Young Personas */}
        {['pre_teen', 'teen'].includes(persona) && (
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <p className={cn(
              'text-blue-800 font-medium',
              persona === 'pre_teen' ? 'text-sm' : 'text-xs'
            )}>
              💡 Budgeting Wisdom:
            </p>
            <p className={cn(
              'text-blue-700 mt-1',
              persona === 'pre_teen' ? 'text-sm' : 'text-xs'
            )}>
              {persona === 'pre_teen' 
                ? '"Plans fail for lack of counsel, but with many advisers they succeed." - Proverbs 15:22'
                : '"The plans of the diligent lead to profit as surely as haste leads to poverty." - Proverbs 21:5'
              }
            </p>
          </div>
        )}

        {/* Emergency Alert for Single Parent */}
        {persona === 'single_parent' && isOverBudget && (
          <div className="p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <p className="text-red-800 font-medium text-sm">
                Budget exceeded - consider priority adjustments
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};