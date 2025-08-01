/**
 * Persona Context for User Interface Adaptation (Web Version)
 * Manages persona-specific UI configurations and business logic
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
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
  getRecommendedBudgetCategories: () => string[];
  getPersonalizedInsights: () => string[];
  getTailoredTips: () => string[];
}

const PersonaContext = createContext<PersonaContextType | undefined>(undefined);

export const PersonaProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [currentPersona, setCurrentPersona] = useState<PersonaType | null>(null);
  const [personaConfig, setPersonaConfig] = useState<PersonaUIConfig | null>(null);
  const [isPersonaLoading, setIsPersonaLoading] = useState(false);

  // Initialize persona on mount or user change
  useEffect(() => {
    if (user) {
      initializePersona();
    }
  }, [user]);

  const initializePersona = async () => {
    try {
      setIsPersonaLoading(true);
      
      // Try to load stored persona from localStorage
      const storedPersona = localStorage.getItem('user_persona') as PersonaType;
      const storedConfig = localStorage.getItem('persona_config');

      if (storedPersona && PERSONA_CONFIG[storedPersona]) {
        setCurrentPersona(storedPersona);
        
        if (storedConfig) {
          setPersonaConfig(JSON.parse(storedConfig));
        } else {
          setPersonaConfig(PERSONA_CONFIG[storedPersona]);
        }
      } else {
        // Default to single_adult persona if none stored
        const defaultPersona: PersonaType = 'single_adult';
        setCurrentPersona(defaultPersona);
        setPersonaConfig(PERSONA_CONFIG[defaultPersona]);
        
        // Store default persona
        localStorage.setItem('user_persona', defaultPersona);
        localStorage.setItem('persona_config', JSON.stringify(PERSONA_CONFIG[defaultPersona]));
      }
    } catch (error) {
      console.error('Error initializing persona:', error);
      // Fallback to single_adult
      const fallbackPersona: PersonaType = 'single_adult';
      setCurrentPersona(fallbackPersona);
      setPersonaConfig(PERSONA_CONFIG[fallbackPersona]);
    } finally {
      setIsPersonaLoading(false);
    }
  };

  const setPersona = async (persona: PersonaType): Promise<void> => {
    try {
      setIsPersonaLoading(true);
      
      const config = PERSONA_CONFIG[persona];
      if (!config) {
        throw new Error(`Invalid persona: ${persona}`);
      }

      setCurrentPersona(persona);
      setPersonaConfig(config);

      // Store in localStorage
      localStorage.setItem('user_persona', persona);
      localStorage.setItem('persona_config', JSON.stringify(config));
    } catch (error) {
      console.error('Error setting persona:', error);
      throw error;
    } finally {
      setIsPersonaLoading(false);
    }
  };

  const getPersonaColors = () => {
    if (!currentPersona) return PersonaColors.default;
    return PersonaColors[currentPersona] || PersonaColors.default;
  };

  const getPersonaFeatures = (): string[] => {
    if (!personaConfig) return [];
    return personaConfig.features || [];
  };

  const getPersonaRestrictions = (): string[] => {
    if (!personaConfig) return [];
    return personaConfig.restrictions || [];
  };

  const updateAccessibilityFeatures = async (features: Partial<AccessibilityFeatures>): Promise<void> => {
    if (!personaConfig) return;

    const currentFeatures = personaConfig.accessibility || {};
    const updatedFeatures = { ...currentFeatures, ...features };
    
    const updatedConfig = {
      ...personaConfig,
      accessibility: updatedFeatures
    };

    setPersonaConfig(updatedConfig);
    localStorage.setItem('persona_accessibility', JSON.stringify(updatedFeatures));
  };

  const updateUIPreferences = async (preferences: Partial<PersonaUIConfig>): Promise<void> => {
    if (!personaConfig) return;

    const updatedConfig = { ...personaConfig, ...preferences };
    setPersonaConfig(updatedConfig);
    localStorage.setItem('persona_config', JSON.stringify(updatedConfig));
  };

  const shouldShowFeature = (feature: string): boolean => {
    if (!personaConfig) return true;
    
    const restrictions = personaConfig.restrictions || [];
    const features = personaConfig.features || [];
    
    // If explicitly restricted, don't show
    if (restrictions.includes(feature)) return false;
    
    // If no specific features defined, show everything not restricted
    if (features.length === 0) return true;
    
    // If features are defined, only show if included
    return features.includes(feature);
  };

  const getComplexityLevel = (): 'simple' | 'moderate' | 'advanced' => {
    if (!personaConfig) return 'moderate';
    return personaConfig.complexityLevel || 'moderate';
  };

  const getNavigationStyle = (): 'bottom' | 'drawer' | 'stack' => {
    if (!personaConfig) return 'drawer';
    return personaConfig.navigationStyle || 'drawer';
  };

  const getRecommendedBudgetCategories = (): string[] => {
    if (!currentPersona) return [];
    
    const recommendations = {
      pre_teen: ['Allowance', 'Savings', 'Giving', 'Fun Money'],
      teen: ['Allowance', 'Job Income', 'Savings', 'Giving', 'Entertainment', 'Transportation'],
      college_student: ['Financial Aid', 'Part-time Job', 'Food', 'Books', 'Entertainment', 'Savings'],
      single_adult: ['Salary', 'Housing', 'Food', 'Transportation', 'Savings', 'Giving', 'Entertainment'],
      married_couple: ['Combined Income', 'Housing', 'Food', 'Transportation', 'Savings', 'Giving', 'Date Nights'],
      single_parent: ['Income', 'Housing', 'Childcare', 'Food', 'Transportation', 'Emergency Fund', 'Giving'],
      two_parent_family: ['Family Income', 'Housing', 'Childcare', 'Food', 'Transportation', 'Education', 'Giving'],
      fixed_income: ['Pension/SS', 'Healthcare', 'Housing', 'Food', 'Transportation', 'Emergency Fund']
    };

    return recommendations[currentPersona] || [];
  };

  const getPersonalizedInsights = (): string[] => {
    if (!currentPersona) return [];
    
    const insights = {
      pre_teen: [
        "Great job learning about money!",
        "Remember to save part of your allowance",
        "Giving to others makes God happy"
      ],
      teen: [
        "You're building great money habits!",
        "Consider opening a savings account",
        "Learn about budgeting before college"
      ],
      college_student: [
        "Track your spending to avoid debt",
        "Look for student discounts everywhere",
        "Start building credit responsibly"
      ],
      single_adult: [
        "Build an emergency fund of 3-6 months expenses",
        "Consider increasing your giving as income grows",
        "Start investing for retirement early"
      ],
      married_couple: [
        "Communicate openly about financial goals",
        "Consider joint vs separate accounts",
        "Plan for future family expenses"
      ],
      single_parent: [
        "Focus on building your emergency fund",
        "Look into assistance programs if needed",
        "Teach your children about money management"
      ],
      two_parent_family: [
        "Budget for growing family expenses",
        "Start education savings early",
        "Involve kids in age-appropriate money decisions"
      ],
      fixed_income: [
        "Focus on essential expenses first",
        "Look for senior discounts",
        "Consider healthcare cost planning"
      ]
    };

    return insights[currentPersona] || [];
  };

  const getTailoredTips = (): string[] => {
    if (!currentPersona) return [];
    
    const tips = {
      pre_teen: [
        "Use a clear jar to see your savings grow",
        "Count your money regularly",
        "Ask parents before making purchases"
      ],
      teen: [
        "Use apps to track your spending",
        "Save money from your job for big goals",
        "Learn the difference between needs and wants"
      ],
      college_student: [
        "Take advantage of student meal plans",
        "Buy used textbooks when possible",
        "Avoid credit card debt"
      ],
      single_adult: [
        "Automate your savings and giving",
        "Review your budget monthly",
        "Invest in your professional development"
      ],
      married_couple: [
        "Have regular money meetings",
        "Set shared financial goals",
        "Celebrate financial milestones together"
      ],
      single_parent: [
        "Build a support network for financial advice",
        "Take advantage of family assistance programs",
        "Plan fun, low-cost activities with kids"
      ],
      two_parent_family: [
        "Teach kids through family financial activities",
        "Plan for education expenses early",
        "Create family financial traditions"
      ],
      fixed_income: [
        "Take advantage of senior discounts",
        "Consider downsizing if appropriate",
        "Plan for healthcare expenses"
      ]
    };

    return tips[currentPersona] || [];
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
    getRecommendedBudgetCategories,
    getPersonalizedInsights,
    getTailoredTips
  };

  return (
    <PersonaContext.Provider value={contextValue}>
      {children}
    </PersonaContext.Provider>
  );
};

export const usePersona = (): PersonaContextType => {
  const context = useContext(PersonaContext);
  if (!context) {
    throw new Error('usePersona must be used within a PersonaProvider');
  }
  return context;
};