/**
 * Family Context - Complete family collaboration and permission management
 * Handles family member management, permissions, oversight, and child account coordination
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { useAuth } from './AuthContext';

export interface FamilyMember {
  id: string;
  name: string;
  email?: string;
  role: 'parent' | 'teen' | 'pre_teen' | 'child';
  age: number;
  avatar?: string;
  permissions: FamilyPermissions;
  allowance?: {
    amount: number;
    frequency: 'weekly' | 'monthly';
    lastPaid?: string;
    nextDue?: string;
  };
  chores?: Chore[];
  savings?: {
    balance: number;
    goals: FamilySavingsGoal[];
  };
  restrictions?: {
    maxTransactionAmount: number;
    requiresApproval: boolean;
    blockedCategories: string[];
    allowedCategories: string[];
    spendingLimit: {
      daily: number;
      weekly: number;
      monthly: number;
    };
  };
}

export interface FamilyPermissions {
  canViewFamilyFinances: boolean;
  canMakeTransactions: boolean;
  canViewOwnTransactions: boolean;
  canSetSavingsGoals: boolean;
  canReceiveAllowance: boolean;
  canGiveTithe: boolean;
  maxTransactionAmount: number;
  requiresParentalApproval: boolean;
  canInviteMembers: boolean;
  canManageFamily: boolean;
  canViewReports: boolean;
  canExportData: boolean;
}

export interface Chore {
  id: string;
  title: string;
  description: string;
  value: number;
  frequency: 'daily' | 'weekly' | 'monthly';
  status: 'pending' | 'completed' | 'approved' | 'paid';
  assignedDate: string;
  dueDate: string;
  completedDate?: string;
  approvedBy?: string;
  notes?: string;
}

export interface FamilySavingsGoal {
  id: string;
  title: string;
  description: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  category: string;
  contributors: { memberId: string; amount: number }[];
  milestones: { amount: number; reached: boolean; date?: string }[];
}

export interface FamilyTransaction {
  id: string;
  amount: number;
  description: string;
  category: string;
  date: string;
  memberId: string;
  status: 'pending' | 'approved' | 'rejected';
  approvedBy?: string;
  notes?: string;
  splits?: { memberId: string; amount: number; percentage: number }[];
}

export interface FamilyBudget {
  id: string;
  category: string;
  budgetedAmount: number;
  spentAmount: number;
  period: 'monthly' | 'weekly';
  manager: string; // memberId
  participants: string[]; // memberIds
  alerts: {
    at75Percent: boolean;
    at90Percent: boolean;
    at100Percent: boolean;
  };
}

interface FamilyContextType {
  // Family Management
  familyMembers: FamilyMember[];
  inviteCode: string | null;
  pendingInvitations: any[];
  
  // Member Management
  addFamilyMember: (member: Omit<FamilyMember, 'id'>) => Promise<void>;
  updateFamilyMember: (memberId: string, updates: Partial<FamilyMember>) => Promise<void>;
  removeFamilyMember: (memberId: string) => Promise<void>;
  generateInviteCode: () => Promise<string>;
  
  // Permissions & Oversight
  updateMemberPermissions: (memberId: string, permissions: Partial<FamilyPermissions>) => Promise<void>;
  requestTransactionApproval: (transaction: Omit<FamilyTransaction, 'id'>) => Promise<void>;
  approveTransaction: (transactionId: string, approverId: string, notes?: string) => Promise<void>;
  rejectTransaction: (transactionId: string, approverId: string, reason: string) => Promise<void>;
  
  // Chores & Allowances
  assignChore: (memberId: string, chore: Omit<Chore, 'id'>) => Promise<void>;
  completeChore: (choreId: string, memberId: string, notes?: string) => Promise<void>;
  approveChore: (choreId: string, approverId: string) => Promise<void>;
  payAllowance: (memberId: string) => Promise<void>;
  
  // Family Goals & Budgets
  createFamilyGoal: (goal: Omit<FamilySavingsGoal, 'id'>) => Promise<void>;
  contributeToGoal: (goalId: string, memberId: string, amount: number) => Promise<void>;
  createFamilyBudget: (budget: Omit<FamilyBudget, 'id'>) => Promise<void>;
  updateFamilyBudget: (budgetId: string, updates: Partial<FamilyBudget>) => Promise<void>;
  
  // Notifications & Communication
  sendFamilyMessage: (message: string, recipients: string[]) => Promise<void>;
  getFamilyNotifications: () => Promise<any[]>;
  markNotificationRead: (notificationId: string) => Promise<void>;
  
  // Reports & Analytics
  getFamilySpendingReport: (period: 'weekly' | 'monthly' | 'yearly') => Promise<any>;
  getMemberSpendingReport: (memberId: string, period: 'weekly' | 'monthly' | 'yearly') => Promise<any>;
  exportFamilyData: (format: 'csv' | 'pdf') => Promise<string>;
  
  // State
  loading: boolean;
  error: string | null;
  currentMember: FamilyMember | null;
}

const FamilyContext = createContext<FamilyContextType | undefined>(undefined);

// Default permission templates
const getDefaultPermissions = (role: FamilyMember['role']): FamilyPermissions => {
  switch (role) {
    case 'parent':
      return {
        canViewFamilyFinances: true,
        canMakeTransactions: true,
        canViewOwnTransactions: true,
        canSetSavingsGoals: true,
        canReceiveAllowance: false,
        canGiveTithe: true,
        maxTransactionAmount: 10000,
        requiresParentalApproval: false,
        canInviteMembers: true,
        canManageFamily: true,
        canViewReports: true,
        canExportData: true,
      };
    case 'teen':
      return {
        canViewFamilyFinances: true,
        canMakeTransactions: true,
        canViewOwnTransactions: true,
        canSetSavingsGoals: true,
        canReceiveAllowance: true,
        canGiveTithe: true,
        maxTransactionAmount: 200,
        requiresParentalApproval: true,
        canInviteMembers: false,
        canManageFamily: false,
        canViewReports: false,
        canExportData: false,
      };
    case 'pre_teen':
      return {
        canViewFamilyFinances: false,
        canMakeTransactions: true,
        canViewOwnTransactions: true,
        canSetSavingsGoals: true,
        canReceiveAllowance: true,
        canGiveTithe: true,
        maxTransactionAmount: 50,
        requiresParentalApproval: true,
        canInviteMembers: false,
        canManageFamily: false,
        canViewReports: false,
        canExportData: false,
      };
    case 'child':
      return {
        canViewFamilyFinances: false,
        canMakeTransactions: false,
        canViewOwnTransactions: true,
        canSetSavingsGoals: true,
        canReceiveAllowance: true,
        canGiveTithe: false,
        maxTransactionAmount: 20,
        requiresParentalApproval: true,
        canInviteMembers: false,
        canManageFamily: false,
        canViewReports: false,
        canExportData: false,
      };
    default:
      return getDefaultPermissions('child');
  }
};

export const FamilyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  
  // State
  const [familyMembers, setFamilyMembers] = useState<FamilyMember[]>([]);
  const [inviteCode, setInviteCode] = useState<string | null>(null);
  const [pendingInvitations, setPendingInvitations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentMember, setCurrentMember] = useState<FamilyMember | null>(null);

  // Initialize family data
  useEffect(() => {
    if (user) {
      initializeFamily();
    }
  }, [user]);

  const initializeFamily = async () => {
    try {
      setLoading(true);
      
      // Load existing family or create new one
      const existingFamily = localStorage.getItem(`family_${user?.sub}`);
      if (existingFamily) {
        const familyData = JSON.parse(existingFamily);
        setFamilyMembers(familyData.members || []);
        setCurrentMember(familyData.members?.find((m: FamilyMember) => m.email === user?.email) || null);
      } else {
        // Create initial family with current user as parent
        const initialMember: FamilyMember = {
          id: user?.sub || 'user-1',
          name: user?.name || 'Parent',
          email: user?.email,
          role: 'parent',
          age: 35,
          permissions: getDefaultPermissions('parent'),
          savings: {
            balance: 0,
            goals: []
          }
        };
        
        setFamilyMembers([initialMember]);
        setCurrentMember(initialMember);
        
        // Save to localStorage
        localStorage.setItem(`family_${user?.sub}`, JSON.stringify({
          members: [initialMember],
          inviteCode: null,
          createdAt: new Date().toISOString()
        }));
      }
    } catch (err) {
      setError('Failed to initialize family');
    } finally {
      setLoading(false);
    }
  };

  const saveFamilyData = useCallback(() => {
    if (user) {
      localStorage.setItem(`family_${user.sub}`, JSON.stringify({
        members: familyMembers,
        inviteCode,
        updatedAt: new Date().toISOString()
      }));
    }
  }, [familyMembers, inviteCode, user]);

  useEffect(() => {
    saveFamilyData();
  }, [saveFamilyData]);

  // Member Management
  const addFamilyMember = async (memberData: Omit<FamilyMember, 'id'>) => {
    try {
      setLoading(true);
      
      const newMember: FamilyMember = {
        ...memberData,
        id: `member-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        permissions: memberData.permissions || getDefaultPermissions(memberData.role),
        savings: memberData.savings || { balance: 0, goals: [] },
        chores: memberData.chores || []
      };

      setFamilyMembers(prev => [...prev, newMember]);
    } catch (err) {
      setError('Failed to add family member');
    } finally {
      setLoading(false);
    }
  };

  const updateFamilyMember = async (memberId: string, updates: Partial<FamilyMember>) => {
    try {
      setLoading(true);
      
      setFamilyMembers(prev => 
        prev.map(member => 
          member.id === memberId 
            ? { ...member, ...updates }
            : member
        )
      );

      if (currentMember?.id === memberId) {
        setCurrentMember(prev => prev ? { ...prev, ...updates } : null);
      }
    } catch (err) {
      setError('Failed to update family member');
    } finally {
      setLoading(false);
    }
  };

  const removeFamilyMember = async (memberId: string) => {
    try {
      setLoading(true);
      
      setFamilyMembers(prev => prev.filter(member => member.id !== memberId));
    } catch (err) {
      setError('Failed to remove family member');
    } finally {
      setLoading(false);
    }
  };

  const generateInviteCode = async (): Promise<string> => {
    const code = Math.random().toString(36).substr(2, 9).toUpperCase();
    setInviteCode(code);
    
    // Store invite with expiration
    localStorage.setItem(`invite_${code}`, JSON.stringify({
      familyId: user?.sub,
      createdAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString() // 7 days
    }));
    
    return code;
  };

  // Permissions & Oversight
  const updateMemberPermissions = async (memberId: string, permissions: Partial<FamilyPermissions>) => {
    await updateFamilyMember(memberId, {
      permissions: {
        ...familyMembers.find(m => m.id === memberId)?.permissions,
        ...permissions
      } as FamilyPermissions
    });
  };

  const requestTransactionApproval = async (transaction: Omit<FamilyTransaction, 'id'>) => {
    const newTransaction: FamilyTransaction = {
      ...transaction,
      id: `transaction-${Date.now()}`,
      status: 'pending'
    };

    // Store pending transaction
    const existing = JSON.parse(localStorage.getItem('pending_transactions') || '[]');
    localStorage.setItem('pending_transactions', JSON.stringify([...existing, newTransaction]));

    // Notify parents
    await sendFamilyMessage(
      `${familyMembers.find(m => m.id === transaction.memberId)?.name} requested approval for $${transaction.amount} - ${transaction.description}`,
      familyMembers.filter(m => m.role === 'parent').map(m => m.id)
    );
  };

  const approveTransaction = async (transactionId: string, approverId: string, notes?: string) => {
    const transactions = JSON.parse(localStorage.getItem('pending_transactions') || '[]');
    const updated = transactions.map((t: FamilyTransaction) => 
      t.id === transactionId 
        ? { ...t, status: 'approved', approvedBy: approverId, notes }
        : t
    );
    localStorage.setItem('pending_transactions', JSON.stringify(updated));
  };

  const rejectTransaction = async (transactionId: string, approverId: string, reason: string) => {
    const transactions = JSON.parse(localStorage.getItem('pending_transactions') || '[]');
    const updated = transactions.map((t: FamilyTransaction) => 
      t.id === transactionId 
        ? { ...t, status: 'rejected', approvedBy: approverId, notes: reason }
        : t
    );
    localStorage.setItem('pending_transactions', JSON.stringify(updated));
  };

  // Chores & Allowances
  const assignChore = async (memberId: string, chore: Omit<Chore, 'id'>) => {
    const newChore: Chore = {
      ...chore,
      id: `chore-${Date.now()}`,
      status: 'pending',
      assignedDate: new Date().toISOString()
    };

    await updateFamilyMember(memberId, {
      chores: [...(familyMembers.find(m => m.id === memberId)?.chores || []), newChore]
    });
  };

  const completeChore = async (choreId: string, memberId: string, notes?: string) => {
    const member = familyMembers.find(m => m.id === memberId);
    if (!member) return;

    const updatedChores = member.chores?.map(chore =>
      chore.id === choreId
        ? { ...chore, status: 'completed' as const, completedDate: new Date().toISOString(), notes }
        : chore
    );

    await updateFamilyMember(memberId, { chores: updatedChores });
  };

  const approveChore = async (choreId: string, approverId: string) => {
    // Find member with this chore
    const member = familyMembers.find(m => m.chores?.some(c => c.id === choreId));
    if (!member) return;

    const updatedChores = member.chores?.map(chore =>
      chore.id === choreId
        ? { ...chore, status: 'approved' as const, approvedBy: approverId }
        : chore
    );

    await updateFamilyMember(member.id, { chores: updatedChores });
  };

  const payAllowance = async (memberId: string) => {
    const member = familyMembers.find(m => m.id === memberId);
    if (!member?.allowance) return;

    // Update last paid date
    await updateFamilyMember(memberId, {
      allowance: {
        ...member.allowance,
        lastPaid: new Date().toISOString(),
        nextDue: new Date(Date.now() + (member.allowance.frequency === 'weekly' ? 7 : 30) * 24 * 60 * 60 * 1000).toISOString()
      }
    });

    // Add to member's savings
    const currentBalance = member.savings?.balance || 0;
    await updateFamilyMember(memberId, {
      savings: {
        ...member.savings,
        balance: currentBalance + member.allowance.amount,
        goals: member.savings?.goals || []
      }
    });
  };

  // Family Goals & Budgets
  const createFamilyGoal = async (goal: Omit<FamilySavingsGoal, 'id'>) => {
    const newGoal: FamilySavingsGoal = {
      ...goal,
      id: `goal-${Date.now()}`,
      contributors: goal.contributors || [],
      milestones: goal.milestones || []
    };

    // Store family goals separately
    const existing = JSON.parse(localStorage.getItem('family_goals') || '[]');
    localStorage.setItem('family_goals', JSON.stringify([...existing, newGoal]));
  };

  const contributeToGoal = async (goalId: string, memberId: string, amount: number) => {
    const goals = JSON.parse(localStorage.getItem('family_goals') || '[]');
    const updated = goals.map((goal: FamilySavingsGoal) => {
      if (goal.id === goalId) {
        const existingContribution = goal.contributors.find(c => c.memberId === memberId);
        const newContributors = existingContribution
          ? goal.contributors.map(c => 
              c.memberId === memberId 
                ? { ...c, amount: c.amount + amount }
                : c
            )
          : [...goal.contributors, { memberId, amount }];
          
        return {
          ...goal,
          currentAmount: goal.currentAmount + amount,
          contributors: newContributors
        };
      }
      return goal;
    });
    
    localStorage.setItem('family_goals', JSON.stringify(updated));
  };

  const createFamilyBudget = async (budget: Omit<FamilyBudget, 'id'>) => {
    const newBudget: FamilyBudget = {
      ...budget,
      id: `budget-${Date.now()}`
    };

    const existing = JSON.parse(localStorage.getItem('family_budgets') || '[]');
    localStorage.setItem('family_budgets', JSON.stringify([...existing, newBudget]));
  };

  const updateFamilyBudget = async (budgetId: string, updates: Partial<FamilyBudget>) => {
    const budgets = JSON.parse(localStorage.getItem('family_budgets') || '[]');
    const updated = budgets.map((budget: FamilyBudget) =>
      budget.id === budgetId ? { ...budget, ...updates } : budget
    );
    localStorage.setItem('family_budgets', JSON.stringify(updated));
  };

  // Communication
  const sendFamilyMessage = async (message: string, recipients: string[]) => {
    const notification = {
      id: `notification-${Date.now()}`,
      message,
      recipients,
      sender: currentMember?.id,
      timestamp: new Date().toISOString(),
      read: false
    };

    const existing = JSON.parse(localStorage.getItem('family_notifications') || '[]');
    localStorage.setItem('family_notifications', JSON.stringify([...existing, notification]));
  };

  const getFamilyNotifications = async () => {
    return JSON.parse(localStorage.getItem('family_notifications') || '[]');
  };

  const markNotificationRead = async (notificationId: string) => {
    const notifications = JSON.parse(localStorage.getItem('family_notifications') || '[]');
    const updated = notifications.map((n: any) =>
      n.id === notificationId ? { ...n, read: true } : n
    );
    localStorage.setItem('family_notifications', JSON.stringify(updated));
  };

  // Reports & Analytics
  const getFamilySpendingReport = async (period: 'weekly' | 'monthly' | 'yearly') => {
    // Mock implementation - would fetch from API
    return {
      period,
      totalSpent: 2500,
      topCategories: [
        { category: 'Food', amount: 800 },
        { category: 'Transportation', amount: 400 },
        { category: 'Entertainment', amount: 300 }
      ],
      memberBreakdown: familyMembers.map(member => ({
        memberId: member.id,
        name: member.name,
        spent: Math.random() * 500
      }))
    };
  };

  const getMemberSpendingReport = async (memberId: string, period: 'weekly' | 'monthly' | 'yearly') => {
    const member = familyMembers.find(m => m.id === memberId);
    return {
      memberId,
      memberName: member?.name,
      period,
      totalSpent: Math.random() * 300,
      categories: [
        { category: 'Entertainment', amount: Math.random() * 100 },
        { category: 'Food', amount: Math.random() * 50 }
      ]
    };
  };

  const exportFamilyData = async (format: 'csv' | 'pdf'): Promise<string> => {
    // Mock implementation - would generate actual file
    return `family-data-${Date.now()}.${format}`;
  };

  const contextValue: FamilyContextType = {
    // State
    familyMembers,
    inviteCode,
    pendingInvitations,
    loading,
    error,
    currentMember,
    
    // Member Management
    addFamilyMember,
    updateFamilyMember,
    removeFamilyMember,
    generateInviteCode,
    
    // Permissions & Oversight
    updateMemberPermissions,
    requestTransactionApproval,
    approveTransaction,
    rejectTransaction,
    
    // Chores & Allowances
    assignChore,
    completeChore,
    approveChore,
    payAllowance,
    
    // Family Goals & Budgets
    createFamilyGoal,
    contributeToGoal,
    createFamilyBudget,
    updateFamilyBudget,
    
    // Communication
    sendFamilyMessage,
    getFamilyNotifications,
    markNotificationRead,
    
    // Reports
    getFamilySpendingReport,
    getMemberSpendingReport,
    exportFamilyData
  };

  return (
    <FamilyContext.Provider value={contextValue}>
      {children}
    </FamilyContext.Provider>
  );
};

export const useFamily = (): FamilyContextType => {
  const context = useContext(FamilyContext);
  if (!context) {
    throw new Error('useFamily must be used within a FamilyProvider');
  }
  return context;
};