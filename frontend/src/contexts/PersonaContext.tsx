/**
 * Persona Context for User Interface Adaptation
 * Manages persona-specific UI configurations and business logic
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { PersonaType, PersonaUIConfig, AccessibilityFeatures } from '../types';
import { PERSONA_CONFIG } from '../constants/Config';
import { PersonaColors } from '../constants/Colors';
import { useAuth } from './AuthContext';

interface PersonaContextType {
  // Current persona state
  currentPersona: PersonaType | null;
  personaConfig: PersonaUIConfig | null;
  isPersonaLoading: boolean;
  
  // Persona methods
  setPersona: (persona: PersonaType) => Promise<void>;
  getPersonaColors: () => any;
  getPersonaFeatures: () => string[];
  getPersonaRestrictions: () => string[];
  updateAccessibilityFeatures: (features: Partial<AccessibilityFeatures>) => Promise<void>;
  updateUIPreferences: (preferences: Partial<PersonaUIConfig>) => Promise<void>;
  
  // Persona-specific business logic
  shouldShowFeature: (feature: string) => boolean;
  getComplexityLevel: () => 'simple' | 'moderate' | 'advanced';
  getNavigationStyle: () => 'bottom' | 'drawer' | 'stack';
  isGamificationEnabled: () => boolean;
  
  // Accessibility helpers
  shouldUseLargeText: () => boolean;
  shouldUseHighContrast: () => boolean;
  shouldUseHapticFeedback: () => boolean;
  shouldUseVoiceNavigation: () => boolean;
  shouldReduceMotion: () => boolean;
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

const STORAGE_KEY = '@faithful_finances_persona_config';

// Default persona configurations
const DEFAULT_PERSONA_CONFIGS: Record<PersonaType, PersonaUIConfig> = {
  pre_teen: {
    persona: 'pre_teen',
    theme_preference: 'light',
    navigation_style: 'bottom',
    complexity_level: 'simple',
    accessibility_features: {
      large_text: true,
      high_contrast: false,
      voice_navigation: true,
      haptic_feedback: true,
      reduced_motion: false,
    },
    gamification_enabled: true,
  },
  
  teen: {
    persona: 'teen',
    theme_preference: 'auto',
    navigation_style: 'bottom',
    complexity_level: 'moderate',
    accessibility_features: {
      large_text: false,
      high_contrast: false,
      voice_navigation: false,
      haptic_feedback: true,
      reduced_motion: false,
    },
    gamification_enabled: true,
  },
  
  college_student: {
    persona: 'college_student',
    theme_preference: 'dark',
    navigation_style: 'bottom',
    complexity_level: 'moderate',
    accessibility_features: {
      large_text: false,
      high_contrast: false,
      voice_navigation: false,
      haptic_feedback: true,
      reduced_motion: false,
    },
    gamification_enabled: false,
  },
  
  single_adult: {
    persona: 'single_adult',
    theme_preference: 'auto',
    navigation_style: 'drawer',
    complexity_level: 'advanced',
    accessibility_features: {
      large_text: false,
      high_contrast: false,
      voice_navigation: false,
      haptic_feedback: false,
      reduced_motion: false,
    },
    gamification_enabled: false,
  },
  
  married_couple: {
    persona: 'married_couple',
    theme_preference: 'auto',
    navigation_style: 'drawer',
    complexity_level: 'advanced',
    accessibility_features: {
      large_text: false,
      high_contrast: false,
      voice_navigation: false,
      haptic_feedback: false,
      reduced_motion: false,
    },
    gamification_enabled: false,
  },
  
  single_parent: {
    persona: 'single_parent',
    theme_preference: 'auto',
    navigation_style: 'bottom',
    complexity_level: 'moderate',
    accessibility_features: {
      large_text: false,
      high_contrast: false,
      voice_navigation: false,
      haptic_feedback: true,
      reduced_motion: false,
    },
    gamification_enabled: false,
  },
  
  two_parent_family: {
    persona: 'two_parent_family',
    theme_preference: 'auto',
    navigation_style: 'drawer',
    complexity_level: 'advanced',
    accessibility_features: {
      large_text: false,
      high_contrast: false,
      voice_navigation: false,
      haptic_feedback: false,
      reduced_motion: false,
    },
    gamification_enabled: false,
  },
  
  fixed_income: {
    persona: 'fixed_income',
    theme_preference: 'light',
    navigation_style: 'drawer',
    complexity_level: 'simple',
    accessibility_features: {
      large_text: true,
      high_contrast: true,
      voice_navigation: true,
      haptic_feedback: false,
      reduced_motion: true,
    },
    gamification_enabled: false,
  },
};

// Feature availability by persona
const PERSONA_FEATURES: Record<PersonaType, string[]> = {
  pre_teen: [
    'basic_budgeting',
    'savings_goals',
    'tithing_tracking',
    'parental_oversight',
    'gamification',
    'educational_content',
  ],
  
  teen: [
    'basic_budgeting',
    'bank_connection',
    'savings_goals',
    'tithing_tracking',
    'achievement_system',
    'educational_content',
    'part_time_job_tracking',
  ],
  
  college_student: [
    'full_budgeting',
    'bank_connection',
    'savings_goals',
    'tithing_tracking',
    'student_loan_tracking',
    'irregular_income',
    'semester_planning',
  ],
  
  single_adult: [
    'full_budgeting',
    'bank_connection',
    'investment_tracking',
    'savings_goals',
    'tithing_tracking',
    'advanced_analytics',
    'tax_optimization',
    'career_planning',
  ],
  
  married_couple: [
    'full_budgeting',
    'bank_connection',
    'investment_tracking',
    'savings_goals',
    'tithing_tracking',
    'advanced_analytics',
    'family_management',
    'spouse_coordination',
    'joint_planning',
  ],
  
  single_parent: [
    'full_budgeting',
    'bank_connection',
    'savings_goals',
    'tithing_tracking',
    'family_management',
    'crisis_prevention',
    'child_expense_tracking',
    'priority_alerts',
  ],
  
  two_parent_family: [
    'full_budgeting',
    'bank_connection',
    'investment_tracking',
    'savings_goals',
    'tithing_tracking',
    'advanced_analytics',
    'family_management',
    'dual_income_coordination',
    'children_planning',
    'extended_family',
  ],
  
  fixed_income: [
    'simplified_budgeting',
    'bank_connection',
    'savings_goals',
    'tithing_tracking',
    'healthcare_tracking',
    'retirement_planning',
    'simplified_interface',
    'legacy_planning',
  ],
};

interface PersonaProviderProps {
  children: ReactNode;
}

export const PersonaProvider: React.FC<PersonaProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const [currentPersona, setCurrentPersona] = useState<PersonaType | null>(null);
  const [personaConfig, setPersonaConfig] = useState<PersonaUIConfig | null>(null);
  const [isPersonaLoading, setIsPersonaLoading] = useState(true);

  // Initialize persona when user changes
  useEffect(() => {
    if (user) {
      initializePersona(user.persona);
    } else {
      setCurrentPersona(null);
      setPersonaConfig(null);
    }
  }, [user]);

  const initializePersona = async (persona: PersonaType) => {
    try {
      setIsPersonaLoading(true);
      
      // Try to load saved persona config from storage
      const storedConfig = await AsyncStorage.getItem(STORAGE_KEY);
      
      if (storedConfig) {
        const parsedConfig: PersonaUIConfig = JSON.parse(storedConfig);
        
        // Make sure the stored config matches the current persona
        if (parsedConfig.persona === persona) {
          setCurrentPersona(persona);
          setPersonaConfig(parsedConfig);
          return;
        }
      }
      
      // No stored config or persona mismatch, use default
      const defaultConfig = DEFAULT_PERSONA_CONFIGS[persona];
      setCurrentPersona(persona);
      setPersonaConfig({ ...defaultConfig });
      
      // Save default config to storage
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(defaultConfig));
      
    } catch (error) {
      console.error('Error initializing persona:', error);
      
      // Fallback to default config
      const defaultConfig = DEFAULT_PERSONA_CONFIGS[persona];
      setCurrentPersona(persona);
      setPersonaConfig({ ...defaultConfig });
    } finally {
      setIsPersonaLoading(false);
    }
  };

  const setPersona = async (persona: PersonaType) => {
    try {
      const newConfig = DEFAULT_PERSONA_CONFIGS[persona];
      
      setCurrentPersona(persona);
      setPersonaConfig({ ...newConfig });
      
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(newConfig));
    } catch (error) {
      console.error('Error setting persona:', error);
    }
  };

  const updateAccessibilityFeatures = async (features: Partial<AccessibilityFeatures>) => {
    if (!personaConfig) return;
    
    const updatedConfig = {
      ...personaConfig,
      accessibility_features: {
        ...personaConfig.accessibility_features,
        ...features,
      },
    };
    
    setPersonaConfig(updatedConfig);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updatedConfig));
  };

  const updateUIPreferences = async (preferences: Partial<PersonaUIConfig>) => {
    if (!personaConfig) return;
    
    const updatedConfig = {
      ...personaConfig,
      ...preferences,
    };
    
    setPersonaConfig(updatedConfig);
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(updatedConfig));
  };

  const getPersonaColors = () => {
    if (!currentPersona) return PersonaColors.single_adult;
    return PersonaColors[currentPersona] || PersonaColors.single_adult;
  };

  const getPersonaFeatures = (): string[] => {
    if (!currentPersona) return [];
    return PERSONA_FEATURES[currentPersona] || [];
  };

  const getPersonaRestrictions = (): string[] => {
    if (!currentPersona) return [];
    return PERSONA_CONFIG[currentPersona]?.restrictions || [];
  };

  const shouldShowFeature = (feature: string): boolean => {
    const features = getPersonaFeatures();
    return features.includes(feature);
  };

  const getComplexityLevel = (): 'simple' | 'moderate' | 'advanced' => {
    return personaConfig?.complexity_level || 'moderate';
  };

  const getNavigationStyle = (): 'bottom' | 'drawer' | 'stack' => {
    return personaConfig?.navigation_style || 'bottom';
  };

  const isGamificationEnabled = (): boolean => {
    return personaConfig?.gamification_enabled || false;
  };

  // Accessibility helpers
  const shouldUseLargeText = (): boolean => {
    return personaConfig?.accessibility_features.large_text || false;
  };

  const shouldUseHighContrast = (): boolean => {
    return personaConfig?.accessibility_features.high_contrast || false;
  };

  const shouldUseHapticFeedback = (): boolean => {
    return personaConfig?.accessibility_features.haptic_feedback || false;
  };

  const shouldUseVoiceNavigation = (): boolean => {
    return personaConfig?.accessibility_features.voice_navigation || false;
  };

  const shouldReduceMotion = (): boolean => {
    return personaConfig?.accessibility_features.reduced_motion || false;
  };

  const contextValue: PersonaContextType = {
    currentPersona,
    personaConfig,
    isPersonaLoading,
    setPersona,
    getPersonaColors,
    getPersonaFeatures,
    getPersonaRestrictions,
    updateAccessibilityFeatures,
    updateUIPreferences,
    shouldShowFeature,
    getComplexityLevel,
    getNavigationStyle,
    isGamificationEnabled,
    shouldUseLargeText,
    shouldUseHighContrast,
    shouldUseHapticFeedback,
    shouldUseVoiceNavigation,
    shouldReduceMotion,
  };

  return (
    <PersonaContext.Provider value={contextValue}>
      {children}
    </PersonaContext.Provider>
  );
};

export const usePersona = (): PersonaContextType => {
  const context = useContext(PersonaContext);
  if (context === undefined) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
};