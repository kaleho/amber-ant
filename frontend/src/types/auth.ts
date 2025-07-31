import { PersonaType } from './persona'

export interface User {
  id: string
  email: string
  name: string
  persona: PersonaType
  preferences: UserPreferences
  family_id?: string
  family_role?: FamilyRole
  created_at: string
  updated_at: string
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  notifications: NotificationPreferences
  currency: string
  date_format: string
  language?: string
}

export interface NotificationPreferences {
  email: boolean
  push: boolean
  sms: boolean
  frequency: 'immediate' | 'daily' | 'weekly' | 'monthly'
}

export type FamilyRole = 
  | 'administrator'
  | 'member'
  | 'child'
  | 'viewer'

export interface FamilyMember {
  user_id: string
  name: string
  email: string
  persona: PersonaType
  role: FamilyRole
  permissions: FamilyPermissions
  created_at: string
}

export interface FamilyPermissions {
  view_finances: boolean
  edit_budget: boolean
  manage_accounts: boolean
  approve_transactions: boolean
  manage_members: boolean
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (updates: Partial<User>) => Promise<void>
  switchPersona: (persona: PersonaType) => Promise<void>
}