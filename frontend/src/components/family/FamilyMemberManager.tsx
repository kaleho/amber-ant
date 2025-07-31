/**
 * Family Member Management Component
 * Comprehensive family plan management with role-based permissions
 * Supports all persona types and family coordination workflows
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import LinearGradient from 'react-native-linear-gradient';
import HapticFeedback from 'react-native-haptic-feedback';
import { format } from 'date-fns';

import { Family, FamilyMember, FamilyRole, FamilyInvitation } from '../../types';
import { Colors } from '../../constants/Colors';
import { useAuth } from '../../contexts/AuthContext';
import { usePersona } from '../../contexts/PersonaContext';
import { FamilyService } from '../../services/FamilyService';

interface FamilyMemberManagerProps {
  family: Family | null;
  onInviteMemberPress: () => void;
  onMemberPress: (member: FamilyMember) => void;
  onInvitationPress: (invitation: FamilyInvitation) => void;
  onRefresh?: () => Promise<void>;
}

const ROLE_COLORS: Record<FamilyRole, string> = {
  administrator: Colors.light.primary,
  spouse: Colors.light.secondary,
  teen: Colors.light.info,
  pre_teen: Colors.light.success,
  support: Colors.light.warning,
  agent: Colors.light.textSecondary,
};

const ROLE_ICONS: Record<FamilyRole, string> = {
  administrator: 'admin-panel-settings',
  spouse: 'favorite',
  teen: 'school',
  pre_teen: 'child-care',
  support: 'support-agent',
  agent: 'smart-toy',
};

const ROLE_DESCRIPTIONS: Record<FamilyRole, string> = {
  administrator: 'Full access to all family financial data and settings',
  spouse: 'Joint access to shared accounts and family goals',
  teen: 'Supervised access with parental oversight and spending limits',
  pre_teen: 'Basic access with full parental supervision required',
  support: 'Time-limited technical assistance access',
  agent: 'Automated process control with admin oversight',
};

export const FamilyMemberManager: React.FC<FamilyMemberManagerProps> = ({
  family,
  onInviteMemberPress,
  onMemberPress,
  onInvitationPress,
  onRefresh,
}) => {
  const { user } = useAuth();
  const { shouldUseHapticFeedback, currentPersona } = usePersona();
  
  const [pendingInvitations, setPendingInvitations] = useState<FamilyInvitation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const isAdministrator = user && family && family.administrator_id === user.id;
  const currentMember = family?.members.find(member => member.user_id === user?.id);

  useEffect(() => {
    if (family) {
      loadPendingInvitations();
    }
  }, [family]);

  const loadPendingInvitations = async () => {
    if (!family) return;

    try {
      const invitations = await FamilyService.getPendingInvitations(family.id);
      setPendingInvitations(invitations);
    } catch (error) {
      console.error('Error loading pending invitations:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      if (onRefresh) {
        await onRefresh();
      }
      await loadPendingInvitations();
    } catch (error) {
      console.error('Error refreshing family data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleRemoveMember = async (member: FamilyMember) => {
    if (!family || !isAdministrator) return;

    Alert.alert(
      'Remove Family Member',
      `Are you sure you want to remove ${member.name} from your family plan?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsLoading(true);
              await FamilyService.removeMember(family.id, member.id);
              
              if (shouldUseHapticFeedback()) {
                HapticFeedback.trigger('notificationSuccess');
              }
              
              if (onRefresh) {
                await onRefresh();
              }
            } catch (error) {
              console.error('Error removing member:', error);
              Alert.alert('Error', 'Failed to remove family member');
              
              if (shouldUseHapticFeedback()) {
                HapticFeedback.trigger('notificationError');
              }
            } finally {
              setIsLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleCancelInvitation = async (invitation: FamilyInvitation) => {
    if (!isAdministrator) return;

    Alert.alert(
      'Cancel Invitation',
      `Cancel the invitation sent to ${invitation.email}?`,
      [
        { text: 'No', style: 'cancel' },
        {
          text: 'Cancel Invitation',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsLoading(true);
              await FamilyService.cancelInvitation(invitation.id);
              
              if (shouldUseHapticFeedback()) {
                HapticFeedback.trigger('impactMedium');
              }
              
              await loadPendingInvitations();
            } catch (error) {
              console.error('Error canceling invitation:', error);
              Alert.alert('Error', 'Failed to cancel invitation');
            } finally {
              setIsLoading(false);
            }
          },
        },
      ]
    );
  };

  const getRoleDisplayName = (role: FamilyRole): string => {
    const roleNames: Record<FamilyRole, string> = {
      administrator: 'Administrator',
      spouse: 'Spouse',
      teen: 'Teen',
      pre_teen: 'Pre-Teen',
      support: 'Support',
      agent: 'Agent',
    };
    return roleNames[role];
  };

  const getStatusDisplayName = (status: 'active' | 'pending' | 'suspended'): string => {
    const statusNames = {
      active: 'Active',
      pending: 'Pending',
      suspended: 'Suspended',
    };
    return statusNames[status];
  };

  const getStatusColor = (status: 'active' | 'pending' | 'suspended'): string => {
    const statusColors = {
      active: Colors.light.success,
      pending: Colors.light.warning,
      suspended: Colors.light.error,
    };
    return statusColors[status];
  };

  const renderFamilyHeader = () => {
    if (!family) return null;

    return (
      <View style={styles.familyHeader}>
        <LinearGradient
          colors={[Colors.light.primary, Colors.light.primaryVariant]}
          style={styles.familyHeaderGradient}
        >
          <View style={styles.familyHeaderContent}>
            <View style={styles.familyHeaderIcon}>
              <Icon name="family-restroom" size={32} color="white" />
            </View>
            
            <View style={styles.familyHeaderInfo}>
              <Text style={styles.familyName}>{family.name}</Text>
              <Text style={styles.familyMemberCount}>
                {family.members.length} member{family.members.length !== 1 ? 's' : ''}
              </Text>
            </View>
            
            {isAdministrator && (
              <TouchableOpacity
                style={styles.inviteButton}
                onPress={onInviteMemberPress}
                disabled={isLoading}
              >
                <Icon name="person-add" size={20} color="white" />
                <Text style={styles.inviteButtonText}>Invite</Text>
              </TouchableOpacity>
            )}
          </View>
        </LinearGradient>
      </View>
    );
  };

  const renderMemberCard = (member: FamilyMember) => {
    const isCurrentUser = member.user_id === user?.id;
    const canManage = isAdministrator && !isCurrentUser;
    const roleColor = ROLE_COLORS[member.role];
    const roleIcon = ROLE_ICONS[member.role];

    return (
      <TouchableOpacity
        key={member.id}
        style={[styles.memberCard, { borderLeftColor: roleColor }]}
        onPress={() => onMemberPress(member)}
        disabled={isLoading}
      >
        <View style={styles.memberCardContent}>
          <View style={styles.memberInfo}>
            <View style={[styles.memberAvatar, { backgroundColor: `${roleColor}20` }]}>
              <Icon name={roleIcon} size={24} color={roleColor} />
            </View>
            
            <View style={styles.memberDetails}>
              <View style={styles.memberNameRow}>
                <Text style={styles.memberName}>
                  {member.name}
                  {isCurrentUser && <Text style={styles.youLabel}> (You)</Text>}
                </Text>
                <View style={[styles.roleChip, { backgroundColor: `${roleColor}15` }]}>
                  <Text style={[styles.roleChipText, { color: roleColor }]}>
                    {getRoleDisplayName(member.role)}
                  </Text>
                </View>
              </View>
              
              <Text style={styles.memberEmail}>{member.email}</Text>
              
              <View style={styles.memberMeta}>
                <View style={styles.statusIndicator}>
                  <View style={[styles.statusDot, { backgroundColor: getStatusColor(member.status) }]} />
                  <Text style={styles.statusText}>{getStatusDisplayName(member.status)}</Text>
                </View>
                
                <Text style={styles.joinedDate}>
                  Joined {format(new Date(member.joined_at), 'MMM d, yyyy')}
                </Text>
              </View>
            </View>
          </View>
          
          <View style={styles.memberActions}>
            {canManage && (
              <TouchableOpacity
                style={styles.removeButton}
                onPress={() => handleRemoveMember(member)}
                disabled={isLoading}
              >
                <Icon name="remove-circle-outline" size={20} color={Colors.light.error} />
              </TouchableOpacity>
            )}
            
            <TouchableOpacity style={styles.detailsButton}>
              <Icon name="chevron-right" size={20} color={Colors.light.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>
        
        {member.permissions.requires_approval_over !== null && (
          <View style={styles.permissionsInfo}>
            <Icon name="security" size={14} color={Colors.light.info} />
            <Text style={styles.permissionsText}>
              Requires approval for purchases over ${member.permissions.requires_approval_over?.toFixed(2)}
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderPendingInvitations = () => {
    if (pendingInvitations.length === 0 || !isAdministrator) return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Pending Invitations</Text>
        
        {pendingInvitations.map((invitation) => (
          <TouchableOpacity
            key={invitation.id}
            style={styles.invitationCard}
            onPress={() => onInvitationPress(invitation)}
            disabled={isLoading}
          >
            <View style={styles.invitationContent}>
              <View style={styles.invitationInfo}>
                <View style={styles.invitationAvatar}>
                  <Icon name="mail-outline" size={20} color={Colors.light.warning} />
                </View>
                
                <View style={styles.invitationDetails}>
                  <Text style={styles.invitationEmail}>{invitation.email}</Text>
                  <Text style={styles.invitationRole}>
                    Invited as {getRoleDisplayName(invitation.role)}
                  </Text>
                  <Text style={styles.invitationDate}>
                    Sent {format(new Date(invitation.created_at), 'MMM d, yyyy')} • 
                    Expires {format(new Date(invitation.expires_at), 'MMM d')}
                  </Text>
                </View>
              </View>
              
              <TouchableOpacity
                style={styles.cancelInvitationButton}
                onPress={() => handleCancelInvitation(invitation)}
                disabled={isLoading}
              >
                <Icon name="cancel" size={20} color={Colors.light.error} />
              </TouchableOpacity>
            </View>
            
            {invitation.message && (
              <Text style={styles.invitationMessage}>"{invitation.message}"</Text>
            )}
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderPermissionsOverview = () => {
    if (!currentMember || currentPersona === 'pre_teen') return null;

    return (
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your Permissions</Text>
        
        <View style={styles.permissionsCard}>
          <View style={styles.permissionsList}>
            <View style={styles.permissionItem}>
              <Icon 
                name={currentMember.permissions.can_view_accounts ? 'check-circle' : 'cancel'} 
                size={16} 
                color={currentMember.permissions.can_view_accounts ? Colors.light.success : Colors.light.error} 
              />
              <Text style={styles.permissionText}>View family accounts</Text>
            </View>
            
            <View style={styles.permissionItem}>
              <Icon 
                name={currentMember.permissions.can_view_transactions ? 'check-circle' : 'cancel'} 
                size={16} 
                color={currentMember.permissions.can_view_transactions ? Colors.light.success : Colors.light.error} 
              />
              <Text style={styles.permissionText}>View transactions</Text>
            </View>
            
            <View style={styles.permissionItem}>
              <Icon 
                name={currentMember.permissions.can_manage_budget ? 'check-circle' : 'cancel'} 
                size={16} 
                color={currentMember.permissions.can_manage_budget ? Colors.light.success : Colors.light.error} 
              />
              <Text style={styles.permissionText}>Manage budgets</Text>
            </View>
            
            <View style={styles.permissionItem}>
              <Icon 
                name={currentMember.permissions.can_approve_spending ? 'check-circle' : 'cancel'} 
                size={16} 
                color={currentMember.permissions.can_approve_spending ? Colors.light.success : Colors.light.error} 
              />
              <Text style={styles.permissionText}>Approve spending</Text>
            </View>
            
            <View style={styles.permissionItem}>
              <Icon 
                name={currentMember.permissions.can_invite_members ? 'check-circle' : 'cancel'} 
                size={16} 
                color={currentMember.permissions.can_invite_members ? Colors.light.success : Colors.light.error} 
              />
              <Text style={styles.permissionText}>Invite family members</Text>
            </View>
          </View>
          
          {currentMember.permissions.requires_approval_over !== null && (
            <View style={styles.spendingLimitInfo}>
              <Icon name="warning" size={16} color={Colors.light.warning} />
              <Text style={styles.spendingLimitText}>
                You need approval for purchases over ${currentMember.permissions.requires_approval_over.toFixed(2)}
              </Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  if (!family) {
    return (
      <View style={styles.emptyState}>
        <Icon name="family-restroom" size={64} color={Colors.light.textSecondary} />
        <Text style={styles.emptyStateTitle}>No Family Plan</Text>
        <Text style={styles.emptyStateText}>
          Create or join a family plan to manage finances together
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
      }
    >
      {renderFamilyHeader()}
      
      <View style={styles.content}>
        {renderPendingInvitations()}
        
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Family Members</Text>
          
          {family.members.map(renderMemberCard)}
        </View>
        
        {renderPermissionsOverview()}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  familyHeader: {
    marginBottom: 20,
  },
  familyHeaderGradient: {
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  familyHeaderContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  familyHeaderIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  familyHeaderInfo: {
    flex: 1,
  },
  familyName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  familyMemberCount: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
  },
  inviteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  inviteButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 6,
  },
  content: {
    padding: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.light.text,
    marginBottom: 16,
  },
  memberCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    elevation: 1,
    shadowColor: Colors.light.shadow,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  memberCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  memberInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  memberAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  memberDetails: {
    flex: 1,
  },
  memberNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  memberName: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
  },
  youLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.light.primary,
  },
  roleChip: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  roleChipText: {
    fontSize: 12,
    fontWeight: '600',
  },
  memberEmail: {
    fontSize: 14,
    color: Colors.light.textSecondary,
    marginBottom: 6,
  },
  memberMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  statusText: {
    fontSize: 12,
    color: Colors.light.textSecondary,
  },
  joinedDate: {
    fontSize: 12,
    color: Colors.light.textSecondary,
  },
  memberActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  removeButton: {
    padding: 8,
    marginRight: 4,
  },
  detailsButton: {
    padding: 4,
  },
  permissionsInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.light.border,
  },
  permissionsText: {
    fontSize: 12,
    color: Colors.light.info,
    marginLeft: 6,
  },
  invitationCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.light.warning + '30',
  },
  invitationContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  invitationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  invitationAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.light.warning + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  invitationDetails: {
    flex: 1,
  },
  invitationEmail: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 2,
  },
  invitationRole: {
    fontSize: 14,
    color: Colors.light.textSecondary,
    marginBottom: 2,
  },
  invitationDate: {
    fontSize: 12,
    color: Colors.light.textSecondary,
  },
  cancelInvitationButton: {
    padding: 8,
  },
  invitationMessage: {
    fontSize: 14,
    color: Colors.light.textSecondary,
    fontStyle: 'italic',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.light.border,
  },
  permissionsCard: {
    backgroundColor: Colors.light.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  permissionsList: {
    marginBottom: 16,
  },
  permissionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  permissionText: {
    fontSize: 14,
    color: Colors.light.text,
    marginLeft: 8,
  },
  spendingLimitInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.light.warning + '15',
    padding: 12,
    borderRadius: 8,
  },
  spendingLimitText: {
    fontSize: 13,
    color: Colors.light.warning,
    marginLeft: 6,
    flex: 1,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  emptyStateTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.light.text,
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 16,
    color: Colors.light.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
});