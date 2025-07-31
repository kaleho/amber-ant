/**
 * Authentication Context with Auth0 Integration (Web)
 * Manages user authentication state and Auth0 operations for web application
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useAuth0, User as Auth0User } from '@auth0/auth0-react';
import { User, PersonaType } from '@/types';

interface AuthContextType {
  // Authentication state
  user: User | null;
  auth0User: Auth0User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Authentication methods
  login: () => void;
  logout: () => void;
  clearError: () => void;
  
  // Token management
  getAccessTokenSilently: () => Promise<string>;
  
  // User profile management
  updateUserProfile: (updates: Partial<User>) => Promise<void>;
  switchPersona: (persona: PersonaType) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const {
    user: auth0User,
    isAuthenticated,
    isLoading: auth0Loading,
    error: auth0Error,
    loginWithRedirect,
    logout: auth0Logout,
    getAccessTokenSilently: getAuth0Token,
  } = useAuth0();

  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize user profile when authenticated
  useEffect(() => {
    if (isAuthenticated && auth0User && !user) {
      initializeUserProfile();
    } else if (!isAuthenticated) {
      setUser(null);
      setIsLoading(false);
    }
  }, [isAuthenticated, auth0User]);

  // Handle Auth0 errors
  useEffect(() => {
    if (auth0Error) {
      setError(auth0Error.message);
    }
  }, [auth0Error]);

  const initializeUserProfile = async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (!auth0User) return;

      // Try to get existing user profile from our API
      const token = await getAuth0Token();
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        // User exists in our system
        const existingUser = await response.json();
        setUser(existingUser);
      } else if (response.status === 404) {
        // New user - create profile based on Auth0 data
        const newUser = await createUserProfile(auth0User, token);
        setUser(newUser);
      } else {
        throw new Error('Failed to fetch user profile');
      }
    } catch (error: any) {
      console.error('Error initializing user profile:', error);
      setError(error.message || 'Failed to initialize user profile');
    } finally {
      setIsLoading(false);
    }
  };

  const createUserProfile = async (auth0User: Auth0User, token: string): Promise<User> => {
    const userData = {
      email: auth0User.email!,
      name: auth0User.name || auth0User.email!,
      persona: 'single_adult' as PersonaType, // Default persona
      preferences: {
        theme: 'auto' as const,
        notifications: {
          email: true,
          push: true,
          sms: false,
          frequency: 'daily' as const,
        },
        currency: 'USD',
        date_format: 'MM/DD/YYYY' as const,
      },
    };

    const response = await fetch('/api/v1/users', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      throw new Error('Failed to create user profile');
    }

    return response.json();
  };

  const login = () => {
    loginWithRedirect({
      authorizationParams: {
        redirect_uri: window.location.origin,
      },
    });
  };

  const logout = () => {
    auth0Logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
    setUser(null);
  };

  const getAccessTokenSilently = async (): Promise<string> => {
    try {
      return await getAuth0Token();
    } catch (error) {
      console.error('Error getting access token:', error);
      throw error;
    }
  };

  const updateUserProfile = async (updates: Partial<User>): Promise<void> => {
    try {
      if (!user) throw new Error('User not authenticated');

      const token = await getAccessTokenSilently();
      const response = await fetch(`/api/v1/users/${user.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error('Failed to update user profile');
      }

      const updatedUser = await response.json();
      setUser(updatedUser);
    } catch (error: any) {
      setError(error.message || 'Failed to update profile');
      throw error;
    }
  };

  const switchPersona = async (persona: PersonaType): Promise<void> => {
    try {
      await updateUserProfile({ persona });
    } catch (error: any) {
      setError(error.message || 'Failed to switch persona');
      throw error;
    }
  };

  const clearError = () => {
    setError(null);
  };

  const contextValue: AuthContextType = {
    user,
    auth0User,
    isAuthenticated,
    isLoading: auth0Loading || isLoading,
    error,
    login,
    logout,
    clearError,
    getAccessTokenSilently,
    updateUserProfile,
    switchPersona,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};