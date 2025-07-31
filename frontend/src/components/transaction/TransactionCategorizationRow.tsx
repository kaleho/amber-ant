/**
 * Transaction Categorization Row Component
 * Enhanced transaction list item with dual categorization and quick actions
 * Supports persona-specific interfaces and stewardship guidance
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';
import HapticFeedback from 'react-native-haptic-feedback';
import { format } from 'date-fns';

import { Transaction, ExpenseType } from '../../types';
import { Colors, getCategoryColor, getExpenseTypeColor } from '../../constants/Colors';
import { usePersona } from '../../contexts/PersonaContext';

interface TransactionCategorizationRowProps {
  transaction: Transaction;
  onCategorize: (transactionId: string, expenseType: ExpenseType) => Promise<void>;
  onSplit: (transactionId: string) => void;
  onAutoClassify: (transactionId: string) => Promise<void>;
  onEdit: (transactionId: string) => void;
  showStewardshipGuidance?: boolean;
}

export const TransactionCategorizationRow: React.FC<TransactionCategorizationRowProps> = ({
  transaction,
  onCategorize,
  onSplit,
  onAutoClassify,
  onEdit,
  showStewardshipGuidance = false,
}) => {
  const { currentPersona, shouldUseHapticFeedback, getComplexityLevel } = usePersona();
  const [isProcessing, setIsProcessing] = useState(false);

  const complexityLevel = getComplexityLevel();
  const isUncategorized = transaction.app_expense_type === null || transaction.app_expense_type === undefined;
  const isSplit = transaction.is_split;

  const handleQuickCategorize = async (expenseType: ExpenseType) => {
    if (isProcessing) return;

    setIsProcessing(true);
    
    try {
      await onCategorize(transaction.id, expenseType);
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('impactLight');
      }
    } catch (error) {
      console.error('Error categorizing transaction:', error);
      Alert.alert('Error', 'Failed to categorize transaction');
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('notificationError');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAutoClassify = async () => {
    if (isProcessing) return;

    setIsProcessing(true);
    
    try {
      await onAutoClassify(transaction.id);
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('impactMedium');
      }
    } catch (error) {
      console.error('Error auto-classifying transaction:', error);
      Alert.alert('Error', 'Failed to auto-classify transaction');
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('notificationError');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const formatAmount = (amount: number): string => {
    return `$${Math.abs(amount).toFixed(2)}`;
  };

  const formatDate = (dateString: string): string => {
    return format(new Date(dateString), 'MMM d, yyyy');
  };

  const getMerchantDisplayName = (): string => {
    return transaction.merchant_name || transaction.name;
  };

  const getCategoryIcon = (category: string): string => {
    const iconMap: Record<string, string> = {
      groceries: 'local-grocery-store',
      transportation: 'directions-car',
      rent: 'home',
      utilities: 'flash-on',
      health: 'local-hospital',
      entertainment: 'movie',
      shopping: 'shopping-bag',
      dining: 'restaurant',
      education: 'school',
      clothing: 'checkroom',
      personal_care: 'spa',
      travel: 'flight',
      insurance: 'security',
      taxes: 'account-balance',
      charity: 'favorite',
      default: 'category',
    };
    
    return iconMap[category] || iconMap.default;
  };

  const renderPersonaSpecificInterface = () => {
    if (currentPersona === 'pre_teen') {
      return renderPreTeenInterface();
    } else if (currentPersona === 'teen') {
      return renderTeenInterface();
    } else if (currentPersona === 'single_parent') {
      return renderSingleParentInterface();
    } else if (currentPersona === 'fixed_income') {
      return renderFixedIncomeInterface();
    }
    
    return renderDefaultInterface();
  };

  const renderPreTeenInterface = () => {
    if (isUncategorized) {
      return (
        <View style={styles.preTeenActions}>
          <Text style={styles.preTeenQuestion}>Is this something you NEED or WANT?</Text>
          
          <View style={styles.preTeenButtons}>
            <TouchableOpacity
              style={[styles.preTeenButton, styles.preTeenNeedButton]}
              onPress={() => handleQuickCategorize('fixed')}
              disabled={isProcessing}
            >
              <Icon name="home" size={24} color="white" />
              <Text style={styles.preTeenButtonText}>NEED</Text>
              <Text style={styles.preTeenButtonSubtext}>(like food, school supplies)</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.preTeenButton, styles.preTeenWantButton]}
              onPress={() => handleQuickCategorize('discretionary')}
              disabled={isProcessing}
            >
              <Icon name="card-giftcard" size={24} color="white" />
              <Text style={styles.preTeenButtonText}>WANT</Text>
              <Text style={styles.preTeenButtonSubtext}>(like toys, games, treats)</Text>
            </TouchableOpacity>
          </View>
          
          {showStewardshipGuidance && (
            <Text style={styles.preTeenGuidance}>
              💡 Remember: Needs first, wants second!
            </Text>
          )}
        </View>
      );
    }
    
    return renderCategorizedDisplay();
  };

  const renderTeenInterface = () => {
    if (isUncategorized) {
      return (
        <View style={styles.teenActions}>
          <Text style={styles.teenQuestion}>What type of expense is this?</Text>
          
          <View style={styles.teenOptions}>
            <TouchableOpacity
              style={styles.teenOption}
              onPress={() => handleQuickCategorize('fixed')}
              disabled={isProcessing}
            >
              <Icon name="radio-button-unchecked" size={20} color={Colors.light.fixed} />
              <Text style={styles.teenOptionText}>Fixed (Need) - Required for school or work</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.teenOption}
              onPress={() => handleQuickCategorize('discretionary')}
              disabled={isProcessing}
            >
              <Icon name="radio-button-unchecked" size={20} color={Colors.light.discretionary} />
              <Text style={styles.teenOptionText}>Discretionary (Want) - Nice to have but not essential</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.teenOption}
              onPress={() => onSplit(transaction.id)}
              disabled={isProcessing}
            >
              <Icon name="radio-button-unchecked" size={20} color={Colors.light.info} />
              <Text style={styles.teenOptionText}>Split - Part need, part want</Text>
            </TouchableOpacity>
          </View>
          
          {showStewardshipGuidance && (
            <View style={styles.teenGuidance}>
              <Text style={styles.teenGuidanceText}>
                💭 Think about it: Is this item necessary for your education or required activities? 
                Or is it an upgrade/entertainment purchase?
              </Text>
            </View>
          )}
          
          <View style={styles.teenActionButtons}>
            <TouchableOpacity style={styles.teenCategorizeButton} disabled={isProcessing}>
              <Text style={styles.teenCategorizeButtonText}>Categorize</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.teenHelpButton}>
              <Text style={styles.teenHelpButtonText}>Need Help?</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }
    
    return renderCategorizedDisplay();
  };

  const renderSingleParentInterface = () => {
    if (isUncategorized) {
      return (
        <View style={styles.singleParentActions}>
          <View style={styles.singleParentHeader}>
            <Icon name="flash-on" size={20} color={Colors.light.warning} />
            <Text style={styles.singleParentTitle}>Quick Categorization for Busy Parents</Text>
          </View>
          
          <View style={styles.singleParentSuggestion}>
            <Text style={styles.suggestionTitle}>🎯 Smart Suggestion: 75% Fixed / 25% Discretionary</Text>
            <Text style={styles.suggestionSubtext}>Based on your family's typical patterns</Text>
          </View>
          
          <View style={styles.singleParentBreakdown}>
            <View style={styles.breakdownItem}>
              <Text style={styles.breakdownLabel}>Family Fixed (Needs): ${(transaction.amount * 0.75).toFixed(2)}</Text>
              <Text style={styles.breakdownSubtext}>• Basic groceries, household essentials</Text>
            </View>
            
            <View style={styles.breakdownItem}>
              <Text style={styles.breakdownLabel}>Family Discretionary (Wants): ${(transaction.amount * 0.25).toFixed(2)}</Text>
              <Text style={styles.breakdownSubtext}>• Treats, convenience items</Text>
            </View>
          </View>
          
          <View style={styles.singleParentButtons}>
            <TouchableOpacity
              style={styles.acceptButton}
              onPress={handleAutoClassify}
              disabled={isProcessing}
            >
              <Icon name="check" size={16} color="white" />
              <Text style={styles.acceptButtonText}>Accept</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.adjustButton}
              onPress={() => onSplit(transaction.id)}
              disabled={isProcessing}
            >
              <Icon name="edit" size={16} color={Colors.light.text} />
              <Text style={styles.adjustButtonText}>Adjust</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.saveDefaultButton}
              disabled={isProcessing}
            >
              <Icon name="flash-on" size={16} color={Colors.light.warning} />
              <Text style={styles.saveDefaultButtonText}>Save as Default</Text>
            </TouchableOpacity>
          </View>
          
          <Text style={styles.timesSaved}>⏱️ Categorized in 10 seconds!</Text>
        </View>
      );
    }
    
    return renderCategorizedDisplay();
  };

  const renderFixedIncomeInterface = () => {
    if (isUncategorized && transaction.plaid_category === 'health') {
      return (
        <View style={styles.fixedIncomeActions}>
          <Text style={styles.fixedIncomeTitle}>Healthcare Expense Type:</Text>
          
          <View style={styles.fixedIncomeButtons}>
            <TouchableOpacity
              style={[styles.fixedIncomeButton, styles.essentialButton]}
              onPress={() => handleQuickCategorize('fixed')}
              disabled={isProcessing}
            >
              <Icon name="local-pharmacy" size={24} color="white" />
              <Text style={styles.fixedIncomeButtonText}>ESSENTIAL</Text>
              <Text style={styles.fixedIncomeButtonSubtext}>Prescriptions, Medical supplies</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.fixedIncomeButton, styles.optionalButton]}
              onPress={() => handleQuickCategorize('discretionary')}
              disabled={isProcessing}
            >
              <Icon name="card-giftcard" size={24} color="white" />
              <Text style={styles.fixedIncomeButtonText}>OPTIONAL</Text>
              <Text style={styles.fixedIncomeButtonSubtext}>Vitamins, supplements, comfort items</Text>
            </TouchableOpacity>
          </View>
          
          <Text style={styles.medicareNote}>📋 Medicare/Insurance may cover essential items</Text>
        </View>
      );
    }
    
    return renderDefaultInterface();
  };

  const renderDefaultInterface = () => {
    if (isUncategorized) {
      return (
        <View style={styles.defaultActions}>
          <Text style={styles.categorizationNeeded}>⚠️ Needs categorization</Text>
          
          <View style={styles.quickActions}>
            <TouchableOpacity
              style={[styles.quickActionButton, styles.fixedButton]}
              onPress={() => handleQuickCategorize('fixed')}
              disabled={isProcessing}
            >
              <Icon name="home" size={16} color="white" />
              <Text style={styles.quickActionText}>Fixed</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.quickActionButton, styles.discretionaryButton]}
              onPress={() => handleQuickCategorize('discretionary')}
              disabled={isProcessing}
            >
              <Icon name="card-giftcard" size={16} color="white" />
              <Text style={styles.quickActionText}>Discretionary</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.quickActionButton, styles.splitButton]}
              onPress={() => onSplit(transaction.id)}
              disabled={isProcessing}
            >
              <Icon name="call-split" size={16} color="white" />
              <Text style={styles.quickActionText}>Split</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[styles.quickActionButton, styles.autoButton]}
              onPress={handleAutoClassify}
              disabled={isProcessing}
            >
              <Icon name="auto-fix-high" size={16} color="white" />
              <Text style={styles.quickActionText}>Auto</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }
    
    return renderCategorizedDisplay();
  };

  const renderCategorizedDisplay = () => {
    if (isSplit && transaction.split_details) {
      return (
        <View style={styles.categorizedDisplay}>
          <View style={styles.splitDisplay}>
            <Icon name="call-split" size={16} color={Colors.light.info} />
            <View style={styles.splitDetails}>
              {transaction.split_details.fixed_categories.map((cat, index) => (
                <Text key={`fixed-${index}`} style={styles.splitText}>
                  {cat.category}/fixed: ${cat.amount.toFixed(2)}
                </Text>
              ))}
              {transaction.split_details.discretionary_categories.map((cat, index) => (
                <Text key={`discretionary-${index}`} style={styles.splitText}>
                  {cat.category}/discretionary: ${cat.amount.toFixed(2)}
                </Text>
              ))}
            </View>
          </View>
          
          <TouchableOpacity
            style={styles.editSplitButton}
            onPress={() => onEdit(transaction.id)}
          >
            <Icon name="edit" size={16} color={Colors.light.primary} />
            <Text style={styles.editSplitText}>Edit Split</Text>
          </TouchableOpacity>
        </View>
      );
    } else if (transaction.app_expense_type) {
      const expenseTypeColor = getExpenseTypeColor(transaction.app_expense_type);
      
      return (
        <View style={styles.categorizedDisplay}>
          <View style={styles.categoryChip}>
            <View style={[styles.categoryDot, { backgroundColor: expenseTypeColor }]} />
            <Text style={styles.categoryText}>
              {transaction.plaid_category}/{transaction.app_expense_type}
            </Text>
          </View>
          
          <TouchableOpacity
            style={styles.editButton}
            onPress={() => onEdit(transaction.id)}
          >
            <Icon name="edit" size={16} color={Colors.light.textSecondary} />
          </TouchableOpacity>
        </View>
      );
    }
    
    return null;
  };

  return (
    <View style={styles.container}>
      <View style={styles.transactionHeader}>
        <View style={styles.merchantInfo}>
          <View style={styles.iconContainer}>
            <Icon 
              name={getCategoryIcon(transaction.plaid_category)} 
              size={24} 
              color={getCategoryColor(transaction.plaid_category)} 
            />
          </View>
          
          <View style={styles.transactionDetails}>
            <Text style={styles.merchantName}>{getMerchantDisplayName()}</Text>
            <Text style={styles.transactionDate}>
              {formatDate(transaction.date)} • {transaction.plaid_category}
            </Text>
          </View>
        </View>
        
        <Text style={[
          styles.amount,
          { color: transaction.amount >= 0 ? Colors.light.income : Colors.light.expense }
        ]}>
          {transaction.amount >= 0 ? '+' : ''}{formatAmount(transaction.amount)}
        </Text>
      </View>
      
      {renderPersonaSpecificInterface()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.light.surface,
    marginHorizontal: 16,
    marginVertical: 4,
    borderRadius: 12,
    padding: 16,
    elevation: 1,
    shadowColor: Colors.light.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  transactionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  merchantInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.light.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  transactionDetails: {
    flex: 1,
  },
  merchantName: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 2,
  },
  transactionDate: {
    fontSize: 13,
    color: Colors.light.textSecondary,
  },
  amount: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  
  // Pre-teen specific styles
  preTeenActions: {
    alignItems: 'center',
  },
  preTeenQuestion: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  preTeenButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 12,
  },
  preTeenButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 6,
  },
  preTeenNeedButton: {
    backgroundColor: Colors.light.fixed,
  },
  preTeenWantButton: {
    backgroundColor: Colors.light.discretionary,
  },
  preTeenButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 4,
  },
  preTeenButtonSubtext: {
    color: 'white',
    fontSize: 12,
    textAlign: 'center',
    opacity: 0.9,
    marginTop: 2,
  },
  preTeenGuidance: {
    fontSize: 14,
    color: Colors.light.primary,
    textAlign: 'center',
    fontWeight: '500',
  },
  
  // Teen specific styles
  teenActions: {
    marginTop: 8,
  },
  teenQuestion: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
  },
  teenOptions: {
    marginBottom: 12,
  },
  teenOption: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  teenOptionText: {
    fontSize: 14,
    color: Colors.light.text,
    marginLeft: 8,
    flex: 1,
  },
  teenGuidance: {
    backgroundColor: Colors.light.surface,
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: Colors.light.info,
  },
  teenGuidanceText: {
    fontSize: 13,
    color: Colors.light.textSecondary,
    lineHeight: 18,
  },
  teenActionButtons: {
    flexDirection: 'row',
  },
  teenCategorizeButton: {
    backgroundColor: Colors.light.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 6,
    marginRight: 12,
  },
  teenCategorizeButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  teenHelpButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  teenHelpButtonText: {
    color: Colors.light.text,
    fontSize: 14,
    fontWeight: '600',
  },
  
  // Single parent specific styles
  singleParentActions: {
    marginTop: 8,
  },
  singleParentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  singleParentTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
    marginLeft: 6,
  },
  singleParentSuggestion: {
    backgroundColor: Colors.light.info + '15',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  suggestionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 2,
  },
  suggestionSubtext: {
    fontSize: 12,
    color: Colors.light.textSecondary,
  },
  singleParentBreakdown: {
    marginBottom: 12,
  },
  breakdownItem: {
    marginBottom: 6,
  },
  breakdownLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.light.text,
  },
  breakdownSubtext: {
    fontSize: 12,
    color: Colors.light.textSecondary,
    marginLeft: 8,
  },
  singleParentButtons: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  acceptButton: {
    backgroundColor: Colors.light.success,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    marginRight: 8,
  },
  acceptButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  adjustButton: {
    backgroundColor: Colors.light.surface,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    marginRight: 8,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  adjustButtonText: {
    color: Colors.light.text,
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  saveDefaultButton: {
    backgroundColor: Colors.light.warning + '15',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  saveDefaultButtonText: {
    color: Colors.light.warning,
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  timesSaved: {
    fontSize: 12,
    color: Colors.light.success,
    textAlign: 'center',
    fontWeight: '500',
  },
  
  // Fixed income specific styles
  fixedIncomeActions: {
    alignItems: 'center',
    marginTop: 8,
  },
  fixedIncomeTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
  },
  fixedIncomeButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 12,
  },
  fixedIncomeButton: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginHorizontal: 6,
  },
  essentialButton: {
    backgroundColor: Colors.light.fixed,
  },
  optionalButton: {
    backgroundColor: Colors.light.discretionary,
  },
  fixedIncomeButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 4,
  },
  fixedIncomeButtonSubtext: {
    color: 'white',
    fontSize: 11,
    textAlign: 'center',
    opacity: 0.9,
    marginTop: 2,
  },
  medicareNote: {
    fontSize: 12,
    color: Colors.light.info,
    textAlign: 'center',
  },
  
  // Default interface styles
  defaultActions: {
    marginTop: 8,
  },
  categorizationNeeded: {
    fontSize: 13,
    color: Colors.light.warning,
    fontWeight: '500',
    marginBottom: 12,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  quickActionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginHorizontal: 2,
  },
  fixedButton: {
    backgroundColor: Colors.light.fixed,
  },
  discretionaryButton: {
    backgroundColor: Colors.light.discretionary,
  },
  splitButton: {
    backgroundColor: Colors.light.info,
  },
  autoButton: {
    backgroundColor: Colors.light.secondary,
  },
  quickActionText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  
  // Categorized display styles
  categorizedDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  splitDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  splitDetails: {
    marginLeft: 8,
    flex: 1,
  },
  splitText: {
    fontSize: 12,
    color: Colors.light.textSecondary,
    marginBottom: 2,
  },
  editSplitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 4,
  },
  editSplitText: {
    fontSize: 12,
    color: Colors.light.primary,
    marginLeft: 4,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.light.surface,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  categoryDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  categoryText: {
    fontSize: 12,
    color: Colors.light.textSecondary,
  },
  editButton: {
    padding: 4,
  },
});