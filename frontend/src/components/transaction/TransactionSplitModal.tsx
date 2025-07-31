/**
 * Transaction Split Modal Component
 * Advanced transaction splitting interface with dual categorization
 * Supports splitting between fixed (needs) and discretionary (wants) expenses
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Dimensions,
} from 'react-native';
import Modal from 'react-native-modal';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';
import DropDownPicker from 'react-native-dropdown-picker';
import HapticFeedback from 'react-native-haptic-feedback';

import { Transaction, SplitDetails, CategoryAmount, ExpenseType } from '../../types';
import { Colors, getExpenseTypeColor } from '../../constants/Colors';
import { usePersona } from '../../contexts/PersonaContext';

interface TransactionSplitModalProps {
  isVisible: boolean;
  transaction: Transaction | null;
  onClose: () => void;
  onSave: (splitDetails: SplitDetails) => Promise<void>;
  splitSuggestions?: {
    typical_fixed_percentage: number;
    typical_discretionary_percentage: number;
    fixed_items: string[];
    discretionary_items: string[];
    confidence: 'high' | 'medium' | 'low';
  };
}

interface SplitItem {
  id: string;
  category: string;
  amount: number;
  expenseType: ExpenseType;
}

const { width } = Dimensions.get('window');

const PLAID_CATEGORIES = [
  { label: 'Groceries', value: 'groceries' },
  { label: 'Transportation', value: 'transportation' },
  { label: 'Shopping', value: 'shopping' },
  { label: 'Dining', value: 'dining' },
  { label: 'Entertainment', value: 'entertainment' },
  { label: 'Health', value: 'health' },
  { label: 'Household', value: 'household' },
  { label: 'Utilities', value: 'utilities' },
  { label: 'Education', value: 'education' },
  { label: 'Professional Services', value: 'professional_services' },
  { label: 'Travel', value: 'travel' },
  { label: 'Personal Care', value: 'personal_care' },
  { label: 'Clothing', value: 'clothing' },
  { label: 'Insurance', value: 'insurance' },
  { label: 'Taxes', value: 'taxes' },
  { label: 'Charity', value: 'charity' },
];

export const TransactionSplitModal: React.FC<TransactionSplitModalProps> = ({
  isVisible,
  transaction,
  onClose,
  onSave,
  splitSuggestions,
}) => {
  const { shouldUseHapticFeedback, currentPersona } = usePersona();
  
  const [splitItems, setSplitItems] = useState<SplitItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  
  // Dropdown states
  const [openDropdowns, setOpenDropdowns] = useState<Record<string, boolean>>({});
  const [categoryValues, setCategoryValues] = useState<Record<string, string>>({});

  // Initialize split items when transaction changes
  useEffect(() => {
    if (transaction && isVisible) {
      initializeSplitItems();
    }
  }, [transaction, isVisible]);

  // Calculate total allocated amount
  const totalAllocated = useMemo(() => {
    return splitItems.reduce((sum, item) => sum + item.amount, 0);
  }, [splitItems]);

  // Calculate remaining amount
  const remainingAmount = useMemo(() => {
    if (!transaction) return 0;
    return transaction.amount - totalAllocated;
  }, [transaction, totalAllocated]);

  // Check if split is valid
  const isValidSplit = useMemo(() => {
    if (!transaction) return false;
    return Math.abs(remainingAmount) < 0.01 && splitItems.length >= 2;
  }, [transaction, remainingAmount, splitItems]);

  const initializeSplitItems = () => {
    if (!transaction) return;

    const initialItems: SplitItem[] = [];
    
    if (splitSuggestions && splitSuggestions.confidence === 'high') {
      // Use AI suggestions for high confidence splits
      const fixedAmount = transaction.amount * (splitSuggestions.typical_fixed_percentage / 100);
      const discretionaryAmount = transaction.amount * (splitSuggestions.typical_discretionary_percentage / 100);
      
      initialItems.push({
        id: 'fixed-1',
        category: transaction.plaid_category,
        amount: parseFloat(fixedAmount.toFixed(2)),
        expenseType: 'fixed',
      });
      
      initialItems.push({
        id: 'discretionary-1',
        category: transaction.plaid_category,
        amount: parseFloat(discretionaryAmount.toFixed(2)),
        expenseType: 'discretionary',
      });
    } else {
      // Default 70/30 split for manual entry
      const fixedAmount = transaction.amount * 0.7;
      const discretionaryAmount = transaction.amount * 0.3;
      
      initialItems.push({
        id: 'fixed-1',
        category: transaction.plaid_category,
        amount: parseFloat(fixedAmount.toFixed(2)),
        expenseType: 'fixed',
      });
      
      initialItems.push({
        id: 'discretionary-1',
        category: transaction.plaid_category,
        amount: parseFloat(discretionaryAmount.toFixed(2)),
        expenseType: 'discretionary',
      });
    }
    
    setSplitItems(initialItems);
    
    // Initialize category values
    const initialCategoryValues: Record<string, string> = {};
    initialItems.forEach(item => {
      initialCategoryValues[item.id] = item.category;
    });
    setCategoryValues(initialCategoryValues);
  };

  const addSplitItem = (expenseType: ExpenseType) => {
    const newItem: SplitItem = {
      id: `${expenseType}-${Date.now()}`,
      category: transaction?.plaid_category || 'groceries',
      amount: 0,
      expenseType,
    };
    
    setSplitItems(prev => [...prev, newItem]);
    setCategoryValues(prev => ({ ...prev, [newItem.id]: newItem.category }));
    
    if (shouldUseHapticFeedback()) {
      HapticFeedback.trigger('impactLight');
    }
  };

  const removeSplitItem = (itemId: string) => {
    setSplitItems(prev => prev.filter(item => item.id !== itemId));
    setCategoryValues(prev => {
      const updated = { ...prev };
      delete updated[itemId];
      return updated;
    });
    
    if (shouldUseHapticFeedback()) {
      HapticFeedback.trigger('impactMedium');
    }
  };

  const updateSplitItem = (itemId: string, updates: Partial<SplitItem>) => {
    setSplitItems(prev => prev.map(item => 
      item.id === itemId ? { ...item, ...updates } : item
    ));
    
    if (updates.category) {
      setCategoryValues(prev => ({ ...prev, [itemId]: updates.category! }));
    }
  };

  const applySuggestionPreset = (fixedPercentage: number) => {
    if (!transaction) return;
    
    const fixedAmount = transaction.amount * (fixedPercentage / 100);
    const discretionaryAmount = transaction.amount * ((100 - fixedPercentage) / 100);
    
    setSplitItems([
      {
        id: 'fixed-preset',
        category: transaction.plaid_category,
        amount: parseFloat(fixedAmount.toFixed(2)),
        expenseType: 'fixed',
      },
      {
        id: 'discretionary-preset',
        category: transaction.plaid_category,
        amount: parseFloat(discretionaryAmount.toFixed(2)),
        expenseType: 'discretionary',
      },
    ]);
    
    setCategoryValues({
      'fixed-preset': transaction.plaid_category,
      'discretionary-preset': transaction.plaid_category,
    });
    
    if (shouldUseHapticFeedback()) {
      HapticFeedboard.trigger('impactLight');
    }
  };

  const validateAndSave = async () => {
    if (!transaction || !isValidSplit) {
      setValidationError('Please ensure all amounts add up to the transaction total');
      return;
    }

    setIsLoading(true);
    setValidationError(null);

    try {
      const fixedCategories: CategoryAmount[] = [];
      const discretionaryCategories: CategoryAmount[] = [];

      splitItems.forEach(item => {
        const categoryAmount: CategoryAmount = {
          category: item.category,
          amount: item.amount,
        };

        if (item.expenseType === 'fixed') {
          fixedCategories.push(categoryAmount);
        } else {
          discretionaryCategories.push(categoryAmount);
        }
      });

      const splitDetails: SplitDetails = {
        fixed_categories: fixedCategories,
        discretionary_categories: discretionaryCategories,
      };

      await onSave(splitDetails);
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('notificationSuccess');
      }
      
      onClose();
    } catch (error) {
      console.error('Error saving split:', error);
      setValidationError('Failed to save transaction split');
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('notificationError');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const renderSplitItem = (item: SplitItem, index: number) => {
    const expenseTypeColor = getExpenseTypeColor(item.expenseType);
    const canRemove = splitItems.filter(i => i.expenseType === item.expenseType).length > 1;

    return (
      <View key={item.id} style={[styles.splitItem, { borderLeftColor: expenseTypeColor }]}>
        <View style={styles.splitItemHeader}>
          <View style={[styles.expenseTypeIcon, { backgroundColor: expenseTypeColor }]}>
            <Icon 
              name={item.expenseType === 'fixed' ? 'home' : 'card-giftcard'} 
              size={16} 
              color="white" 
            />
          </View>
          
          <Text style={styles.expenseTypeLabel}>
            {item.expenseType === 'fixed' ? 'Fixed (Need)' : 'Discretionary (Want)'}
          </Text>
          
          {canRemove && (
            <TouchableOpacity 
              onPress={() => removeSplitItem(item.id)}
              style={styles.removeButton}
            >
              <Icon name="close" size={20} color={Colors.light.error} />
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.splitItemContent}>
          <View style={styles.categorySelector}>
            <Text style={styles.inputLabel}>Category</Text>
            <DropDownPicker
              open={openDropdowns[item.id] || false}
              value={categoryValues[item.id] || item.category}
              items={PLAID_CATEGORIES}
              setOpen={(open) => setOpenDropdowns(prev => ({ ...prev, [item.id]: open }))}
              setValue={(value) => {
                const newCategory = typeof value === 'function' ? value(categoryValues[item.id]) : value;
                updateSplitItem(item.id, { category: newCategory });
              }}
              style={styles.dropdown}
              dropDownStyle={styles.dropdownContainer}
              textStyle={styles.dropdownText}
              placeholder="Select category"
              searchable={true}
              searchPlaceholder="Search categories..."
              zIndex={1000 - index}
            />
          </View>

          <View style={styles.amountInput}>
            <Text style={styles.inputLabel}>Amount</Text>
            <TextInput
              style={styles.amountInputField}
              value={item.amount.toString()}
              onChangeText={(text) => {
                const amount = parseFloat(text) || 0;
                updateSplitItem(item.id, { amount });
              }}
              keyboardType="numeric"
              placeholder="0.00"
              placeholderTextColor={Colors.light.placeholder}
            />
          </View>
        </View>
      </View>
    );
  };

  const renderQuickPresets = () => {
    if (!splitSuggestions) return null;

    const presets = [
      { label: '80/20', fixed: 80 },
      { label: '70/30', fixed: 70 },
      { label: '60/40', fixed: 60 },
      { label: '50/50', fixed: 50 },
    ];

    return (
      <View style={styles.presetsSection}>
        <Text style={styles.presetsTitle}>Quick Split Presets</Text>
        <View style={styles.presetsContainer}>
          {presets.map((preset) => (
            <TouchableOpacity
              key={preset.label}
              style={styles.presetButton}
              onPress={() => applySuggestionPreset(preset.fixed)}
            >
              <Text style={styles.presetButtonText}>{preset.label}</Text>
              <Text style={styles.presetButtonSubtext}>
                Fixed/Discretionary
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  };

  const renderStewardshipGuidance = () => {
    if (currentPersona === 'pre_teen' || currentPersona === 'teen') {
      return (
        <View style={styles.guidanceSection}>
          <View style={styles.guidanceHeader}>
            <Icon name="lightbulb" size={20} color={Colors.light.warning} />
            <Text style={styles.guidanceTitle}>Stewardship Guidance</Text>
          </View>
          
          <View style={styles.guidanceContent}>
            <View style={styles.guidanceItem}>
              <Icon name="home" size={16} color={Colors.light.fixed} />
              <Text style={styles.guidanceText}>
                <Text style={styles.guidanceBold}>Fixed (Needs):</Text> Essential items for basic living
              </Text>
            </View>
            
            <View style={styles.guidanceItem}>
              <Icon name="card-giftcard" size={16} color={Colors.light.discretionary} />
              <Text style={styles.guidanceText}>
                <Text style={styles.guidanceBold}>Discretionary (Wants):</Text> Nice to have but not essential
              </Text>
            </View>
          </View>
          
          <Text style={styles.bibleVerse}>
            "But seek first his kingdom and his righteousness, and all these things will be given to you as well." - Matthew 6:33
          </Text>
        </View>
      );
    }
    return null;
  };

  if (!transaction) return null;

  return (
    <Modal
      isVisible={isVisible}
      onBackdropPress={onClose}
      style={styles.modal}
      propagateSwipe={true}
      scrollHorizontal={true}
    >
      <View style={styles.modalContent}>
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Text style={styles.title}>Split Transaction</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="close" size={24} color={Colors.light.text} />
            </TouchableOpacity>
          </View>
          
          <View style={styles.transactionInfo}>
            <Text style={styles.merchantName}>{transaction.merchant_name || transaction.name}</Text>
            <Text style={styles.transactionAmount}>${transaction.amount.toFixed(2)}</Text>
            <Text style={styles.transactionDate}>
              {new Date(transaction.date).toLocaleDateString()} • {transaction.plaid_category}
            </Text>
          </View>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {renderStewardshipGuidance()}
          {renderQuickPresets()}

          <View style={styles.splitSection}>
            <View style={styles.sectionHeader}>
              <Icon name="home" size={20} color={Colors.light.fixed} />
              <Text style={styles.sectionTitle}>Fixed Expenses (Needs)</Text>
              <TouchableOpacity 
                onPress={() => addSplitItem('fixed')}
                style={styles.addButton}
              >
                <Icon name="add" size={20} color={Colors.light.fixed} />
              </TouchableOpacity>
            </View>
            
            {splitItems
              .filter(item => item.expenseType === 'fixed')
              .map((item, index) => renderSplitItem(item, index))}
          </View>

          <View style={styles.splitSection}>
            <View style={styles.sectionHeader}>
              <Icon name="card-giftcard" size={20} color={Colors.light.discretionary} />
              <Text style={styles.sectionTitle}>Discretionary Expenses (Wants)</Text>
              <TouchableOpacity 
                onPress={() => addSplitItem('discretionary')}
                style={styles.addButton}
              >
                <Icon name="add" size={20} color={Colors.light.discretionary} />
              </TouchableOpacity>
            </View>
            
            {splitItems
              .filter(item => item.expenseType === 'discretionary')
              .map((item, index) => renderSplitItem(item, index))}
          </View>

          <View style={styles.summarySection}>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Total Allocated:</Text>
              <Text style={[styles.summaryValue, { color: isValidSplit ? Colors.light.success : Colors.light.warning }]}>
                ${totalAllocated.toFixed(2)}
              </Text>
            </View>
            
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Remaining:</Text>
              <Text style={[
                styles.summaryValue, 
                { color: Math.abs(remainingAmount) < 0.01 ? Colors.light.success : Colors.light.error }
              ]}>
                ${remainingAmount.toFixed(2)}
              </Text>
            </View>
            
            {Math.abs(remainingAmount) < 0.01 && (
              <View style={styles.validationSuccess}>
                <Icon name="check-circle" size={16} color={Colors.light.success} />
                <Text style={styles.validationSuccessText}>Split is balanced!</Text>
              </View>
            )}
          </View>

          {validationError && (
            <View style={styles.errorContainer}>
              <Icon name="error" size={16} color={Colors.light.error} />
              <Text style={styles.errorText}>{validationError}</Text>
            </View>
          )}
        </ScrollView>

        <View style={styles.footer}>
          <TouchableOpacity 
            style={styles.cancelButton} 
            onPress={onClose}
            disabled={isLoading}
          >
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          
          <LinearGradient
            colors={Colors.light.primary}
            style={[styles.saveButton, { opacity: isValidSplit ? 1 : 0.5 }]}
          >
            <TouchableOpacity 
              onPress={validateAndSave}
              disabled={!isValidSplit || isLoading}
              style={styles.saveButtonTouchable}
            >
              <Text style={styles.saveButtonText}>
                {isLoading ? 'Saving...' : 'Save Split'}
              </Text>
            </TouchableOpacity>
          </LinearGradient>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  modal: {
    margin: 0,
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.light.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
    minHeight: '70%',
  },
  header: {
    padding: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.light.text,
  },
  closeButton: {
    padding: 4,
  },
  transactionInfo: {
    alignItems: 'center',
  },
  merchantName: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 4,
  },
  transactionAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.light.primary,
    marginBottom: 4,
  },
  transactionDate: {
    fontSize: 14,
    color: Colors.light.textSecondary,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  presetsSection: {
    marginBottom: 24,
  },
  presetsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 12,
  },
  presetsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  presetButton: {
    flex: 1,
    backgroundColor: Colors.light.surface,
    borderRadius: 8,
    padding: 12,
    marginHorizontal: 4,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  presetButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 2,
  },
  presetButtonSubtext: {
    fontSize: 12,
    color: Colors.light.textSecondary,
  },
  guidanceSection: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    borderLeftWidth: 4,
    borderLeftColor: Colors.light.warning,
  },
  guidanceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  guidanceTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginLeft: 8,
  },
  guidanceContent: {
    marginBottom: 12,
  },
  guidanceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  guidanceText: {
    fontSize: 14,
    color: Colors.light.text,
    marginLeft: 8,
    flex: 1,
  },
  guidanceBold: {
    fontWeight: '600',
  },
  bibleVerse: {
    fontSize: 13,
    fontStyle: 'italic',
    color: Colors.light.textSecondary,
    textAlign: 'center',
    marginTop: 8,
  },
  splitSection: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginLeft: 8,
    flex: 1,
  },
  addButton: {
    padding: 4,
  },
  splitItem: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  splitItemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  expenseTypeIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  expenseTypeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.light.text,
    marginLeft: 8,
    flex: 1,
  },
  removeButton: {
    padding: 4,
  },
  splitItemContent: {
    flexDirection: 'row',
    alignItems: 'flex-end',
  },
  categorySelector: {
    flex: 2,
    marginRight: 12,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.light.text,
    marginBottom: 6,
  },
  dropdown: {
    backgroundColor: Colors.light.background,
    borderColor: Colors.light.border,
    borderRadius: 8,
    minHeight: 44,
  },
  dropdownContainer: {
    backgroundColor: Colors.light.background,
    borderColor: Colors.light.border,
  },
  dropdownText: {
    fontSize: 14,
    color: Colors.light.text,
  },
  amountInput: {
    flex: 1,
  },
  amountInputField: {
    backgroundColor: Colors.light.background,
    borderWidth: 1,
    borderColor: Colors.light.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: Colors.light.text,
    textAlign: 'right',
  },
  summarySection: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 16,
    color: Colors.light.text,
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  validationSuccess: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
    padding: 8,
    backgroundColor: `${Colors.light.success}15`,
    borderRadius: 6,
  },
  validationSuccessText: {
    fontSize: 14,
    color: Colors.light.success,
    marginLeft: 6,
    fontWeight: '500',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: `${Colors.light.error}15`,
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: Colors.light.error,
    marginLeft: 8,
    flex: 1,
  },
  footer: {
    flexDirection: 'row',
    padding: 20,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.light.border,
  },
  cancelButton: {
    flex: 1,
    backgroundColor: Colors.light.surface,
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginRight: 12,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
  },
  saveButton: {
    flex: 2,
    borderRadius: 8,
  },
  saveButtonTouchable: {
    padding: 16,
    alignItems: 'center',
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
});