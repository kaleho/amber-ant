/**
 * Emergency Fund Card Component
 * Displays savings goal progress with persona-specific recommendations
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Shield, Target, Plus, TrendingUp, AlertCircle } from 'lucide-react';
import { SavingsGoal, PersonaType } from '@/types';
import { cn } from '@/lib/utils';

interface EmergencyFundCardProps {
  goal: SavingsGoal;
  persona: PersonaType;
  onAddFunds?: () => void;
  onUpdateGoal?: () => void;
  className?: string;
}

export const EmergencyFundCard: React.FC<EmergencyFundCardProps> = ({
  goal,
  persona,
  onAddFunds,
  onUpdateGoal,
  className
}) => {
  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  // Get persona-specific recommendations
  const getPersonaRecommendations = () => {
    switch (persona) {
      case 'pre_teen':
        return {
          targetMonths: 1,
          description: 'Save for small emergencies like replacing lost school supplies',
          targetAmount: 100,
          tips: ['Save $5 from each allowance', 'Ask parents about matching contributions']
        };
      case 'teen':
        return {
          targetMonths: 2,
          description: 'Build a small buffer for unexpected expenses',
          targetAmount: 500,
          tips: ['Save 20% of part-time job income', 'Use birthday money wisely']
        };
      case 'college_student':
        return {
          targetMonths: 2,
          description: 'Cover unexpected costs during college',
          targetAmount: 1000,
          tips: ['Start with $25/month', 'Use refund money wisely']
        };
      case 'single_parent':
        return {
          targetMonths: 9,
          description: 'Enhanced security for family protection',
          targetAmount: 25000,
          tips: ['Priority #1 after basic needs', 'Consider automatic transfers']
        };
      case 'fixed_income':
        return {
          targetMonths: 6,
          description: 'Medical emergency and income protection',
          targetAmount: 15000,
          tips: ['Focus on healthcare costs', 'Consider high-yield savings']
        };
      default:
        return {
          targetMonths: 6,
          description: '3-6 months of living expenses',
          targetAmount: 15000,
          tips: ['Start with $1000 minimum', 'Automate your savings']
        };
    }
  };

  // Get progress status
  const getProgressStatus = () => {
    const percentage = goal.progress_percentage;
    if (percentage >= 100) return { status: 'complete', color: 'text-green-600', icon: Target };
    if (percentage >= 75) return { status: 'excellent', color: 'text-blue-600', icon: TrendingUp };
    if (percentage >= 50) return { status: 'good', color: 'text-purple-600', icon: TrendingUp };
    if (percentage >= 25) return { status: 'started', color: 'text-yellow-600', icon: TrendingUp };
    return { status: 'needs_attention', color: 'text-red-600', icon: AlertCircle };
  };

  // Get persona-specific styling
  const getPersonaCardStyle = () => {
    switch (persona) {
      case 'pre_teen':
        return 'border-2 border-orange-300 bg-gradient-to-br from-orange-100 to-yellow-100';
      case 'teen':
        return 'border-2 border-blue-300 bg-gradient-to-br from-blue-100 to-cyan-100';
      case 'college_student':
        return 'border border-purple-300 bg-gradient-to-br from-purple-100 to-pink-100';
      case 'single_parent':
        return 'border-2 border-pink-300 bg-gradient-to-br from-pink-100 to-rose-100';
      case 'fixed_income':
        return 'border-2 border-green-300 bg-gradient-to-br from-green-100 to-emerald-100';
      default:
        return 'border border-blue-300 bg-gradient-to-br from-blue-100 to-indigo-100';
    }
  };

  const recommendations = getPersonaRecommendations();
  const progressStatus = getProgressStatus();
  const StatusIcon = progressStatus.icon;

  return (
    <Card className={cn(
      'transition-all duration-300 hover:shadow-lg',
      getPersonaCardStyle(),
      className
    )}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className={cn(
              'text-blue-600',
              persona === 'fixed_income' ? 'h-6 w-6' : 'h-5 w-5'
            )} />
            <CardTitle className={cn(
              'font-bold',
              persona === 'fixed_income' ? 'text-xl' : 'text-lg'
            )}>
              {goal.name}
            </CardTitle>
          </div>
          
          <Badge 
            className={cn(
              'bg-blue-100 text-blue-800 border-blue-200',
              persona === 'fixed_income' && 'text-sm px-3 py-1'
            )}
          >
            Emergency Fund
          </Badge>
        </div>
        
        {goal.description && (
          <p className={cn(
            'text-muted-foreground',
            persona === 'fixed_income' ? 'text-base' : 'text-sm'
          )}>
            {goal.description}
          </p>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress Overview */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <StatusIcon className={cn('h-4 w-4', progressStatus.color)} />
              <span className={cn(
                'font-medium',
                progressStatus.color,
                persona === 'fixed_income' ? 'text-base' : 'text-sm'
              )}>
                {Math.round(goal.progress_percentage)}% Complete
              </span>
            </div>
            
            <span className={cn(
              'font-bold text-gray-900',
              persona === 'fixed_income' ? 'text-lg' : 'text-base'
            )}>
              {formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}
            </span>
          </div>
          
          <Progress 
            value={goal.progress_percentage} 
            className={cn(
              'h-3 bg-gray-200',
              persona === 'fixed_income' && 'h-4'
            )}
            indicatorClassName="bg-gradient-to-r from-blue-500 to-green-500"
          />
          
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Remaining: {formatCurrency(goal.target_amount - goal.current_amount)}</span>
            {goal.target_date && (
              <span>Target: {new Date(goal.target_date).toLocaleDateString()}</span>
            )}
          </div>
        </div>

        {/* Persona-Specific Recommendations */}
        <div className={cn(
          'p-4 rounded-lg border',
          persona === 'pre_teen' ? 'bg-orange-50 border-orange-200' :
          persona === 'teen' ? 'bg-blue-50 border-blue-200' :
          persona === 'college_student' ? 'bg-purple-50 border-purple-200' :
          persona === 'single_parent' ? 'bg-pink-50 border-pink-200' :
          persona === 'fixed_income' ? 'bg-green-50 border-green-200' :
          'bg-blue-50 border-blue-200'
        )}>
          <h4 className={cn(
            'font-semibold mb-2',
            persona === 'fixed_income' ? 'text-base' : 'text-sm'
          )}>
            💡 Recommended for {persona.replace('_', ' ')}:
          </h4>
          
          <div className="space-y-2">
            <p className={cn(
              'text-gray-700',
              persona === 'fixed_income' ? 'text-base' : 'text-sm'
            )}>
              {recommendations.description}
            </p>
            
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="text-xs">
                {recommendations.targetMonths} months expenses
              </Badge>
              <Badge variant="outline" className="text-xs">
                Target: {formatCurrency(recommendations.targetAmount)}
              </Badge>
            </div>
            
            <div className="space-y-1">
              {recommendations.tips.map((tip, index) => (
                <p key={index} className={cn(
                  'text-gray-600',
                  persona === 'fixed_income' ? 'text-sm' : 'text-xs'
                )}>
                  • {tip}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          {onAddFunds && (
            <Button 
              onClick={onAddFunds}
              className={cn(
                'flex-1 bg-green-600 hover:bg-green-700',
                persona === 'fixed_income' && 'text-base py-3'
              )}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Funds
            </Button>
          )}
          
          {onUpdateGoal && !['pre_teen'].includes(persona) && (
            <Button 
              variant="outline"
              onClick={onUpdateGoal}
              className={persona === 'fixed_income' ? 'text-base py-3' : ''}
            >
              Update Goal
            </Button>
          )}
        </div>

        {/* Biblical Wisdom */}
        {['pre_teen', 'teen', 'single_parent'].includes(persona) && (
          <div className="p-3 bg-white/70 rounded-lg border border-gray-200">
            <p className={cn(
              'text-gray-800 font-medium mb-1',
              persona === 'fixed_income' ? 'text-base' : 'text-sm'
            )}>
              🙏 Biblical Wisdom:
            </p>
            <p className={cn(
              'text-gray-700 italic',
              persona === 'fixed_income' ? 'text-sm' : 'text-xs'
            )}>
              {persona === 'pre_teen' && '"The wise store up choice food and olive oil, but fools gulp theirs down." - Proverbs 21:20'}
              {persona === 'teen' && '"Go to the ant, you sluggard; consider its ways and be wise!" - Proverbs 6:6'}
              {persona === 'single_parent' && '"She is clothed with strength and dignity; she can laugh at the days to come." - Proverbs 31:25'}
            </p>
          </div>
        )}

        {/* Completion Celebration */}
        {goal.is_completed && (
          <div className="p-4 bg-green-100 border border-green-300 rounded-lg text-center">
            <div className="text-2xl mb-2">🎉</div>
            <p className="font-bold text-green-800">Congratulations!</p>
            <p className="text-green-700 text-sm">
              You've reached your emergency fund goal! Your financial security is stronger.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};