/**
 * Transaction Card Component
 * Displays transaction information with dual categorization and splitting capabilities
 */

import React, { useState } from 'react';
import { format } from 'date-fns';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import { Split, Edit3, DollarSign, Calendar, Building2 } from 'lucide-react';
import { Transaction, PersonaType } from '@/types';
import { TransactionSplitModal } from '@/components/transaction/TransactionSplitModal';
import { cn } from '@/lib/utils';

interface TransactionCardProps {
  transaction: Transaction;
  persona: PersonaType;
  onUpdate?: (transactionId: string, updates: any) => void;
  onSplit?: (transactionId: string, splitData: any) => void;
  className?: string;
}

export const TransactionCard: React.FC<TransactionCardProps> = ({
  transaction,
  persona,
  onUpdate,
  onSplit,
  className
}) => {
  const [showSplitModal, setShowSplitModal] = useState(false);
  
  // Format amount with proper sign
  const formatAmount = (amount: number) => {
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: transaction.iso_currency_code || 'USD',
    }).format(Math.abs(amount));
    
    return amount < 0 ? `-${formatted}` : formatted;
  };

  // Get expense type color
  const getExpenseTypeColor = (expenseType: string) => {
    switch (expenseType) {
      case 'fixed':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'discretionary':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'split':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Get category display name
  const getCategoryDisplay = (category: string) => {
    return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Check if persona can split transactions
  const canSplitTransaction = () => {
    return !['pre_teen', 'teen'].includes(persona) && !transaction.is_split;
  };

  // Get persona-specific styling
  const getPersonaCardStyle = () => {
    switch (persona) {
      case 'pre_teen':
        return 'border-2 border-orange-200 bg-orange-50/50';
      case 'teen':
        return 'border-2 border-blue-200 bg-blue-50/50';
      case 'college_student':
        return 'border border-purple-200 bg-purple-50/30';
      case 'fixed_income':
        return 'border-2 border-green-200 bg-green-50/50 text-lg';
      default:
        return 'border border-gray-200 hover:border-gray-300';
    }
  };

  const handleSplitTransaction = (splitData: any) => {
    if (onSplit) {
      onSplit(transaction.id, splitData);
    }
    setShowSplitModal(false);
  };

  return (
    <Card className={cn(
      'transition-all duration-200 hover:shadow-md',
      getPersonaCardStyle(),
      className
    )}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          {/* Transaction Details */}
          <div className="flex-1 min-w-0">
            {/* Merchant Name */}
            <div className="flex items-center gap-2 mb-2">
              <Building2 className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <h3 className={cn(
                "font-semibold truncate",
                persona === 'fixed_income' ? 'text-lg' : 'text-sm'
              )}>
                {transaction.merchant_name || transaction.name}
              </h3>
            </div>

            {/* Date and Amount */}
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-1 text-muted-foreground">
                <Calendar className="h-3 w-3" />
                <span className={cn(
                  persona === 'fixed_income' ? 'text-base' : 'text-xs'
                )}>
                  {format(new Date(transaction.date), 'MMM dd, yyyy')}
                </span>
              </div>
              
              <div className="flex items-center gap-1">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <span className={cn(
                  "font-bold",
                  transaction.amount > 0 ? 'text-red-600' : 'text-green-600',
                  persona === 'fixed_income' ? 'text-lg' : 'text-sm'
                )}>
                  {formatAmount(transaction.amount)}
                </span>
              </div>
            </div>

            {/* Categories and Expense Type */}
            <div className="flex flex-wrap gap-2 mb-3">
              <Badge 
                variant="outline" 
                className={cn(
                  'text-xs',
                  persona === 'fixed_income' && 'text-sm px-3 py-1'
                )}
              >
                {getCategoryDisplay(transaction.plaid_category)}
              </Badge>
              
              <Badge 
                className={cn(
                  'text-xs border',
                  getExpenseTypeColor(transaction.app_expense_type),
                  persona === 'fixed_income' && 'text-sm px-3 py-1'
                )}
              >
                {transaction.app_expense_type === 'fixed' ? 'Need' : 
                 transaction.app_expense_type === 'discretionary' ? 'Want' : 'Split'}
              </Badge>

              {transaction.is_tithing_income && (
                <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200 text-xs">
                  Tithing Income
                </Badge>
              )}
            </div>

            {/* Split Details */}
            {transaction.is_split && transaction.split_details && (
              <div className="bg-gray-50 rounded-lg p-3 mb-3">
                <p className="text-xs font-medium text-gray-700 mb-2">Split Details:</p>
                <div className="space-y-1">
                  {transaction.split_details.fixed_categories?.map((split, index) => (
                    <div key={`fixed-${index}`} className="flex justify-between text-xs">
                      <span>{getCategoryDisplay(split.category)} (Need)</span>
                      <span className="font-medium">{formatAmount(split.amount)}</span>
                    </div>
                  ))}
                  {transaction.split_details.discretionary_categories?.map((split, index) => (
                    <div key={`discretionary-${index}`} className="flex justify-between text-xs">
                      <span>{getCategoryDisplay(split.category)} (Want)</span>
                      <span className="font-medium">{formatAmount(split.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Notes */}
            {transaction.notes && (
              <p className={cn(
                "text-muted-foreground italic",
                persona === 'fixed_income' ? 'text-base' : 'text-xs'
              )}>
                "{transaction.notes}"
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2 ml-4">
            {canSplitTransaction() && (
              <Dialog open={showSplitModal} onOpenChange={setShowSplitModal}>
                <DialogTrigger asChild>
                  <Button
                    variant="outline"
                    size={persona === 'fixed_income' ? 'default' : 'sm'}
                    className="whitespace-nowrap"
                  >
                    <Split className="h-3 w-3 mr-1" />
                    Split
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <TransactionSplitModal
                    transaction={transaction}
                    onSplit={handleSplitTransaction}
                    onCancel={() => setShowSplitModal(false)}
                  />
                </DialogContent>
              </Dialog>
            )}

            {/* Edit button for advanced personas */}
            {!['pre_teen', 'teen'].includes(persona) && (
              <Button
                variant="ghost"
                size={persona === 'fixed_income' ? 'default' : 'sm'}
                onClick={() => onUpdate?.(transaction.id, {})}
              >
                <Edit3 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        {/* Biblical Stewardship Insight for Pre-Teen/Teen */}
        {['pre_teen', 'teen'].includes(persona) && transaction.app_expense_type && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
            <p className="text-sm text-blue-800">
              {transaction.app_expense_type === 'fixed' 
                ? '💡 This is a "need" - something we must have to live well.'
                : '🎯 This is a "want" - something nice to have but not essential.'
              }
            </p>
            {persona === 'pre_teen' && (
              <p className="text-xs text-blue-600 mt-1">
                "In everything, do to others as you would have them do to you." - Matthew 7:12
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};