/**
 * Color Constants for Faithful Finances
 * Persona-adaptive color system with accessibility support
 */

export const Colors = {
  // Light Theme Colors
  light: {
    // Primary Brand Colors
    primary: '#2E7D32',         // Green - Stewardship & Growth
    primaryVariant: '#1B5E20',  // Darker Green
    secondary: '#1976D2',       // Blue - Trust & Reliability
    secondaryVariant: '#0D47A1', // Darker Blue
    
    // Surface Colors
    background: '#FFFFFF',
    surface: '#F8F9FA',
    card: '#FFFFFF',
    
    // Text Colors
    text: '#212121',
    textSecondary: '#757575',
    textDisabled: '#BDBDBD',
    
    // Status Colors
    success: '#4CAF50',         // Green - Success states
    warning: '#FF9800',         // Orange - Warnings
    error: '#F44336',           // Red - Errors
    info: '#2196F3',            // Blue - Information
    
    // Financial Colors
    income: '#4CAF50',          // Green for income
    expense: '#F44336',         // Red for expenses
    fixed: '#1976D2',           // Blue for fixed expenses (needs)
    discretionary: '#FF9800',   // Orange for discretionary expenses (wants)
    tithing: '#9C27B0',         // Purple for tithing/giving
    savings: '#00BCD4',         // Cyan for savings goals
    
    // UI Element Colors
    border: '#E0E0E0',
    divider: '#E0E0E0',
    disabled: '#F5F5F5',
    placeholder: '#9E9E9E',
    shadow: 'rgba(0, 0, 0, 0.1)',
    
    // Button Colors
    buttonPrimary: '#2E7D32',
    buttonSecondary: '#E8F5E8',
    buttonDisabled: '#E0E0E0',
    
    // Overlay Colors
    overlay: 'rgba(0, 0, 0, 0.5)',
    backdropLight: 'rgba(255, 255, 255, 0.9)',
  },
  
  // Dark Theme Colors
  dark: {
    // Primary Brand Colors
    primary: '#66BB6A',         // Lighter Green for dark theme
    primaryVariant: '#4CAF50',  // Medium Green
    secondary: '#42A5F5',       // Lighter Blue
    secondaryVariant: '#2196F3', // Medium Blue
    
    // Surface Colors
    background: '#121212',
    surface: '#1E1E1E',
    card: '#2D2D2D',
    
    // Text Colors
    text: '#FFFFFF',
    textSecondary: '#AAAAAA',
    textDisabled: '#666666',
    
    // Status Colors
    success: '#66BB6A',         // Lighter green for dark theme
    warning: '#FFB74D',         // Lighter orange
    error: '#EF5350',           // Lighter red
    info: '#42A5F5',            // Lighter blue
    
    // Financial Colors
    income: '#66BB6A',          // Lighter green for income
    expense: '#EF5350',         // Lighter red for expenses
    fixed: '#42A5F5',           // Lighter blue for fixed expenses
    discretionary: '#FFB74D',   // Lighter orange for discretionary
    tithing: '#BA68C8',         // Lighter purple for tithing
    savings: '#26C6DA',         // Lighter cyan for savings
    
    // UI Element Colors
    border: '#333333',
    divider: '#333333',
    disabled: '#2A2A2A',
    placeholder: '#666666',
    shadow: 'rgba(0, 0, 0, 0.3)',
    
    // Button Colors
    buttonPrimary: '#66BB6A',
    buttonSecondary: '#2A4A2A',
    buttonDisabled: '#333333',
    
    // Overlay Colors
    overlay: 'rgba(0, 0, 0, 0.7)',
    backdropDark: 'rgba(18, 18, 18, 0.9)',
  },
  
  // High Contrast Theme (for accessibility)
  highContrast: {
    // Primary Colors with maximum contrast
    primary: '#000000',
    primaryVariant: '#000000',
    secondary: '#FFFFFF',
    secondaryVariant: '#FFFFFF',
    
    // Surface Colors
    background: '#FFFFFF',
    surface: '#FFFFFF',
    card: '#FFFFFF',
    
    // Text Colors
    text: '#000000',
    textSecondary: '#000000',
    textDisabled: '#666666',
    
    // Status Colors (high contrast)
    success: '#006600',         // Dark green
    warning: '#CC6600',         // Dark orange
    error: '#CC0000',           // Dark red
    info: '#0066CC',            // Dark blue
    
    // Financial Colors (high contrast)
    income: '#006600',
    expense: '#CC0000',
    fixed: '#0066CC',
    discretionary: '#CC6600',
    tithing: '#660066',
    savings: '#006666',
    
    // UI Element Colors
    border: '#000000',
    divider: '#000000',
    disabled: '#CCCCCC',
    placeholder: '#666666',
    shadow: 'rgba(0, 0, 0, 0.5)',
    
    // Button Colors
    buttonPrimary: '#000000',
    buttonSecondary: '#FFFFFF',
    buttonDisabled: '#CCCCCC',
    
    // Overlay Colors
    overlay: 'rgba(0, 0, 0, 0.8)',
    backdropHigh: 'rgba(255, 255, 255, 0.95)',
  },
};

// Persona-specific color variations
export const PersonaColors = {
  pre_teen: {
    primary: '#4CAF50',         // Bright green
    secondary: '#FF9800',       // Fun orange
    accent: '#E91E63',          // Pink accent
    background: '#F3E5F5',      // Light purple background
    gamification: {
      bronze: '#CD7F32',
      silver: '#C0C0C0',
      gold: '#FFD700',
      diamond: '#B9F2FF',
    },
  },
  
  teen: {
    primary: '#2196F3',         // Modern blue
    secondary: '#9C27B0',       // Purple
    accent: '#00BCD4',          // Cyan accent
    background: '#FAFAFA',      // Clean white
    achievement: {
      level1: '#4CAF50',
      level2: '#FF9800',
      level3: '#F44336',
      level4: '#9C27B0',
    },
  },
  
  college_student: {
    primary: '#FF5722',         // Energetic orange
    secondary: '#795548',       // Brown (earthy)
    accent: '#607D8B',          // Blue grey
    background: '#FFF3E0',      // Light orange background
    budget: {
      critical: '#F44336',      // Red for low funds
      warning: '#FF9800',       // Orange for caution
      safe: '#4CAF50',          // Green for healthy
    },
  },
  
  single_adult: {
    primary: '#1976D2',         // Professional blue
    secondary: '#424242',       // Neutral grey
    accent: '#00BCD4',          // Teal accent
    background: '#FFFFFF',      // Clean white
    professional: {
      investment: '#4CAF50',
      career: '#2196F3',
      networking: '#9C27B0',
      development: '#FF9800',
    },
  },
  
  married_couple: {
    primary: '#8BC34A',         // Harmonious green
    secondary: '#FFC107',       // Warm yellow
    accent: '#E91E63',          // Pink accent
    background: '#F1F8E9',      // Light green background
    joint: {
      shared: '#4CAF50',
      individual: '#2196F3',
      discussion: '#FF9800',
      conflict: '#F44336',
    },
  },
  
  single_parent: {
    primary: '#F44336',         // Alert red (priorities)
    secondary: '#2196F3',       // Trustworthy blue
    accent: '#4CAF50',          // Hopeful green
    background: '#FFF8F0',      // Warm background
    priority: {
      critical: '#F44336',      // Emergency/critical
      important: '#FF9800',     // Important tasks
      routine: '#2196F3',       // Regular tasks
      future: '#4CAF50',        // Future planning
    },
  },
  
  two_parent_family: {
    primary: '#4CAF50',         // Family green
    secondary: '#FF9800',       // Warm orange
    accent: '#9C27B0',          // Purple accent
    background: '#E8F5E8',      // Light green background
    family: {
      parent1: '#2196F3',
      parent2: '#9C27B0',
      children: '#FF9800',
      joint: '#4CAF50',
    },
  },
  
  fixed_income: {
    primary: '#795548',         // Stable brown
    secondary: '#607D8B',       // Blue grey
    accent: '#4CAF50',          // Positive green
    background: '#FFF8E1',      // Light yellow background
    healthcare: {
      essential: '#4CAF50',     // Green for essential
      optional: '#FF9800',      // Orange for optional
      emergency: '#F44336',     // Red for emergency
      covered: '#2196F3',       // Blue for covered
    },
  },
};

// Gradient definitions
export const Gradients = {
  primary: ['#2E7D32', '#66BB6A'],
  secondary: ['#1976D2', '#42A5F5'],
  success: ['#388E3C', '#66BB6A'],
  warning: ['#F57C00', '#FFB74D'],
  error: ['#D32F2F', '#EF5350'],
  
  // Financial gradients
  income: ['#388E3C', '#66BB6A'],
  expense: ['#D32F2F', '#EF5350'],
  fixed: ['#1565C0', '#42A5F5'],
  discretionary: ['#F57C00', '#FFB74D'],
  tithing: ['#7B1FA2', '#BA68C8'],
  savings: ['#0097A7', '#26C6DA'],
  
  // Persona gradients
  preTeenGradient: ['#E91E63', '#F8BBD9'],
  teenGradient: ['#2196F3', '#90CAF9'],
  collegeGradient: ['#FF5722', '#FFAB91'],
  adultGradient: ['#1976D2', '#90CAF9'],
  familyGradient: ['#4CAF50', '#A5D6A7'],
  seniorGradient: ['#795548', '#BCAAA4'],
};

// Utility functions
export const getPersonaColor = (persona: string, colorType: string = 'primary') => {
  const personaColorMap = PersonaColors[persona as keyof typeof PersonaColors];
  if (personaColorMap) {
    return personaColorMap[colorType as keyof typeof personaColorMap] || Colors.light.primary;
  }
  return Colors.light.primary;
};

export const getContrastText = (backgroundColor: string) => {
  // Simple contrast calculation - in production, use a proper library
  const hex = backgroundColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const brightness = (r * 299 + g * 587 + b * 114) / 1000;
  return brightness > 128 ? '#000000' : '#FFFFFF';
};

export const getExpenseTypeColor = (expenseType: 'fixed' | 'discretionary', theme: 'light' | 'dark' = 'light') => {
  return expenseType === 'fixed' ? Colors[theme].fixed : Colors[theme].discretionary;
};

export const getCategoryColor = (category: string, theme: 'light' | 'dark' = 'light') => {
  const categoryColorMap: Record<string, string> = {
    groceries: Colors[theme].success,
    transportation: Colors[theme].info,
    housing: Colors[theme].primary,
    utilities: Colors[theme].secondary,
    health: Colors[theme].error,
    entertainment: Colors[theme].discretionary,
    education: Colors[theme].info,
    clothing: Colors[theme].secondary,
    dining: Colors[theme].warning,
    shopping: Colors[theme].discretionary,
    charity: Colors[theme].tithing,
    default: Colors[theme].text,
  };
  
  return categoryColorMap[category] || categoryColorMap.default;
};