/**
 * Transaction Split Modal Component (Web Version)
 * Advanced transaction splitting interface with dual categorization
 * Supports splitting between fixed (needs) and discretionary (wants) expenses
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Plus, 
  Minus, 
  DollarSign, 
  PieChart, 
  AlertTriangle,
  CheckCircle,
  X
} from 'lucide-react';

interface Transaction {
  id: string;
  amount: number;
  description: string;
  category?: string;
  date: string;
}

interface SplitDetails {
  categoryId: string;
  categoryName: string;
  amount: number;
  percentage: number;
  expenseType: 'need' | 'want';
}

interface TransactionSplitModalProps {
  isVisible: boolean;
  transaction: Transaction | null;
  onClose: () => void;
  onSplit: (splits: SplitDetails[]) => void;
  availableCategories: Array<{
    id: string;
    name: string;
    type: 'need' | 'want';
    color: string;
  }>;
}

export const TransactionSplitModal: React.FC<TransactionSplitModalProps> = ({
  isVisible,
  transaction,
  onClose,
  onSplit,
  availableCategories = []
}) => {
  const [splits, setSplits] = useState<SplitDetails[]>([]);
  const [totalAllocated, setTotalAllocated] = useState(0);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // Initialize splits when transaction changes
  useEffect(() => {
    if (transaction && splits.length === 0) {
      // Start with one empty split
      setSplits([{
        categoryId: '',
        categoryName: '',
        amount: transaction.amount,
        percentage: 100,
        expenseType: 'need'
      }]);
    }
  }, [transaction]);

  // Calculate total allocated amount
  useEffect(() => {
    const total = splits.reduce((sum, split) => sum + split.amount, 0);
    setTotalAllocated(total);
  }, [splits]);

  const addSplit = () => {
    if (splits.length < 10) { // Limit to 10 splits
      setSplits([...splits, {
        categoryId: '',
        categoryName: '',
        amount: 0,
        percentage: 0,
        expenseType: 'need'
      }]);
    }
  };

  const removeSplit = (index: number) => {
    if (splits.length > 1) {
      setSplits(splits.filter((_, i) => i !== index));
    }
  };

  const updateSplit = (index: number, field: keyof SplitDetails, value: any) => {
    const updatedSplits = [...splits];
    updatedSplits[index] = { ...updatedSplits[index], [field]: value };

    // If amount changed, recalculate percentage
    if (field === 'amount' && transaction) {
      updatedSplits[index].percentage = (value / transaction.amount) * 100;
    }

    // If category changed, update category name and type
    if (field === 'categoryId') {
      const category = availableCategories.find(cat => cat.id === value);
      if (category) {
        updatedSplits[index].categoryName = category.name;
        updatedSplits[index].expenseType = category.type;
      }
    }

    setSplits(updatedSplits);
  };

  const validateSplits = (): boolean => {
    const errors: string[] = [];

    if (!transaction) {
      errors.push('No transaction selected');
      setValidationErrors(errors);
      return false;
    }

    // Check if all splits have categories
    const emptySplits = splits.filter(split => !split.categoryId);
    if (emptySplits.length > 0) {
      errors.push('All splits must have a category selected');
    }

    // Check if total equals transaction amount
    const totalDiff = Math.abs(totalAllocated - transaction.amount);
    if (totalDiff > 0.01) {
      errors.push(`Total splits (${totalAllocated.toFixed(2)}) must equal transaction amount (${transaction.amount.toFixed(2)})`);
    }

    // Check for negative amounts
    const negativeSplits = splits.filter(split => split.amount < 0);
    if (negativeSplits.length > 0) {
      errors.push('Split amounts cannot be negative');
    }

    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSplit = () => {
    if (validateSplits()) {
      onSplit(splits);
      onClose();
    }
  };

  const remainingAmount = transaction ? transaction.amount - totalAllocated : 0;
  const isValidSplit = Math.abs(remainingAmount) < 0.01;

  const needsTotal = splits
    .filter(split => split.expenseType === 'need')
    .reduce((sum, split) => sum + split.amount, 0);
  
  const wantsTotal = splits
    .filter(split => split.expenseType === 'want')
    .reduce((sum, split) => sum + split.amount, 0);

  if (!transaction) return null;

  return (
    <Dialog open={isVisible} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PieChart className="w-5 h-5" />
            Split Transaction
          </DialogTitle>
          <DialogDescription>
            Divide this transaction across multiple budget categories and classify as needs vs wants
          </DialogDescription>
        </DialogHeader>

        {/* Transaction Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Transaction Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm font-medium">Description</Label>
                <p className="text-lg">{transaction.description}</p>
              </div>
              <div>
                <Label className="text-sm font-medium">Amount</Label>
                <p className="text-2xl font-bold text-green-600">
                  ${transaction.amount.toFixed(2)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Split Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Split Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <p className="text-sm text-muted-foreground">Needs</p>
                <p className="text-xl font-bold text-blue-600">
                  ${needsTotal.toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground">Wants</p>
                <p className="text-xl font-bold text-purple-600">
                  ${wantsTotal.toFixed(2)}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-muted-foreground">Remaining</p>
                <p className={`text-xl font-bold ${remainingAmount === 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${remainingAmount.toFixed(2)}
                </p>
              </div>
            </div>
            <Progress 
              value={(totalAllocated / transaction.amount) * 100} 
              className="h-2"
            />
          </CardContent>
        </Card>

        {/* Splits */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Split Details</h3>
            <Button 
              onClick={addSplit} 
              variant="outline" 
              size="sm"
              disabled={splits.length >= 10}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Split
            </Button>
          </div>

          {splits.map((split, index) => (
            <Card key={index}>
              <CardContent className="pt-6">
                <div className="grid grid-cols-12 gap-4 items-end">
                  <div className="col-span-4">
                    <Label>Category</Label>
                    <Select 
                      value={split.categoryId} 
                      onValueChange={(value) => updateSplit(index, 'categoryId', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableCategories.map((category) => (
                          <SelectItem key={category.id} value={category.id}>
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-3 h-3 rounded-full" 
                                style={{ backgroundColor: category.color }}
                              />
                              {category.name}
                              <Badge variant={category.type === 'need' ? 'default' : 'secondary'}>
                                {category.type}
                              </Badge>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="col-span-3">
                    <Label>Amount</Label>
                    <div className="relative">
                      <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        type="number"
                        value={split.amount}
                        onChange={(e) => updateSplit(index, 'amount', parseFloat(e.target.value) || 0)}
                        className="pl-10"
                        step="0.01"
                        min="0"
                        max={transaction.amount}
                      />
                    </div>
                  </div>

                  <div className="col-span-2">
                    <Label>Percentage</Label>
                    <div className="flex items-center">
                      <span className="text-sm font-medium">
                        {split.percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <div className="col-span-2">
                    <Badge 
                      variant={split.expenseType === 'need' ? 'default' : 'secondary'}
                      className="w-full justify-center"
                    >
                      {split.expenseType === 'need' ? 'Need' : 'Want'}
                    </Badge>
                  </div>

                  <div className="col-span-1">
                    {splits.length > 1 && (
                      <Button
                        onClick={() => removeSplit(index)}
                        variant="outline"
                        size="sm"
                        className="text-red-600 hover:text-red-700"
                      >
                        <Minus className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <h4 className="font-medium text-red-800">Validation Errors</h4>
                  <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                    {validationErrors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button 
            onClick={handleSplit}
            disabled={!isValidSplit}
            className="min-w-[120px]"
          >
            {isValidSplit ? (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Split Transaction
              </>
            ) : (
              <>
                <AlertTriangle className="w-4 h-4 mr-2" />
                Fix Errors First
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};