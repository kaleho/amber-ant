import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { PersonaType, FamilyRole } from '@/types';

interface PersonaRouteProps {
  children: React.ReactNode;
  allowedPersonas?: PersonaType[];
  allowedRoles?: FamilyRole[];
}

export const PersonaRoute: React.FC<PersonaRouteProps> = ({ 
  children, 
  allowedPersonas,
  allowedRoles 
}) => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }

  // Check persona access
  if (allowedPersonas && !allowedPersonas.includes(user.persona)) {
    return <Navigate to="/dashboard" replace />;
  }

  // Check role access (for family members)
  if (allowedRoles && user.family_role && !allowedRoles.includes(user.family_role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};