/**
 * Dashboard Statistics Component
 * Displays key financial metrics with persona-specific focus
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  Heart, 
  Target,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { PersonaType } from '@/types';
import { cn } from '@/lib/utils';

interface DashboardStatsProps {
  persona: PersonaType;
  stats: {
    totalBalance: number;
    monthlyIncome: number;
    monthlyExpenses: number;
    emergencyFundProgress: number;
    budgetProgress: number;
    tithingPercentage: number;
    savingsRate: number;
  };
  className?: string;
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({
  persona,
  stats,
  className
}) => {
  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  // Format percentage
  const formatPercentage = (percentage: number) => {
    return `${Math.round(percentage)}%`;
  };

  // Get persona-specific stat cards
  const getPersonaStats = () => {
    const baseStats = [
      {
        title: 'Total Balance',
        value: formatCurrency(stats.totalBalance),
        icon: DollarSign,
        color: 'text-blue-600',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200'
      },
      {
        title: 'Monthly Income',
        value: formatCurrency(stats.monthlyIncome),
        icon: TrendingUp,
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200'
      },
      {
        title: 'Monthly Expenses',
        value: formatCurrency(stats.monthlyExpenses),
        icon: TrendingDown,
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200'
      }
    ];

    // Add persona-specific stats
    switch (persona) {
      case 'pre_teen':
        return [
          {
            title: 'Allowance',
            value: formatCurrency(stats.monthlyIncome),
            icon: DollarSign,
            color: 'text-orange-600',
            bgColor: 'bg-orange-50',
            borderColor: 'border-orange-200'
          },
          {
            title: 'Emergency Fund',
            value: formatPercentage(stats.emergencyFundProgress),
            icon: Shield,
            color: 'text-blue-600',
            bgColor: 'bg-blue-50',
            borderColor: 'border-blue-200'
          },
          {
            title: 'Tithing',
            value: formatPercentage(stats.tithingPercentage),
            icon: Heart,
            color: 'text-purple-600',
            bgColor: 'bg-purple-50',
            borderColor: 'border-purple-200'
          }
        ];

      case 'teen':
        return [
          ...baseStats,
          {
            title: 'Savings Goal',
            value: formatPercentage(stats.emergencyFundProgress),
            icon: Target,
            color: 'text-purple-600',
            bgColor: 'bg-purple-50',
            borderColor: 'border-purple-200'
          }
        ];

      case 'college_student':
        return [
          ...baseStats,
          {
            title: 'Budget Progress',
            value: formatPercentage(stats.budgetProgress),
            icon: stats.budgetProgress > 100 ? AlertTriangle : CheckCircle,
            color: stats.budgetProgress > 100 ? 'text-red-600' : 'text-green-600',
            bgColor: stats.budgetProgress > 100 ? 'bg-red-50' : 'bg-green-50',
            borderColor: stats.budgetProgress > 100 ? 'border-red-200' : 'border-green-200'
          }
        ];

      case 'single_parent':
        return [
          ...baseStats,
          {
            title: 'Emergency Fund',
            value: formatPercentage(stats.emergencyFundProgress),
            icon: Shield,
            color: stats.emergencyFundProgress < 50 ? 'text-red-600' : 'text-green-600',
            bgColor: stats.emergencyFundProgress < 50 ? 'bg-red-50' : 'bg-green-50',
            borderColor: stats.emergencyFundProgress < 50 ? 'border-red-200' : 'border-green-200'
          }
        ];

      case 'fixed_income':
        return [
          {
            title: 'Monthly Budget',
            value: formatCurrency(stats.monthlyIncome),
            icon: DollarSign,
            color: 'text-green-600',
            bgColor: 'bg-green-50',
            borderColor: 'border-green-200'
          },
          {
            title: 'Healthcare Fund',
            value: formatPercentage(stats.emergencyFundProgress),
            icon: Shield,
            color: 'text-blue-600',
            bgColor: 'bg-blue-50',
            borderColor: 'border-blue-200'
          },
          {
            title: 'Expenses',
            value: formatCurrency(stats.monthlyExpenses),
            icon: TrendingDown,
            color: 'text-orange-600',
            bgColor: 'bg-orange-50',
            borderColor: 'border-orange-200'
          }
        ];

      default:
        return [
          ...baseStats,
          {
            title: 'Savings Rate',
            value: formatPercentage(stats.savingsRate),
            icon: TrendingUp,
            color: 'text-purple-600',
            bgColor: 'bg-purple-50',
            borderColor: 'border-purple-200'
          }
        ];
    }
  };

  // Get persona-specific grid layout
  const getGridLayout = () => {
    switch (persona) {
      case 'pre_teen':
        return 'grid-cols-1 sm:grid-cols-3';
      case 'teen':
        return 'grid-cols-2 sm:grid-cols-4';
      case 'fixed_income':
        return 'grid-cols-1 sm:grid-cols-3';
      default:
        return 'grid-cols-2 sm:grid-cols-4';
    }
  };

  const personaStats = getPersonaStats();

  return (
    <div className={cn('grid gap-4', getGridLayout(), className)}>
      {personaStats.map((stat, index) => {
        const Icon = stat.icon;
        
        return (
          <Card 
            key={index}
            className={cn(
              'transition-all duration-200 hover:shadow-md border',
              stat.borderColor,
              stat.bgColor
            )}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className={cn(
                'font-medium text-muted-foreground',
                persona === 'fixed_income' ? 'text-base' : 'text-sm'
              )}>
                {stat.title}
              </CardTitle>
              <Icon className={cn(
                'h-4 w-4',
                stat.color,
                persona === 'fixed_income' && 'h-5 w-5'
              )} />
            </CardHeader>
            
            <CardContent>
              <div className={cn(
                'font-bold',
                stat.color,
                persona === 'fixed_income' ? 'text-2xl' : 'text-xl'
              )}>
                {stat.value}
              </div>
              
              {/* Add progress bar for percentage stats */}
              {(stat.title.includes('Fund') || stat.title.includes('Progress') || stat.title.includes('Tithing')) && (
                <div className="mt-2">
                  <Progress 
                    value={
                      stat.title.includes('Fund') ? stats.emergencyFundProgress :
                      stat.title.includes('Progress') ? stats.budgetProgress :
                      stat.title.includes('Tithing') ? stats.tithingPercentage : 0
                    }
                    className={cn(
                      'h-1',
                      persona === 'fixed_income' && 'h-2'
                    )}
                    indicatorClassName={cn(
                      stat.title.includes('Fund') && stats.emergencyFundProgress < 50 ? 'bg-red-500' :
                      stat.title.includes('Progress') && stats.budgetProgress > 100 ? 'bg-red-500' :
                      'bg-current'
                    )}
                  />
                </div>
              )}
              
              {/* Add status badges for certain personas */}
              {persona === 'single_parent' && stat.title === 'Emergency Fund' && (
                <Badge 
                  variant="outline" 
                  className={cn(
                    'mt-2 text-xs',
                    stats.emergencyFundProgress < 50 ? 'border-red-200 text-red-700' : 'border-green-200 text-green-700'
                  )}
                >
                  {stats.emergencyFundProgress < 50 ? 'Priority' : 'On Track'}
                </Badge>
              )}
              
              {['pre_teen', 'teen'].includes(persona) && stat.title === 'Tithing' && (
                <Badge variant="outline" className="mt-2 text-xs border-purple-200 text-purple-700">
                  {stats.tithingPercentage >= 10 ? 'Faithful!' : 'Growing'}
                </Badge>
              )}
            </CardContent>
          </Card>
        );
      })}
      
      {/* Special insights card for certain personas */}
      {persona === 'college_student' && stats.budgetProgress > 90 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <p className="text-sm font-medium text-yellow-800">
                Approaching budget limit
              </p>
            </div>
            <p className="text-xs text-yellow-700 mt-1">
              Consider "ramen mode" for the rest of the month
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};