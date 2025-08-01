/**
 * Budget Context - Comprehensive budget management system
 * Handles budget creation, tracking, alerts, category management, and goal integration
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';

export interface BudgetCategory {
  id: string;
  name: string;
  description?: string;
  budgetedAmount: number;
  spentAmount: number;
  period: 'weekly' | 'monthly' | 'yearly';
  startDate: string;
  endDate: string;
  color: string;
  icon?: string;
  isActive: boolean;
  parentCategoryId?: string;
  subcategories?: string[];
  tags: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  rollover: boolean; // Whether unused budget rolls over to next period
  alerts: {
    at50Percent: boolean;
    at75Percent: boolean;
    at90Percent: boolean;
    at100Percent: boolean;
    customAlerts: { percentage: number; message: string; enabled: boolean }[];
  };
}

export interface BudgetGoal {
  id: string;
  title: string;
  description: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  milestones: {
    percentage: number;
    amount: number;
    reached: boolean;
    date?: string;
    celebration?: string;
  }[];
  linkedBudgetCategories: string[];
  autoContribution: {
    enabled: boolean;
    amount: number;
    frequency: 'weekly' | 'monthly';
    sourceCategory?: string;
  };
}

export interface BudgetAlert {
  id: string;
  type: 'warning' | 'info' | 'success' | 'error';
  title: string;
  message: string;
  categoryId?: string;
  goalId?: string;
  threshold: number;
  triggered: boolean;
  dismissible: boolean;
  actionRequired: boolean;
  suggestedActions: string[];
  createdAt: string;
  dismissedAt?: string;
}

export interface BudgetTransaction {
  id: string;
  amount: number;
  description: string;
  categoryId: string;
  subcategoryId?: string;
  date: string;
  tags: string[];
  notes?: string;
  recurring?: {
    frequency: 'weekly' | 'monthly' | 'yearly';
    nextDate: string;
    endDate?: string;
    count?: number;
  };
  splits?: {
    categoryId: string;
    amount: number;
    percentage: number;
  }[];
}

export interface BudgetReport {
  period: string;
  totalBudgeted: number;
  totalSpent: number;
  variance: number;
  categories: {
    categoryId: string;
    name: string;
    budgeted: number;
    spent: number;
    variance: number;
    percentage: number;
  }[];
  trends: {
    category: string;
    trend: 'increasing' | 'decreasing' | 'stable';
    percentage: number;
  }[];
  insights: string[];
  recommendations: string[];
}

interface BudgetContextType {
  // Categories
  categories: BudgetCategory[];
  activeCategories: BudgetCategory[];
  createCategory: (category: Omit<BudgetCategory, 'id'>) => Promise<string>;
  updateCategory: (categoryId: string, updates: Partial<BudgetCategory>) => Promise<void>;
  deleteCategory: (categoryId: string) => Promise<void>;
  duplicateCategory: (categoryId: string, newName: string) => Promise<string>;
  
  // Goals
  goals: BudgetGoal[];
  activeGoals: BudgetGoal[];
  createGoal: (goal: Omit<BudgetGoal, 'id'>) => Promise<string>;
  updateGoal: (goalId: string, updates: Partial<BudgetGoal>) => Promise<void>;
  deleteGoal: (goalId: string) => Promise<void>;
  contributeToGoal: (goalId: string, amount: number) => Promise<void>;
  checkMilestones: (goalId: string) => Promise<void>;
  
  // Transactions
  transactions: BudgetTransaction[];
  addTransaction: (transaction: Omit<BudgetTransaction, 'id'>) => Promise<string>;
  updateTransaction: (transactionId: string, updates: Partial<BudgetTransaction>) => Promise<void>;
  deleteTransaction: (transactionId: string) => Promise<void>;
  categorizeTransaction: (transactionId: string, categoryId: string, subcategoryId?: string) => Promise<void>;
  splitTransaction: (transactionId: string, splits: { categoryId: string; amount: number }[]) => Promise<void>;
  
  // Alerts & Monitoring
  alerts: BudgetAlert[];
  activeAlerts: BudgetAlert[];
  checkBudgetAlerts: () => Promise<void>;
  dismissAlert: (alertId: string) => Promise<void>;
  createCustomAlert: (categoryId: string, threshold: number, message: string) => Promise<void>;
  
  // Reporting & Analytics
  getCurrentPeriodReport: () => Promise<BudgetReport>;
  getHistoricalReport: (startDate: string, endDate: string) => Promise<BudgetReport>;
  getCategoryTrends: (categoryId: string, months: number) => Promise<any>;
  exportBudgetData: (format: 'csv' | 'pdf' | 'excel') => Promise<string>;
  
  // Budget Planning
  createBudgetFromTemplate: (templateName: string) => Promise<void>;
  copyBudgetFromPeriod: (sourcePeriod: string) => Promise<void>;
  suggestBudgetAdjustments: () => Promise<string[]>;
  forecastBudget: (months: number) => Promise<any>;
  
  // Utilities
  getRemainingBudget: (categoryId: string) => number;
  getBudgetUtilization: (categoryId: string) => number;
  getMonthlyBurnRate: (categoryId: string) => number;
  getDaysUntilBudgetExhausted: (categoryId: string) => number;
  
  // State
  loading: boolean;
  error: string | null;
  currentPeriod: string;
  totalBudgeted: number;
  totalSpent: number;
}

const BudgetContext = createContext<BudgetContextType | undefined>(undefined);

// Default budget categories
const getDefaultCategories = (): Omit<BudgetCategory, 'id'>[] => [
  {
    name: 'Housing',
    description: 'Rent, mortgage, utilities, maintenance',
    budgetedAmount: 1500,
    spentAmount: 0,
    period: 'monthly',
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    color: '#3B82F6',
    icon: 'Home',
    isActive: true,
    tags: ['essential', 'fixed'],
    priority: 'critical',
    rollover: false,
    alerts: {
      at50Percent: false,
      at75Percent: true,
      at90Percent: true,
      at100Percent: true,
      customAlerts: []
    }
  },
  {
    name: 'Food & Dining',
    description: 'Groceries, restaurants, takeout',
    budgetedAmount: 600,
    spentAmount: 0,
    period: 'monthly',
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    color: '#10B981',
    icon: 'ShoppingCart',
    isActive: true,
    tags: ['essential', 'variable'],
    priority: 'high',
    rollover: false,
    alerts: {
      at50Percent: false,
      at75Percent: true,
      at90Percent: true,
      at100Percent: true,
      customAlerts: []
    }
  },
  {
    name: 'Transportation',
    description: 'Gas, public transport, car maintenance',
    budgetedAmount: 300,
    spentAmount: 0,
    period: 'monthly',
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    color: '#F59E0B',
    icon: 'Car',
    isActive: true,
    tags: ['essential', 'variable'],
    priority: 'high',
    rollover: true,
    alerts: {
      at50Percent: false,
      at75Percent: true,
      at90Percent: true,
      at100Percent: true,
      customAlerts: []
    }
  },
  {
    name: 'Entertainment',
    description: 'Movies, games, hobbies, subscriptions',
    budgetedAmount: 200,
    spentAmount: 0,
    period: 'monthly',
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    color: '#8B5CF6',
    icon: 'Gamepad',
    isActive: true,
    tags: ['discretionary', 'flexible'],
    priority: 'medium',
    rollover: true,
    alerts: {
      at50Percent: false,
      at75Percent: false,
      at90Percent: true,
      at100Percent: true,
      customAlerts: []
    }
  },
  {
    name: 'Healthcare',
    description: 'Medical expenses, insurance, prescriptions',
    budgetedAmount: 250,
    spentAmount: 0,
    period: 'monthly',
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    color: '#EF4444',
    icon: 'Heart',
    isActive: true,
    tags: ['essential', 'unpredictable'],
    priority: 'critical',
    rollover: true,
    alerts: {
      at50Percent: true,
      at75Percent: true,
      at90Percent: true,
      at100Percent: true,
      customAlerts: []
    }
  },
  {
    name: 'Giving & Tithing',
    description: 'Church tithe, charitable donations',
    budgetedAmount: 500,
    spentAmount: 0,
    period: 'monthly',
    startDate: new Date().toISOString(),
    endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
    color: '#EC4899',
    icon: 'Heart',
    isActive: true,
    tags: ['giving', 'spiritual'],
    priority: 'high',
    rollover: false,
    alerts: {
      at50Percent: false,
      at75Percent: false,
      at90Percent: false,
      at100Percent: false,
      customAlerts: []
    }
  }
];

export const BudgetProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  
  // State
  const [categories, setCategories] = useState<BudgetCategory[]>([]);
  const [goals, setGoals] = useState<BudgetGoal[]>([]);
  const [transactions, setTransactions] = useState<BudgetTransaction[]>([]);
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPeriod, setCurrentPeriod] = useState(new Date().toISOString().slice(0, 7)); // YYYY-MM

  // Initialize budget data
  useEffect(() => {
    if (user) {
      loadBudgetData();
    }
  }, [user]);

  const loadBudgetData = async () => {
    try {
      setLoading(true);
      
      const budgetData = localStorage.getItem(`budget_${user?.sub}`);
      if (budgetData) {
        const data = JSON.parse(budgetData);
        setCategories(data.categories || []);
        setGoals(data.goals || []);
        setTransactions(data.transactions || []);
        setAlerts(data.alerts || []);
      } else {
        // Initialize with default categories
        const defaultCats = getDefaultCategories().map((cat, index) => ({
          ...cat,
          id: `category-${Date.now()}-${index}`
        }));
        setCategories(defaultCats);
      }
    } catch (err) {
      setError('Failed to load budget data');
    } finally {
      setLoading(false);
    }
  };

  const saveBudgetData = useCallback(() => {
    if (user) {
      localStorage.setItem(`budget_${user.sub}`, JSON.stringify({
        categories,
        goals,
        transactions,
        alerts,
        updatedAt: new Date().toISOString()
      }));
    }
  }, [categories, goals, transactions, alerts, user]);

  useEffect(() => {
    saveBudgetData();
  }, [saveBudgetData]);

  // Computed values
  const activeCategories = categories.filter(cat => cat.isActive);
  const activeGoals = goals.filter(goal => new Date(goal.targetDate) > new Date());
  const activeAlerts = alerts.filter(alert => !alert.dismissedAt);
  const totalBudgeted = activeCategories.reduce((sum, cat) => sum + cat.budgetedAmount, 0);
  const totalSpent = activeCategories.reduce((sum, cat) => sum + cat.spentAmount, 0);

  // Category Management
  const createCategory = async (categoryData: Omit<BudgetCategory, 'id'>): Promise<string> => {
    try {
      setLoading(true);
      
      const newCategory: BudgetCategory = {
        ...categoryData,
        id: `category-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };

      setCategories(prev => [...prev, newCategory]);
      return newCategory.id;
    } catch (err) {
      setError('Failed to create category');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateCategory = async (categoryId: string, updates: Partial<BudgetCategory>) => {
    try {
      setCategories(prev => 
        prev.map(cat => 
          cat.id === categoryId 
            ? { ...cat, ...updates }
            : cat
        )
      );
    } catch (err) {
      setError('Failed to update category');
    }
  };

  const deleteCategory = async (categoryId: string) => {
    try {
      setCategories(prev => prev.filter(cat => cat.id !== categoryId));
      // Also remove related transactions and alerts
      setTransactions(prev => prev.filter(tx => tx.categoryId !== categoryId));
      setAlerts(prev => prev.filter(alert => alert.categoryId !== categoryId));
    } catch (err) {
      setError('Failed to delete category');
    }
  };

  const duplicateCategory = async (categoryId: string, newName: string): Promise<string> => {
    const original = categories.find(cat => cat.id === categoryId);
    if (!original) throw new Error('Category not found');

    return await createCategory({
      ...original,
      name: newName,
      spentAmount: 0
    });
  };

  // Goal Management
  const createGoal = async (goalData: Omit<BudgetGoal, 'id'>): Promise<string> => {
    try {
      const newGoal: BudgetGoal = {
        ...goalData,
        id: `goal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };

      setGoals(prev => [...prev, newGoal]);
      return newGoal.id;
    } catch (err) {
      setError('Failed to create goal');
      throw err;
    }
  };

  const updateGoal = async (goalId: string, updates: Partial<BudgetGoal>) => {
    setGoals(prev => 
      prev.map(goal => 
        goal.id === goalId 
          ? { ...goal, ...updates }
          : goal
      )
    );
  };

  const deleteGoal = async (goalId: string) => {
    setGoals(prev => prev.filter(goal => goal.id !== goalId));
  };

  const contributeToGoal = async (goalId: string, amount: number) => {
    const goal = goals.find(g => g.id === goalId);
    if (!goal) return;

    await updateGoal(goalId, {
      currentAmount: goal.currentAmount + amount
    });

    await checkMilestones(goalId);
  };

  const checkMilestones = async (goalId: string) => {
    const goal = goals.find(g => g.id === goalId);
    if (!goal) return;

    const updatedMilestones = goal.milestones.map(milestone => {
      if (!milestone.reached && goal.currentAmount >= milestone.amount) {
        return {
          ...milestone,
          reached: true,
          date: new Date().toISOString()
        };
      }
      return milestone;
    });

    await updateGoal(goalId, { milestones: updatedMilestones });
  };

  // Transaction Management
  const addTransaction = async (transactionData: Omit<BudgetTransaction, 'id'>): Promise<string> => {
    try {
      const newTransaction: BudgetTransaction = {
        ...transactionData,
        id: `transaction-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };

      setTransactions(prev => [...prev, newTransaction]);

      // Update category spent amount
      await updateCategory(transactionData.categoryId, {
        spentAmount: (categories.find(c => c.id === transactionData.categoryId)?.spentAmount || 0) + transactionData.amount
      });

      // Check for alerts
      await checkBudgetAlerts();

      return newTransaction.id;
    } catch (err) {
      setError('Failed to add transaction');
      throw err;
    }
  };

  const updateTransaction = async (transactionId: string, updates: Partial<BudgetTransaction>) => {
    const originalTransaction = transactions.find(tx => tx.id === transactionId);
    if (!originalTransaction) return;

    // If amount or category changed, update category totals
    if (updates.amount !== undefined || updates.categoryId !== undefined) {
      // Remove from old category
      const oldCategory = categories.find(c => c.id === originalTransaction.categoryId);
      if (oldCategory) {
        await updateCategory(oldCategory.id, {
          spentAmount: oldCategory.spentAmount - originalTransaction.amount
        });
      }

      // Add to new category
      const newCategoryId = updates.categoryId || originalTransaction.categoryId;
      const newAmount = updates.amount || originalTransaction.amount;
      const newCategory = categories.find(c => c.id === newCategoryId);
      if (newCategory) {
        await updateCategory(newCategory.id, {
          spentAmount: newCategory.spentAmount + newAmount
        });
      }
    }

    setTransactions(prev => 
      prev.map(tx => 
        tx.id === transactionId 
          ? { ...tx, ...updates }
          : tx
      )
    );
  };

  const deleteTransaction = async (transactionId: string) => {
    const transaction = transactions.find(tx => tx.id === transactionId);
    if (!transaction) return;

    // Update category spent amount
    const category = categories.find(c => c.id === transaction.categoryId);
    if (category) {
      await updateCategory(category.id, {
        spentAmount: category.spentAmount - transaction.amount
      });
    }

    setTransactions(prev => prev.filter(tx => tx.id !== transactionId));
  };

  const categorizeTransaction = async (transactionId: string, categoryId: string, subcategoryId?: string) => {
    await updateTransaction(transactionId, { categoryId, subcategoryId });
  };

  const splitTransaction = async (transactionId: string, splits: { categoryId: string; amount: number }[]) => {
    await updateTransaction(transactionId, {
      splits: splits.map(split => ({
        ...split,
        percentage: (split.amount / splits.reduce((sum, s) => sum + s.amount, 0)) * 100
      }))
    });
  };

  // Alert Management
  const checkBudgetAlerts = async () => {
    const newAlerts: BudgetAlert[] = [];

    categories.forEach(category => {
      const utilization = (category.spentAmount / category.budgetedAmount) * 100;
      const alerts = category.alerts;

      if (alerts.at50Percent && utilization >= 50 && !alerts.customAlerts.some(a => a.percentage === 50)) {
        newAlerts.push({
          id: `alert-${Date.now()}-${category.id}-50`,
          type: 'info',
          title: 'Budget 50% Used',
          message: `You've used 50% of your ${category.name} budget.`,
          categoryId: category.id,
          threshold: 50,
          triggered: true,
          dismissible: true,
          actionRequired: false,
          suggestedActions: ['Review recent spending', 'Consider adjusting budget'],
          createdAt: new Date().toISOString()
        });
      }

      if (alerts.at75Percent && utilization >= 75) {
        newAlerts.push({
          id: `alert-${Date.now()}-${category.id}-75`,
          type: 'warning',
          title: 'Budget 75% Used',
          message: `You've used 75% of your ${category.name} budget. Consider slowing spending.`,
          categoryId: category.id,
          threshold: 75,
          triggered: true,
          dismissible: true,
          actionRequired: false,
          suggestedActions: ['Reduce spending', 'Find alternatives', 'Increase budget'],
          createdAt: new Date().toISOString()
        });
      }

      if (alerts.at90Percent && utilization >= 90) {
        newAlerts.push({
          id: `alert-${Date.now()}-${category.id}-90`,
          type: 'warning',
          title: 'Budget 90% Used',
          message: `You've used 90% of your ${category.name} budget. Action needed!`,
          categoryId: category.id,
          threshold: 90,
          triggered: true,
          dismissible: true,
          actionRequired: true,
          suggestedActions: ['Stop spending in this category', 'Transfer from another budget', 'Increase budget'],
          createdAt: new Date().toISOString()
        });
      }

      if (alerts.at100Percent && utilization >= 100) {
        newAlerts.push({
          id: `alert-${Date.now()}-${category.id}-100`,
          type: 'error',
          title: 'Budget Exceeded',
          message: `You've exceeded your ${category.name} budget by $${(category.spentAmount - category.budgetedAmount).toFixed(2)}.`,
          categoryId: category.id,
          threshold: 100,
          triggered: true,
          dismissible: false,
          actionRequired: true,
          suggestedActions: ['Review overspending', 'Adjust budget', 'Reduce other categories'],
          createdAt: new Date().toISOString()
        });
      }
    });

    setAlerts(prev => [...prev, ...newAlerts]);
  };

  const dismissAlert = async (alertId: string) => {
    setAlerts(prev => 
      prev.map(alert => 
        alert.id === alertId 
          ? { ...alert, dismissedAt: new Date().toISOString() }
          : alert
      )
    );
  };

  const createCustomAlert = async (categoryId: string, threshold: number, message: string) => {
    const category = categories.find(c => c.id === categoryId);
    if (!category) return;

    const updatedAlerts = {
      ...category.alerts,
      customAlerts: [
        ...category.alerts.customAlerts,
        { percentage: threshold, message, enabled: true }
      ]
    };

    await updateCategory(categoryId, { alerts: updatedAlerts });
  };

  // Reports & Analytics
  const getCurrentPeriodReport = async (): Promise<BudgetReport> => {
    const variance = totalBudgeted - totalSpent;
    
    return {
      period: currentPeriod,
      totalBudgeted,
      totalSpent,
      variance,
      categories: categories.map(cat => ({
        categoryId: cat.id,
        name: cat.name,
        budgeted: cat.budgetedAmount,
        spent: cat.spentAmount,
        variance: cat.budgetedAmount - cat.spentAmount,
        percentage: (cat.spentAmount / cat.budgetedAmount) * 100
      })),
      trends: categories.map(cat => ({
        category: cat.name,
        trend: Math.random() > 0.5 ? 'increasing' : 'decreasing',
        percentage: Math.random() * 20 - 10
      })),
      insights: [
        'You are spending 15% less on entertainment compared to last month',
        'Food expenses are trending upward this quarter',
        'Transportation costs are well within budget'
      ],
      recommendations: [
        'Consider increasing your emergency fund allocation',
        'Review subscription services in entertainment category',
        'Set up automatic savings transfers'
      ]
    };
  };

  const getHistoricalReport = async (startDate: string, endDate: string): Promise<BudgetReport> => {
    // Mock implementation
    return getCurrentPeriodReport();
  };

  const getCategoryTrends = async (categoryId: string, months: number) => {
    // Mock implementation
    return {
      categoryId,
      months,
      data: Array.from({ length: months }, (_, i) => ({
        month: new Date(Date.now() - i * 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 7),
        budgeted: Math.random() * 1000,
        spent: Math.random() * 800
      }))
    };
  };

  const exportBudgetData = async (format: 'csv' | 'pdf' | 'excel'): Promise<string> => {
    // Mock implementation
    return `budget-export-${Date.now()}.${format}`;
  };

  // Utility Functions
  const getRemainingBudget = (categoryId: string): number => {
    const category = categories.find(c => c.id === categoryId);
    return category ? category.budgetedAmount - category.spentAmount : 0;
  };

  const getBudgetUtilization = (categoryId: string): number => {
    const category = categories.find(c => c.id === categoryId);
    return category ? (category.spentAmount / category.budgetedAmount) * 100 : 0;
  };

  const getMonthlyBurnRate = (categoryId: string): number => {
    const category = categories.find(c => c.id === categoryId);
    if (!category) return 0;
    
    const daysPassed = Math.ceil((new Date().getTime() - new Date(category.startDate).getTime()) / (1000 * 60 * 60 * 24));
    return daysPassed > 0 ? category.spentAmount / daysPassed * 30 : 0;
  };

  const getDaysUntilBudgetExhausted = (categoryId: string): number => {
    const category = categories.find(c => c.id === categoryId);
    if (!category) return 0;
    
    const remaining = getRemainingBudget(categoryId);
    const dailyBurnRate = getMonthlyBurnRate(categoryId) / 30;
    
    return dailyBurnRate > 0 ? Math.floor(remaining / dailyBurnRate) : Infinity;
  };

  // Planning Functions
  const createBudgetFromTemplate = async (templateName: string) => {
    const templates = {
      'conservative': getDefaultCategories(),
      'aggressive-saver': getDefaultCategories().map(cat => ({ ...cat, budgetedAmount: cat.budgetedAmount * 0.8 })),
      'family': getDefaultCategories().concat([
        {
          name: 'Children',
          description: 'Childcare, education, activities',
          budgetedAmount: 800,
          spentAmount: 0,
          period: 'monthly' as const,
          startDate: new Date().toISOString(),
          endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          color: '#F59E0B',
          isActive: true,
          tags: ['family', 'essential'],
          priority: 'high' as const,
          rollover: false,
          alerts: {
            at50Percent: false,
            at75Percent: true,
            at90Percent: true,
            at100Percent: true,
            customAlerts: []
          }
        }
      ])
    };

    const template = templates[templateName as keyof typeof templates];
    if (template) {
      const newCategories = template.map((cat, index) => ({
        ...cat,
        id: `category-${Date.now()}-${index}`
      }));
      setCategories(newCategories);
    }
  };

  const copyBudgetFromPeriod = async (sourcePeriod: string) => {
    // Mock implementation - copy categories from previous period
    const newCategories = categories.map(cat => ({
      ...cat,
      id: `category-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      spentAmount: 0,
      startDate: new Date().toISOString(),
      endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
    }));
    
    setCategories(newCategories);
  };

  const suggestBudgetAdjustments = async (): Promise<string[]> => {
    const suggestions: string[] = [];
    
    categories.forEach(category => {
      const utilization = getBudgetUtilization(category.id);
      
      if (utilization > 100) {
        suggestions.push(`Increase ${category.name} budget by $${(category.spentAmount - category.budgetedAmount).toFixed(2)}`);
      } else if (utilization < 50) {
        suggestions.push(`Consider reducing ${category.name} budget by $${((category.budgetedAmount - category.spentAmount) * 0.5).toFixed(2)}`);
      }
    });
    
    return suggestions;
  };

  const forecastBudget = async (months: number) => {
    return {
      months,
      projectedSpending: categories.map(cat => ({
        categoryId: cat.id,
        name: cat.name,
        monthlyProjection: getMonthlyBurnRate(cat.id),
        totalProjection: getMonthlyBurnRate(cat.id) * months
      }))
    };
  };

  const contextValue: BudgetContextType = {
    // Categories
    categories,
    activeCategories,
    createCategory,
    updateCategory,
    deleteCategory,
    duplicateCategory,
    
    // Goals
    goals,
    activeGoals,
    createGoal,
    updateGoal,
    deleteGoal,
    contributeToGoal,
    checkMilestones,
    
    // Transactions
    transactions,
    addTransaction,
    updateTransaction,
    deleteTransaction,
    categorizeTransaction,
    splitTransaction,
    
    // Alerts
    alerts,
    activeAlerts,
    checkBudgetAlerts,
    dismissAlert,
    createCustomAlert,
    
    // Reports
    getCurrentPeriodReport,
    getHistoricalReport,
    getCategoryTrends,
    exportBudgetData,
    
    // Planning
    createBudgetFromTemplate,
    copyBudgetFromPeriod,
    suggestBudgetAdjustments,
    forecastBudget,
    
    // Utilities
    getRemainingBudget,
    getBudgetUtilization,
    getMonthlyBurnRate,
    getDaysUntilBudgetExhausted,
    
    // State
    loading,
    error,
    currentPeriod,
    totalBudgeted,
    totalSpent
  };

  return (
    <BudgetContext.Provider value={contextValue}>
      {children}
    </BudgetContext.Provider>
  );
};

export const useBudget = (): BudgetContextType => {
  const context = useContext(BudgetContext);
  if (!context) {
    throw new Error('useBudget must be used within a BudgetProvider');
  }
  return context;
};