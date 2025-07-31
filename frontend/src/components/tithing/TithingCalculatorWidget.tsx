/**
 * Tithing Calculator Widget Component
 * Comprehensive tithing calculation and tracking system
 * Supports all personas with biblical stewardship principles
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  Modal,
  ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';
import HapticFeedback from 'react-native-haptic-feedback';
import { format, startOfYear, endOfYear } from 'date-fns';

import { TithingSummary, TithingPayment, PersonaType } from '../../types';
import { Colors } from '../../constants/Colors';
import { BUSINESS_RULES } from '../../constants/Config';
import { useAuth } from '../../contexts/AuthContext';
import { usePersona } from '../../contexts/PersonaContext';
import { TithingService } from '../../services/TithingService';

interface TithingCalculatorWidgetProps {
  tithingSummary?: TithingSummary | null;
  onRecordPayment: (payment: Omit<TithingPayment, 'id' | 'created_at'>) => Promise<void>;
  onRefresh?: () => Promise<void>;
  compact?: boolean;
}

export const TithingCalculatorWidget: React.FC<TithingCalculatorWidgetProps> = ({
  tithingSummary,
  onRecordPayment,
  onRefresh,
  compact = false,
}) => {
  const { user } = useAuth();
  const { currentPersona, shouldUseHapticFeedback } = usePersona();
  
  const [showCalculatorModal, setShowCalculatorModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [incomeAmount, setIncomeAmount] = useState('');
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'check' | 'online' | 'other'>('cash');
  const [recipient, setRecipient] = useState('');
  const [notes, setNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // Calculate tithe amounts
  const calculatedTithe = useMemo(() => {
    if (!incomeAmount || isNaN(parseFloat(incomeAmount))) return 0;
    return parseFloat(incomeAmount) * BUSINESS_RULES.TITHING.DEFAULT_PERCENTAGE;
  }, [incomeAmount]);

  // Get persona-specific messaging
  const getPersonaMessage = (): string => {
    const messages: Record<PersonaType, string> = {
      pre_teen: "Great job thinking about giving! Even small amounts matter to God. 🌟",
      teen: "Learning to give first builds a strong foundation for your financial future! 💪",
      college_student: "Faithful giving during tight times shows true stewardship. Keep it up! 📚",
      single_adult: "Consistent tithing demonstrates trust in God's provision. Well done! ✨",
      married_couple: "Joint giving strengthens your marriage and faith together. 💕",
      single_parent: "Your faithful giving is noticed by God, even when resources are tight. 🙏",
      two_parent_family: "Family giving teaches children about generosity and trust in God. 👨‍👩‍👧‍👦",
      fixed_income: "Faithful giving throughout life shows a lifetime of trust in God. 🕊️",
    };
    
    return messages[currentPersona || 'single_adult'];
  };

  // Get current giving status
  const givingStatus = useMemo(() => {
    if (!tithingSummary) return { status: 'unknown', message: 'Loading...', color: Colors.light.textSecondary };
    
    const percentage = tithingSummary.current_percentage;
    const balance = tithingSummary.balance;
    
    if (percentage >= 10) {
      return {
        status: 'faithful',
        message: 'Faithful Giver! 🎉',
        color: Colors.light.success,
      };
    } else if (percentage >= 8) {
      return {
        status: 'growing',
        message: 'Growing in Giving 📈',
        color: Colors.light.warning,
      };
    } else if (percentage >= 5) {
      return {
        status: 'starting',
        message: 'Good Start! 🌱',
        color: Colors.light.info,
      };
    } else {
      return {
        status: 'beginning',
        message: 'Beginning Journey 🚀',
        color: Colors.light.textSecondary,
      };
    }
  }, [tithingSummary]);

  const handleQuickTithe = (amount: number) => {
    setPaymentAmount(amount.toString());
    setShowPaymentModal(true);
    
    if (shouldUseHapticFeedback()) {
      HapticFeedback.trigger('impactLight');
    }
  };

  const handleRecordPayment = async () => {
    if (!paymentAmount || !recipient) {
      Alert.alert('Missing Information', 'Please enter payment amount and recipient');
      return;
    }

    const amount = parseFloat(paymentAmount);
    if (isNaN(amount) || amount <= 0) {
      Alert.alert('Invalid Amount', 'Please enter a valid payment amount');
      return;
    }

    setIsProcessing(true);

    try {
      const payment: Omit<TithingPayment, 'id' | 'created_at'> = {
        amount,
        date: new Date().toISOString().split('T')[0],
        method: paymentMethod,
        recipient,
        notes: notes || undefined,
      };

      await onRecordPayment(payment);
      
      // Reset form
      setPaymentAmount('');
      setRecipient('');
      setNotes('');
      setShowPaymentModal(false);
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('notificationSuccess');
      }
      
      // Refresh data
      if (onRefresh) {
        await onRefresh();
      }
      
    } catch (error) {
      console.error('Error recording payment:', error);
      Alert.alert('Error', 'Failed to record tithing payment');
      
      if (shouldUseHapticFeedback()) {
        HapticFeedback.trigger('notificationError');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const renderCompactView = () => {
    if (!tithingSummary) return null;

    return (
      <TouchableOpacity
        style={styles.compactContainer}
        onPress={() => setShowCalculatorModal(true)}
      >
        <LinearGradient
          colors={[Colors.light.tithing, Colors.light.primary]}
          style={styles.compactGradient}
        >
          <View style={styles.compactHeader}>
            <Icon name="volunteer-activism" size={20} color="white" />
            <Text style={styles.compactTitle}>Tithing</Text>
          </View>
          
          <View style={styles.compactStats}>
            <Text style={styles.compactPercentage}>
              {tithingSummary.current_percentage.toFixed(1)}%
            </Text>
            <Text style={styles.compactStatus}>{givingStatus.message}</Text>
          </View>
          
          {tithingSummary.balance < 0 && (
            <View style={styles.compactBalance}>
              <Text style={styles.compactBalanceText}>
                Behind: ${Math.abs(tithingSummary.balance).toFixed(2)}
              </Text>
            </View>
          )}
        </LinearGradient>
      </TouchableOpacity>
    );
  };

  const renderFullView = () => {
    if (!tithingSummary) return null;

    return (
      <View style={styles.fullContainer}>
        <LinearGradient
          colors={[Colors.light.tithing, Colors.light.primary]}
          style={styles.headerGradient}
        >
          <View style={styles.header}>
            <View style={styles.headerIcon}>
              <Icon name="volunteer-activism" size={32} color="white" />
            </View>
            
            <View style={styles.headerContent}>
              <Text style={styles.headerTitle}>Tithing Tracker</Text>
              <Text style={styles.headerSubtitle}>
                "Honor the Lord with your wealth" - Proverbs 3:9
              </Text>
            </View>
          </View>
        </LinearGradient>
        
        <View style={styles.content}>
          <View style={styles.summaryCard}>
            <View style={styles.summaryRow}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>This Year's Income</Text>
                <Text style={styles.summaryValue}>
                  ${tithingSummary.total_income.toLocaleString()}
                </Text>
              </View>
              
              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Tithe Due (10%)</Text>
                <Text style={styles.summaryValue}>
                  ${tithingSummary.total_tithe_due.toLocaleString()}
                </Text>
              </View>
            </View>
            
            <View style={styles.summaryRow}>
              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Amount Given</Text>
                <Text style={styles.summaryValue}>
                  ${tithingSummary.total_tithe_paid.toLocaleString()}
                </Text>
              </View>
              
              <View style={styles.summaryItem}>
                <Text style={styles.summaryLabel}>Current %</Text>
                <Text style={[styles.summaryValue, { color: givingStatus.color }]}>
                  {tithingSummary.current_percentage.toFixed(1)}%
                </Text>
              </View>
            </View>
            
            {tithingSummary.balance !== 0 && (
              <View style={[
                styles.balanceRow, 
                { backgroundColor: tithingSummary.balance < 0 ? Colors.light.error + '15' : Colors.light.success + '15' }
              ]}>
                <Icon 
                  name={tithingSummary.balance < 0 ? 'trending-down' : 'trending-up'} 
                  size={20} 
                  color={tithingSummary.balance < 0 ? Colors.light.error : Colors.light.success} 
                />
                <Text style={[
                  styles.balanceText,
                  { color: tithingSummary.balance < 0 ? Colors.light.error : Colors.light.success }
                ]}>
                  {tithingSummary.balance < 0 ? 'Behind by' : 'Ahead by'}: ${Math.abs(tithingSummary.balance).toFixed(2)}
                </Text>
              </View>
            )}
          </View>
          
          <View style={styles.statusCard}>
            <Text style={[styles.statusMessage, { color: givingStatus.color }]}>
              {givingStatus.message}
            </Text>
            <Text style={styles.personaMessage}>{getPersonaMessage()}</Text>
          </View>
          
          <View style={styles.quickActionsCard}>
            <Text style={styles.quickActionsTitle}>Quick Actions</Text>
            
            <View style={styles.quickActionButtons}>
              <TouchableOpacity
                style={styles.quickActionButton}
                onPress={() => setShowCalculatorModal(true)}
              >
                <Icon name="calculate" size={20} color={Colors.light.primary} />
                <Text style={styles.quickActionText}>Calculate</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.quickActionButton}
                onPress={() => setShowPaymentModal(true)}
              >
                <Icon name="payment" size={20} color={Colors.light.primary} />
                <Text style={styles.quickActionText}>Record Payment</Text>
              </TouchableOpacity>
              
              {tithingSummary.balance < 0 && (
                <TouchableOpacity
                  style={styles.quickActionButton}
                  onPress={() => handleQuickTithe(Math.abs(tithingSummary.balance))}
                >
                  <Icon name="flash-on" size={20} color={Colors.light.warning} />
                  <Text style={styles.quickActionText}>Catch Up</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
          
          {tithingSummary.recent_payments.length > 0 && (
            <View style={styles.recentPaymentsCard}>
              <Text style={styles.recentPaymentsTitle}>Recent Payments</Text>
              
              {tithingSummary.recent_payments.slice(0, 3).map((payment, index) => (
                <View key={payment.id} style={styles.paymentItem}>
                  <View style={styles.paymentInfo}>
                    <Text style={styles.paymentAmount}>${payment.amount.toFixed(2)}</Text>
                    <Text style={styles.paymentRecipient}>{payment.recipient}</Text>
                    <Text style={styles.paymentDate}>
                      {format(new Date(payment.date), 'MMM d, yyyy')} • {payment.method}
                    </Text>
                  </View>
                  
                  <Icon 
                    name="check-circle" 
                    size={20} 
                    color={Colors.light.success} 
                  />
                </View>
              ))}
            </View>
          )}
        </View>
      </View>
    );
  };

  const renderCalculatorModal = () => (
    <Modal
      visible={showCalculatorModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowCalculatorModal(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Tithe Calculator</Text>
          <TouchableOpacity onPress={() => setShowCalculatorModal(false)}>
            <Icon name="close" size={24} color={Colors.light.text} />
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          <View style={styles.calculatorCard}>
            <Text style={styles.calculatorTitle}>Calculate Your Tithe</Text>
            <Text style={styles.calculatorSubtitle}>
              Enter your income to calculate 10% tithe
            </Text>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Income Amount</Text>
              <TextInput
                style={styles.incomeInput}
                value={incomeAmount}
                onChangeText={setIncomeAmount}
                placeholder="0.00"
                keyboardType="numeric"
                placeholderTextColor={Colors.light.placeholder}
              />
            </View>
            
            {calculatedTithe > 0 && (
              <View style={styles.calculationResult}>
                <Text style={styles.calculationLabel}>Recommended Tithe (10%)</Text>
                <Text style={styles.calculationAmount}>
                  ${calculatedTithe.toFixed(2)}
                </Text>
                
                <TouchableOpacity
                  style={styles.recordButton}
                  onPress={() => {
                    setPaymentAmount(calculatedTithe.toFixed(2));
                    setShowCalculatorModal(false);
                    setShowPaymentModal(true);
                  }}
                >
                  <Text style={styles.recordButtonText}>Record This Payment</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
          
          <View style={styles.guidanceCard}>
            <Text style={styles.guidanceTitle}>💡 Tithing Guidance</Text>
            <Text style={styles.guidanceText}>
              Tithing is giving 10% of your income back to God as an act of worship and trust. 
              It's not about the amount, but about the heart of gratitude and faithfulness.
            </Text>
            
            <View style={styles.bibleVerseCard}>
              <Text style={styles.bibleVerse}>
                "Bring the whole tithe into the storehouse, that there may be food in my house. 
                Test me in this, says the Lord Almighty, and see if I will not throw open the 
                floodgates of heaven and pour out so much blessing that there will not be room 
                enough to store it." - Malachi 3:10
              </Text>
            </View>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  const renderPaymentModal = () => (
    <Modal
      visible={showPaymentModal}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowPaymentModal(false)}
    >
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Record Tithing Payment</Text>
          <TouchableOpacity onPress={() => setShowPaymentModal(false)}>
            <Icon name="close" size={24} color={Colors.light.text} />
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.modalContent}>
          <View style={styles.paymentForm}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Payment Amount *</Text>
              <TextInput
                style={styles.input}
                value={paymentAmount}
                onChangeText={setPaymentAmount}
                placeholder="0.00"
                keyboardType="numeric"
                placeholderTextColor={Colors.light.placeholder}
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Recipient *</Text>
              <TextInput
                style={styles.input}
                value={recipient}
                onChangeText={setRecipient}
                placeholder="Church or organization name"
                placeholderTextColor={Colors.light.placeholder}
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Payment Method</Text>
              <View style={styles.methodButtons}>
                {[
                  { key: 'cash', label: 'Cash', icon: 'payments' },
                  { key: 'check', label: 'Check', icon: 'receipt' },
                  { key: 'online', label: 'Online', icon: 'computer' },
                  { key: 'other', label: 'Other', icon: 'more-horiz' },
                ].map((method) => (
                  <TouchableOpacity
                    key={method.key}
                    style={[
                      styles.methodButton,
                      paymentMethod === method.key && styles.methodButtonSelected
                    ]}
                    onPress={() => setPaymentMethod(method.key as typeof paymentMethod)}
                  >
                    <Icon 
                      name={method.icon} 
                      size={20} 
                      color={paymentMethod === method.key ? 'white' : Colors.light.primary} 
                    />
                    <Text style={[
                      styles.methodButtonText,
                      paymentMethod === method.key && styles.methodButtonTextSelected
                    ]}>
                      {method.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Notes (Optional)</Text>
              <TextInput
                style={[styles.input, styles.notesInput]}
                value={notes}
                onChangeText={setNotes}
                placeholder="Additional notes about this payment"
                multiline
                numberOfLines={3}
                placeholderTextColor={Colors.light.placeholder}
              />
            </View>
            
            <TouchableOpacity
              style={[styles.submitButton, { opacity: isProcessing ? 0.7 : 1 }]}
              onPress={handleRecordPayment}
              disabled={isProcessing}
            >
              <LinearGradient
                colors={[Colors.light.tithing, Colors.light.primary]}
                style={styles.submitButtonGradient}
              >
                <Text style={styles.submitButtonText}>
                  {isProcessing ? 'Recording...' : 'Record Payment'}
                </Text>
              </LinearGradient>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  if (compact) {
    return (
      <>
        {renderCompactView()}
        {renderCalculatorModal()}
        {renderPaymentModal()}
      </>
    );
  }

  return (
    <>
      {renderFullView()}
      {renderCalculatorModal()}
      {renderPaymentModal()}
    </>
  );
};

const styles = StyleSheet.create({
  // Compact view styles
  compactContainer: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 12,
    overflow: 'hidden',
  },
  compactGradient: {
    padding: 16,
  },
  compactHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  compactTitle: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  compactStats: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 4,
  },
  compactPercentage: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
    marginRight: 8,
  },
  compactStatus: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 14,
    fontWeight: '500',
  },
  compactBalance: {
    marginTop: 4,
  },
  compactBalanceText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 12,
  },
  
  // Full view styles
  fullContainer: {
    backgroundColor: Colors.light.background,
    marginBottom: 20,
  },
  headerGradient: {
    paddingTop: 20,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    fontStyle: 'italic',
  },
  content: {
    padding: 20,
  },
  summaryCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    elevation: 1,
    shadowColor: Colors.light.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 14,
    color: Colors.light.textSecondary,
    textAlign: 'center',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.light.text,
    textAlign: 'center',
  },
  balanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  balanceText: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  statusCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    alignItems: 'center',
  },
  statusMessage: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  personaMessage: {
    fontSize: 16,
    color: Colors.light.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  quickActionsCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
  },
  quickActionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.light.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  quickActionButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  quickActionButton: {
    alignItems: 'center',
    padding: 12,
  },
  quickActionText: {
    fontSize: 14,
    color: Colors.light.primary,
    marginTop: 4,
    fontWeight: '500',
  },
  recentPaymentsCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 20,
  },
  recentPaymentsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.light.text,
    marginBottom: 16,
  },
  paymentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  paymentInfo: {
    flex: 1,
  },
  paymentAmount: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 2,
  },
  paymentRecipient: {
    fontSize: 14,
    color: Colors.light.textSecondary,
    marginBottom: 2,
  },
  paymentDate: {
    fontSize: 12,
    color: Colors.light.textSecondary,
  },
  
  // Modal styles
  modalContainer: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: Colors.light.border,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.light.text,
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  calculatorCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
  },
  calculatorTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.light.text,
    marginBottom: 4,
    textAlign: 'center',
  },
  calculatorSubtitle: {
    fontSize: 14,
    color: Colors.light.textSecondary,
    marginBottom: 20,
    textAlign: 'center',
  },
  inputGroup: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 8,
  },
  incomeInput: {
    backgroundColor: Colors.light.background,
    borderWidth: 2,
    borderColor: Colors.light.border,
    borderRadius: 8,
    padding: 16,
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    color: Colors.light.text,
  },
  calculationResult: {
    alignItems: 'center',
    marginTop: 20,
    padding: 20,
    backgroundColor: Colors.light.tithing + '15',
    borderRadius: 12,
  },
  calculationLabel: {
    fontSize: 16,
    color: Colors.light.textSecondary,
    marginBottom: 8,
  },
  calculationAmount: {
    fontSize: 32,
    fontWeight: 'bold',
    color: Colors.light.tithing,
    marginBottom: 16,
  },
  recordButton: {
    backgroundColor: Colors.light.tithing,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  recordButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  guidanceCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 20,
  },
  guidanceTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.light.text,
    marginBottom: 12,
  },
  guidanceText: {
    fontSize: 16,
    color: Colors.light.text,
    lineHeight: 22,
    marginBottom: 16,
  },
  bibleVerseCard: {
    backgroundColor: Colors.light.tithing + '15',
    borderRadius: 8,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: Colors.light.tithing,
  },
  bibleVerse: {
    fontSize: 14,
    color: Colors.light.text,
    fontStyle: 'italic',
    lineHeight: 20,
  },
  paymentForm: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 20,
  },
  input: {
    backgroundColor: Colors.light.background,
    borderWidth: 1,
    borderColor: Colors.light.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: Colors.light.text,
  },
  notesInput: {
    height: 80,
    textAlignVertical: 'top',
  },
  methodButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  methodButton: {
    flex: 1,
    alignItems: 'center',
    padding: 12,
    borderWidth: 1,
    borderColor: Colors.light.border,
    borderRadius: 8,
    marginHorizontal: 2,
  },
  methodButtonSelected: {
    backgroundColor: Colors.light.primary,
    borderColor: Colors.light.primary,
  },
  methodButtonText: {
    fontSize: 12,
    color: Colors.light.primary,
    marginTop: 4,
    fontWeight: '500',
  },
  methodButtonTextSelected: {
    color: 'white',
  },
  submitButton: {
    marginTop: 20,
    borderRadius: 8,
    overflow: 'hidden',
  },
  submitButtonGradient: {
    padding: 16,
    alignItems: 'center',
  },
  submitButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
});