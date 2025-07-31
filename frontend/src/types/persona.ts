export type PersonaType = 
  | 'pre_teen'
  | 'teen'
  | 'college_student'
  | 'single_adult'
  | 'married_couple'
  | 'single_parent'
  | 'two_parent_family'
  | 'fixed_income'

export interface PersonaConfig {
  id: PersonaType
  name: string
  displayName: string
  ageRange: string
  description: string
  capabilities: {
    plaidIntegration: boolean
    parentalOversight: boolean
    familyManagement: boolean
    advancedFeatures: boolean
  }
  ui: {
    fontSize: 'small' | 'medium' | 'large'
    complexity: 'simple' | 'moderate' | 'advanced'
    primaryColor: string
    iconStyle: 'colorful' | 'minimal' | 'outlined'
  }
  features: {
    tithing: boolean
    budgeting: boolean
    savings: boolean
    plaidAccounts: boolean
    parentalApproval: boolean
    goalSetting: boolean
    notifications: boolean
    reports: boolean
  }
}

export const PERSONA_CONFIGS: Record<PersonaType, PersonaConfig> = {
  pre_teen: {
    id: 'pre_teen',
    name: 'Pre-Teen',
    displayName: 'Young Steward',
    ageRange: '8-14 years',
    description: 'Learning money management with parental guidance',
    capabilities: {
      plaidIntegration: false,
      parentalOversight: true,
      familyManagement: false,
      advancedFeatures: false,
    },
    ui: {
      fontSize: 'large',
      complexity: 'simple',
      primaryColor: '#22c55e',
      iconStyle: 'colorful',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: false,
      parentalApproval: true,
      goalSetting: true,
      notifications: false,
      reports: false,
    },
  },
  teen: {
    id: 'teen',
    name: 'Teen',
    displayName: 'Growing Steward',
    ageRange: '15-17 years',
    description: 'Developing financial independence with oversight',
    capabilities: {
      plaidIntegration: true,
      parentalOversight: true,
      familyManagement: false,
      advancedFeatures: false,
    },
    ui: {
      fontSize: 'medium',
      complexity: 'moderate',
      primaryColor: '#3b82f6',
      iconStyle: 'outlined',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: true,
      parentalApproval: true,
      goalSetting: true,
      notifications: true,
      reports: false,
    },
  },
  college_student: {
    id: 'college_student',
    name: 'College Student',
    displayName: 'Student Steward',
    ageRange: '18-22 years',
    description: 'Managing finances independently during education',
    capabilities: {
      plaidIntegration: true,
      parentalOversight: false,
      familyManagement: false,
      advancedFeatures: false,
    },
    ui: {
      fontSize: 'medium',
      complexity: 'moderate',
      primaryColor: '#8b5cf6',
      iconStyle: 'minimal',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: true,
      parentalApproval: false,
      goalSetting: true,
      notifications: true,
      reports: true,
    },
  },
  single_adult: {
    id: 'single_adult',
    name: 'Single Adult',
    displayName: 'Independent Steward',
    ageRange: '25-40 years',
    description: 'Full financial independence and stewardship',
    capabilities: {
      plaidIntegration: true,
      parentalOversight: false,
      familyManagement: false,
      advancedFeatures: true,
    },
    ui: {
      fontSize: 'medium',
      complexity: 'advanced',
      primaryColor: '#2563eb',
      iconStyle: 'minimal',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: true,
      parentalApproval: false,
      goalSetting: true,
      notifications: true,
      reports: true,
    },
  },
  married_couple: {
    id: 'married_couple',
    name: 'Married Couple',
    displayName: 'Joint Stewards',
    ageRange: '25-65 years',
    description: 'Shared financial management and stewardship',
    capabilities: {
      plaidIntegration: true,
      parentalOversight: false,
      familyManagement: true,
      advancedFeatures: true,
    },
    ui: {
      fontSize: 'medium',
      complexity: 'advanced',
      primaryColor: '#dc2626',
      iconStyle: 'minimal',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: true,
      parentalApproval: false,
      goalSetting: true,
      notifications: true,
      reports: true,
    },
  },
  single_parent: {
    id: 'single_parent',
    name: 'Single Parent',
    displayName: 'Family Steward',
    ageRange: '25-45 years',
    description: 'Managing family finances with time constraints',
    capabilities: {
      plaidIntegration: true,
      parentalOversight: false,
      familyManagement: true,
      advancedFeatures: true,
    },
    ui: {
      fontSize: 'medium',
      complexity: 'moderate',
      primaryColor: '#f59e0b',
      iconStyle: 'outlined',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: true,
      parentalApproval: false,
      goalSetting: true,
      notifications: true,
      reports: true,
    },
  },
  two_parent_family: {
    id: 'two_parent_family',
    name: 'Two Parent Family',
    displayName: 'Family Stewards',
    ageRange: '30-50 years',
    description: 'Coordinated family financial management',
    capabilities: {
      plaidIntegration: true,
      parentalOversight: false,
      familyManagement: true,
      advancedFeatures: true,
    },
    ui: {
      fontSize: 'medium',
      complexity: 'advanced',
      primaryColor: '#059669',
      iconStyle: 'minimal',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: true,
      parentalApproval: false,
      goalSetting: true,
      notifications: true,
      reports: true,
    },
  },
  fixed_income: {
    id: 'fixed_income',
    name: 'Fixed Income',
    displayName: 'Wise Steward',
    ageRange: '55+ years',
    description: 'Managing retirement and fixed income resources',
    capabilities: {
      plaidIntegration: true,
      parentalOversight: false,
      familyManagement: false,
      advancedFeatures: false,
    },
    ui: {
      fontSize: 'large',
      complexity: 'simple',
      primaryColor: '#6b7280',
      iconStyle: 'outlined',
    },
    features: {
      tithing: true,
      budgeting: true,
      savings: true,
      plaidAccounts: true,
      parentalApproval: false,
      goalSetting: true,
      notifications: true,
      reports: true,
    },
  },
}