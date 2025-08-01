/**
 * Tithing Context - Complete tithing calculation, tracking, and church integration
 * Handles tithe calculations, payment records, church management, and biblical stewardship
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';

export interface TithingRecord {
  id: string;
  amount: number;
  date: string;
  source: 'salary' | 'bonus' | 'gift' | 'allowance' | 'side_income' | 'investment' | 'other';
  sourceDescription?: string;
  paymentMethod: 'cash' | 'check' | 'online' | 'automatic' | 'bank_transfer';
  churchId?: string;
  ministryId?: string;
  notes?: string;
  status: 'pending' | 'completed' | 'processed' | 'acknowledged';
  receiptUrl?: string;
  taxDeductible: boolean;
}

export interface Church {
  id: string;
  name: string;
  address: string;
  phone?: string;
  email?: string;
  website?: string;
  pastor?: string;
  denomination?: string;
  bankingInfo?: {
    accountName: string;
    accountNumber: string;
    routingNumber: string;
    bankName: string;
  };
  onlineGiving?: {
    enabled: boolean;
    url?: string;
    methods: ('credit_card' | 'bank_transfer' | 'paypal' | 'venmo')[];
  };
  isActive: boolean;
}

export interface Ministry {
  id: string;
  churchId: string;
  name: string;
  description: string;
  category: 'missions' | 'youth' | 'children' | 'music' | 'outreach' | 'building' | 'general';
  targetAmount?: number;
  currentAmount: number;
  endDate?: string;
  isActive: boolean;
}

export interface GivingGoal {
  id: string;
  title: string;
  description: string;
  targetAmount: number;
  currentAmount: number;
  frequency: 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  startDate: string;
  endDate: string;
  category: 'tithe' | 'offering' | 'missions' | 'building' | 'special';
  churchId?: string;
  ministryId?: string;
  autoContribute: {
    enabled: boolean;
    amount: number;
    frequency: 'weekly' | 'monthly';
    nextDate?: string;
  };
}

export interface TithingSettings {
  tithingPercentage: number; // Default 10%
  calculationBase: 'gross' | 'net' | 'custom';
  frequency: 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  autoCalculate: boolean;
  includeBonuses: boolean;
  includeGifts: boolean;
  includeInvestments: boolean;
  defaultChurch?: string;
  defaultPaymentMethod: 'cash' | 'check' | 'online' | 'automatic';
  reminders: {
    enabled: boolean;
    frequency: 'weekly' | 'monthly';
    dayOfWeek?: number; // 0-6 for Sunday-Saturday
    dayOfMonth?: number; // 1-31
    advanceDays: number;
  };
  taxSettings: {
    trackForTaxes: boolean;
    generateYearEndReport: boolean;
    includedCategories: string[];
  };
}

export interface TithingReport {
  period: string;
  startDate: string;
  endDate: string;
  totalIncome: number;
  totalTithed: number;
  tithingPercentage: number;
  variance: number; // Difference from target percentage
  categories: {
    category: string;
    income: number;
    tithed: number;
    percentage: number;
  }[];
  churches: {
    churchId: string;
    churchName: string;
    amount: number;
    percentage: number;
  }[];
  taxDeductibleTotal: number;
  upcomingCommitments: number;
  recommendations: string[];
}

interface TithingContextType {
  // Records Management
  tithingRecords: TithingRecord[];
  addTithingRecord: (record: Omit<TithingRecord, 'id'>) => Promise<string>;
  updateTithingRecord: (recordId: string, updates: Partial<TithingRecord>) => Promise<void>;
  deleteTithingRecord: (recordId: string) => Promise<void>;
  
  // Church Management
  churches: Church[];
  activeChurch: Church | null;
  addChurch: (church: Omit<Church, 'id'>) => Promise<string>;
  updateChurch: (churchId: string, updates: Partial<Church>) => Promise<void>;
  setActiveChurch: (churchId: string) => Promise<void>;
  
  // Ministry Management
  ministries: Ministry[];
  addMinistry: (ministry: Omit<Ministry, 'id'>) => Promise<string>;
  updateMinistry: (ministryId: string, updates: Partial<Ministry>) => Promise<void>;
  contributeToMinistry: (ministryId: string, amount: number) => Promise<void>;
  
  // Goals & Planning
  givingGoals: GivingGoal[];
  createGivingGoal: (goal: Omit<GivingGoal, 'id'>) => Promise<string>;
  updateGivingGoal: (goalId: string, updates: Partial<GivingGoal>) => Promise<void>;
  contributeToGoal: (goalId: string, amount: number) => Promise<void>;
  
  // Calculations
  calculateTithe: (income: number, percentage?: number) => number;
  calculateMonthlyTithe: () => number;
  calculateYearlyTithe: () => number;
  getTithingRecommendation: (income: number) => { amount: number; breakdown: any };
  
  // Settings
  settings: TithingSettings;
  updateSettings: (settings: Partial<TithingSettings>) => Promise<void>;
  
  // Reports & Analytics
  getCurrentPeriodReport: () => Promise<TithingReport>;
  getYearlyTaxReport: (year: number) => Promise<any>;
  exportTithingData: (format: 'csv' | 'pdf', year?: number) => Promise<string>;
  
  // Reminders & Automation
  getUpcomingReminders: () => Promise<any[]>;
  processAutoContributions: () => Promise<void>;
  sendTithingReminder: (type: 'weekly' | 'monthly' | 'goal') => Promise<void>;
  
  // Utilities
  getTotalTithedThisMonth: () => number;
  getTotalTithedYTD: () => number;
  getTithingStreak: () => number;
  getGivingInsights: () => Promise<string[]>;
  
  // State
  loading: boolean;
  error: string | null;
  nextTithingDue: string | null;
  monthlyTithingTarget: number;
}

const TithingContext = createContext<TithingContextType | undefined>(undefined);

// Default settings
const getDefaultSettings = (): TithingSettings => ({
  tithingPercentage: 10,
  calculationBase: 'gross',
  frequency: 'monthly',
  autoCalculate: true,
  includeBonuses: true,
  includeGifts: false,
  includeInvestments: false,
  defaultPaymentMethod: 'check',
  reminders: {
    enabled: true,
    frequency: 'monthly',
    dayOfMonth: 1,
    advanceDays: 3
  },
  taxSettings: {
    trackForTaxes: true,
    generateYearEndReport: true,
    includedCategories: ['tithe', 'offering', 'missions']
  }
});

export const TithingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  
  // State
  const [tithingRecords, setTithingRecords] = useState<TithingRecord[]>([]);
  const [churches, setChurches] = useState<Church[]>([]);
  const [activeChurch, setActiveChurchState] = useState<Church | null>(null);
  const [ministries, setMinistries] = useState<Ministry[]>([]);
  const [givingGoals, setGivingGoals] = useState<GivingGoal[]>([]);
  const [settings, setSettings] = useState<TithingSettings>(getDefaultSettings());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextTithingDue, setNextTithingDue] = useState<string | null>(null);
  const [monthlyTithingTarget, setMonthlyTithingTarget] = useState(0);

  // Initialize tithing data
  useEffect(() => {
    if (user) {
      loadTithingData();
    }
  }, [user]);

  const loadTithingData = async () => {
    try {
      setLoading(true);
      
      const tithingData = localStorage.getItem(`tithing_${user?.sub}`);
      if (tithingData) {
        const data = JSON.parse(tithingData);
        setTithingRecords(data.records || []);
        setChurches(data.churches || []);
        setActiveChurchState(data.activeChurch || null);
        setMinistries(data.ministries || []);
        setGivingGoals(data.goals || []);
        setSettings({ ...getDefaultSettings(), ...data.settings });
      } else {
        // Initialize with default church
        const defaultChurch: Church = {
          id: `church-${Date.now()}`,
          name: 'My Church',
          address: '',
          isActive: true
        };
        setChurches([defaultChurch]);
        setActiveChurchState(defaultChurch);
      }
    } catch (err) {
      setError('Failed to load tithing data');
    } finally {
      setLoading(false);
    }
  };

  const saveTithingData = useCallback(() => {
    if (user) {
      localStorage.setItem(`tithing_${user.sub}`, JSON.stringify({
        records: tithingRecords,
        churches,
        activeChurch,
        ministries,
        goals: givingGoals,
        settings,
        updatedAt: new Date().toISOString()
      }));
    }
  }, [tithingRecords, churches, activeChurch, ministries, givingGoals, settings, user]);

  useEffect(() => {
    saveTithingData();
  }, [saveTithingData]);

  // Records Management
  const addTithingRecord = async (recordData: Omit<TithingRecord, 'id'>): Promise<string> => {
    try {
      const newRecord: TithingRecord = {
        ...recordData,
        id: `tithe-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };

      setTithingRecords(prev => [...prev, newRecord]);
      
      // Update ministry if specified
      if (recordData.ministryId) {
        await contributeToMinistry(recordData.ministryId, recordData.amount);
      }

      return newRecord.id;
    } catch (err) {
      setError('Failed to add tithing record');
      throw err;
    }
  };

  const updateTithingRecord = async (recordId: string, updates: Partial<TithingRecord>) => {
    setTithingRecords(prev => 
      prev.map(record => 
        record.id === recordId 
          ? { ...record, ...updates }
          : record
      )
    );
  };

  const deleteTithingRecord = async (recordId: string) => {
    setTithingRecords(prev => prev.filter(record => record.id !== recordId));
  };

  // Church Management
  const addChurch = async (churchData: Omit<Church, 'id'>): Promise<string> => {
    const newChurch: Church = {
      ...churchData,
      id: `church-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    };

    setChurches(prev => [...prev, newChurch]);
    return newChurch.id;
  };

  const updateChurch = async (churchId: string, updates: Partial<Church>) => {
    setChurches(prev => 
      prev.map(church => 
        church.id === churchId 
          ? { ...church, ...updates }
          : church
      )
    );
  };

  const setActiveChurch = async (churchId: string) => {
    const church = churches.find(c => c.id === churchId);
    if (church) {
      setActiveChurchState(church);
    }
  };

  // Ministry Management
  const addMinistry = async (ministryData: Omit<Ministry, 'id'>): Promise<string> => {
    const newMinistry: Ministry = {
      ...ministryData,
      id: `ministry-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    };

    setMinistries(prev => [...prev, newMinistry]);
    return newMinistry.id;
  };

  const updateMinistry = async (ministryId: string, updates: Partial<Ministry>) => {
    setMinistries(prev => 
      prev.map(ministry => 
        ministry.id === ministryId 
          ? { ...ministry, ...updates }
          : ministry
      )
    );
  };

  const contributeToMinistry = async (ministryId: string, amount: number) => {
    const ministry = ministries.find(m => m.id === ministryId);
    if (ministry) {
      await updateMinistry(ministryId, {
        currentAmount: ministry.currentAmount + amount
      });
    }
  };

  // Goals & Planning
  const createGivingGoal = async (goalData: Omit<GivingGoal, 'id'>): Promise<string> => {
    const newGoal: GivingGoal = {
      ...goalData,
      id: `goal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    };

    setGivingGoals(prev => [...prev, newGoal]);
    return newGoal.id;
  };

  const updateGivingGoal = async (goalId: string, updates: Partial<GivingGoal>) => {
    setGivingGoals(prev => 
      prev.map(goal => 
        goal.id === goalId 
          ? { ...goal, ...updates }
          : goal
      )
    );
  };

  const contributeToGoal = async (goalId: string, amount: number) => {
    const goal = givingGoals.find(g => g.id === goalId);
    if (goal) {
      await updateGivingGoal(goalId, {
        currentAmount: goal.currentAmount + amount
      });
    }
  };

  // Calculations
  const calculateTithe = (income: number, percentage?: number): number => {
    const rate = percentage || settings.tithingPercentage;
    return Math.round((income * rate / 100) * 100) / 100;
  };

  const calculateMonthlyTithe = (): number => {
    // Mock calculation based on assumed monthly income
    const estimatedMonthlyIncome = 5000; // This would come from actual income tracking
    return calculateTithe(estimatedMonthlyIncome);
  };

  const calculateYearlyTithe = (): number => {
    return calculateMonthlyTithe() * 12;
  };

  const getTithingRecommendation = (income: number) => {
    const titheAmount = calculateTithe(income);
    return {
      amount: titheAmount,
      breakdown: {
        church: titheAmount * 0.8,
        missions: titheAmount * 0.15,
        special: titheAmount * 0.05
      }
    };
  };

  // Settings
  const updateSettings = async (newSettings: Partial<TithingSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  // Reports & Analytics
  const getCurrentPeriodReport = async (): Promise<TithingReport> => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    const monthlyRecords = tithingRecords.filter(record => 
      record.date.startsWith(currentMonth)
    );

    const totalTithed = monthlyRecords.reduce((sum, record) => sum + record.amount, 0);
    const estimatedIncome = 5000; // Mock - would come from actual income tracking
    const tithingPercentage = (totalTithed / estimatedIncome) * 100;

    return {
      period: currentMonth,
      startDate: `${currentMonth}-01`,
      endDate: new Date().toISOString(),
      totalIncome: estimatedIncome,
      totalTithed,
      tithingPercentage,
      variance: tithingPercentage - settings.tithingPercentage,
      categories: [
        {
          category: 'Salary',
          income: estimatedIncome * 0.8,
          tithed: totalTithed * 0.8,
          percentage: 10
        },
        {
          category: 'Bonus',
          income: estimatedIncome * 0.2,
          tithed: totalTithed * 0.2,
          percentage: 10
        }
      ],
      churches: churches.map(church => ({
        churchId: church.id,
        churchName: church.name,
        amount: totalTithed, // Simplified - would calculate per church
        percentage: 100
      })),
      taxDeductibleTotal: monthlyRecords
        .filter(record => record.taxDeductible)
        .reduce((sum, record) => sum + record.amount, 0),
      upcomingCommitments: givingGoals
        .filter(goal => goal.autoContribute.enabled)
        .reduce((sum, goal) => sum + goal.autoContribute.amount, 0),
      recommendations: [
        'Consider setting up automatic monthly tithing',
        'Track your giving goals progress regularly',
        'Review tax-deductible giving options'
      ]
    };
  };

  const getYearlyTaxReport = async (year: number) => {
    const yearRecords = tithingRecords.filter(record => 
      record.date.startsWith(year.toString()) && record.taxDeductible
    );

    return {
      year,
      totalDeductible: yearRecords.reduce((sum, record) => sum + record.amount, 0),
      records: yearRecords,
      churchBreakdown: churches.map(church => ({
        churchName: church.name,
        amount: yearRecords
          .filter(record => record.churchId === church.id)
          .reduce((sum, record) => sum + record.amount, 0)
      }))
    };
  };

  const exportTithingData = async (format: 'csv' | 'pdf', year?: number): Promise<string> => {
    // Mock implementation
    const filename = `tithing-report-${year || new Date().getFullYear()}.${format}`;
    return filename;
  };

  // Reminders & Automation
  const getUpcomingReminders = async () => {
    return [
      {
        id: 'monthly-tithe',
        type: 'monthly',
        title: 'Monthly Tithe Reminder',
        dueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        amount: calculateMonthlyTithe()
      }
    ];
  };

  const processAutoContributions = async () => {
    const autoGoals = givingGoals.filter(goal => 
      goal.autoContribute.enabled && 
      goal.autoContribute.nextDate && 
      new Date(goal.autoContribute.nextDate) <= new Date()
    );

    for (const goal of autoGoals) {
      await contributeToGoal(goal.id, goal.autoContribute.amount);
      
      // Update next contribution date
      const nextDate = new Date();
      if (goal.autoContribute.frequency === 'weekly') {
        nextDate.setDate(nextDate.getDate() + 7);
      } else {
        nextDate.setMonth(nextDate.getMonth() + 1);
      }
      
      await updateGivingGoal(goal.id, {
        autoContribute: {
          ...goal.autoContribute,
          nextDate: nextDate.toISOString()
        }
      });
    }
  };

  const sendTithingReminder = async (type: 'weekly' | 'monthly' | 'goal') => {
    // Mock implementation - would integrate with notification system
    console.log(`Sending ${type} tithing reminder`);
  };

  // Utilities
  const getTotalTithedThisMonth = (): number => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    return tithingRecords
      .filter(record => record.date.startsWith(currentMonth))
      .reduce((sum, record) => sum + record.amount, 0);
  };

  const getTotalTithedYTD = (): number => {
    const currentYear = new Date().getFullYear().toString();
    return tithingRecords
      .filter(record => record.date.startsWith(currentYear))
      .reduce((sum, record) => sum + record.amount, 0);
  };

  const getTithingStreak = (): number => {
    // Calculate consecutive months with tithing
    let streak = 0;
    const now = new Date();
    
    for (let i = 0; i < 12; i++) {
      const checkDate = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const monthStr = checkDate.toISOString().slice(0, 7);
      
      const monthlyTotal = tithingRecords
        .filter(record => record.date.startsWith(monthStr))
        .reduce((sum, record) => sum + record.amount, 0);
        
      if (monthlyTotal > 0) {
        streak++;
      } else {
        break;
      }
    }
    
    return streak;
  };

  const getGivingInsights = async (): Promise<string[]> => {
    const insights = [];
    const monthlyTotal = getTotalTithedThisMonth();
    const target = calculateMonthlyTithe();
    
    if (monthlyTotal >= target) {
      insights.push('🎉 You\'ve met your monthly tithing goal!');
    } else {
      insights.push(`💡 You need $${(target - monthlyTotal).toFixed(2)} more to reach your monthly goal`);
    }
    
    const streak = getTithingStreak();
    if (streak >= 3) {
      insights.push(`🔥 Amazing! You have a ${streak}-month giving streak!`);
    }
    
    return insights;
  };

  const contextValue: TithingContextType = {
    // Records
    tithingRecords,
    addTithingRecord,
    updateTithingRecord,
    deleteTithingRecord,
    
    // Churches
    churches,
    activeChurch,
    addChurch,
    updateChurch,
    setActiveChurch,
    
    // Ministries
    ministries,
    addMinistry,
    updateMinistry,
    contributeToMinistry,
    
    // Goals
    givingGoals,
    createGivingGoal,
    updateGivingGoal,
    contributeToGoal,
    
    // Calculations
    calculateTithe,
    calculateMonthlyTithe,
    calculateYearlyTithe,
    getTithingRecommendation,
    
    // Settings
    settings,
    updateSettings,
    
    // Reports
    getCurrentPeriodReport,
    getYearlyTaxReport,
    exportTithingData,
    
    // Reminders
    getUpcomingReminders,
    processAutoContributions,
    sendTithingReminder,
    
    // Utilities
    getTotalTithedThisMonth,
    getTotalTithedYTD,
    getTithingStreak,
    getGivingInsights,
    
    // State
    loading,
    error,
    nextTithingDue,
    monthlyTithingTarget
  };

  return (
    <TithingContext.Provider value={contextValue}>
      {children}
    </TithingContext.Provider>
  );
};

export const useTithing = (): TithingContextType => {
  const context = useContext(TithingContext);
  if (!context) {
    throw new Error('useTithing must be used within a TithingProvider');
  }
  return context;
};