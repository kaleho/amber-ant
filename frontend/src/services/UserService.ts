/**
 * User Service
 * Handles user profile management and Auth0 integration
 */

import { Auth0User } from 'react-native-auth0';
import { API_CONFIG } from '../constants/Config';
import { User, UserPreferences, PersonaType } from '../types';
import { apiClient } from './ApiClient';

export class UserService {
  /**
   * Get or create user profile from Auth0 user data
   */
  static async getOrCreateUser(auth0User: Auth0User, accessToken: string): Promise<User> {
    try {
      // First try to get existing user
      const response = await apiClient.get<User>(API_CONFIG.ENDPOINTS.USERS.PROFILE);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      // User doesn't exist, create new one
      const newUser: Partial<User> = {
        email: auth0User.email,
        name: auth0User.name || auth0User.nickname || 'Unknown User',
        persona: this.inferPersona(auth0User),
        preferences: this.getDefaultPreferences(),
      };
      
      const createResponse = await apiClient.post<User>(API_CONFIG.ENDPOINTS.USERS.PROFILE, newUser);
      
      if (createResponse.success && createResponse.data) {
        return createResponse.data;
      }
      
      throw new Error('Failed to create user profile');
    } catch (error) {
      console.error('Error getting or creating user:', error);
      throw error;
    }
  }

  /**
   * Get user profile
   */
  static async getProfile(accessToken?: string): Promise<User> {
    const response = await apiClient.get<User>(API_CONFIG.ENDPOINTS.USERS.PROFILE);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to get user profile');
  }

  /**
   * Update user profile
   */
  static async updateProfile(updates: Partial<User>): Promise<User> {
    const response = await apiClient.patch<User>(API_CONFIG.ENDPOINTS.USERS.PROFILE, updates);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to update user profile');
  }

  /**
   * Update user preferences
   */
  static async updatePreferences(preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const response = await apiClient.patch<UserPreferences>(
      API_CONFIG.ENDPOINTS.USERS.PREFERENCES, 
      preferences
    );
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to update user preferences');
  }

  /**
   * Change user persona
   */
  static async changePersona(persona: PersonaType): Promise<User> {
    const response = await apiClient.patch<User>(API_CONFIG.ENDPOINTS.USERS.PROFILE, { persona });
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to change persona');
  }

  /**
   * Delete user account
   */
  static async deleteAccount(): Promise<void> {
    const response = await apiClient.delete(API_CONFIG.ENDPOINTS.USERS.PROFILE);
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete account');
    }
  }

  /**
   * Get user subscription status
   */
  static async getSubscription() {
    const response = await apiClient.get(API_CONFIG.ENDPOINTS.USERS.SUBSCRIPTION);
    
    if (response.success) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to get subscription status');
  }

  /**
   * Infer persona from Auth0 user metadata
   */
  private static inferPersona(auth0User: Auth0User): PersonaType {
    // Check for persona in user metadata
    const userMetadata = auth0User.user_metadata as any;
    if (userMetadata?.persona) {
      return userMetadata.persona as PersonaType;
    }
    
    // Check for age-based inference
    const appMetadata = auth0User.app_metadata as any;
    if (appMetadata?.age) {
      const age = parseInt(appMetadata.age);
      if (age >= 8 && age <= 14) return 'pre_teen';
      if (age >= 15 && age <= 17) return 'teen';
      if (age >= 18 && age <= 22) return 'college_student';
      if (age >= 55) return 'fixed_income';
    }
    
    // Check for family status indicators
    if (appMetadata?.family_status) {
      const familyStatus = appMetadata.family_status;
      if (familyStatus === 'single_parent') return 'single_parent';
      if (familyStatus === 'married') return 'married_couple';
      if (familyStatus === 'family') return 'two_parent_family';
    }
    
    // Default to single adult
    return 'single_adult';
  }

  /**
   * Get default user preferences
   */
  private static getDefaultPreferences(): UserPreferences {
    return {
      theme: 'auto',
      notifications: {
        email: true,
        push: true,
        sms: false,
        frequency: 'daily',
      },
      currency: 'USD',
      date_format: 'MM/DD/YYYY',
    };
  }

  /**
   * Generate user analytics data (privacy-conscious)
   */
  static async getUserAnalytics(): Promise<any> {
    const response = await apiClient.get('/analytics/user');
    
    if (response.success) {
      return response.data;
    }
    
    return null;
  }

  /**
   * Export user data (GDPR compliance)
   */
  static async exportUserData(): Promise<Blob> {
    const response = await apiClient.downloadFile('/users/export');
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to export user data');
  }

  /**
   * Request data deletion (GDPR compliance)
   */
  static async requestDataDeletion(): Promise<void> {
    const response = await apiClient.post('/users/delete-request');
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to request data deletion');
    }
  }

  /**
   * Verify email address
   */
  static async verifyEmail(token: string): Promise<void> {
    const response = await apiClient.post('/auth/verify-email', { token });
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to verify email');
    }
  }

  /**
   * Request password reset
   */
  static async requestPasswordReset(email: string): Promise<void> {
    const response = await apiClient.post('/auth/reset-password', { email });
    
    if (!response.success) {
      throw new Error(response.error || 'Failed to request password reset');
    }
  }

  /**
   * Check if user has completed onboarding
   */
  static async hasCompletedOnboarding(): Promise<boolean> {
    try {
      const user = await this.getProfile();
      
      // Check if user has set up basic information
      return !!(
        user.persona &&
        user.preferences &&
        user.created_at &&
        new Date(user.created_at) < new Date(Date.now() - 24 * 60 * 60 * 1000) // Created more than 24 hours ago
      );
    } catch (error) {
      return false;
    }
  }

  /**
   * Complete onboarding process
   */
  static async completeOnboarding(onboardingData: {
    persona: PersonaType;
    preferences: Partial<UserPreferences>;
    additionalInfo?: any;
  }): Promise<User> {
    const response = await apiClient.post<User>('/users/complete-onboarding', onboardingData);
    
    if (response.success && response.data) {
      return response.data;
    }
    
    throw new Error(response.error || 'Failed to complete onboarding');
  }
}