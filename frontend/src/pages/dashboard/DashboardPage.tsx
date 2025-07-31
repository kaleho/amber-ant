import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';

// Persona-specific dashboard imports
import { PreTeenDashboard } from './personas/PreTeenDashboard';
import { TeenDashboard } from './personas/TeenDashboard';
import { CollegeStudentDashboard } from './personas/CollegeStudentDashboard';
import { SingleAdultDashboard } from './personas/SingleAdultDashboard';
import { MarriedCoupleDashboard } from './personas/MarriedCoupleDashboard';
import { SingleParentDashboard } from './personas/SingleParentDashboard';
import { TwoParentFamilyDashboard } from './personas/TwoParentFamilyDashboard';
import { FixedIncomeDashboard } from './personas/FixedIncomeDashboard';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }

  // Route to persona-specific dashboard
  switch (user.persona) {
    case 'pre_teen':
      return <PreTeenDashboard />;
    case 'teen':
      return <TeenDashboard />;
    case 'college_student':
      return <CollegeStudentDashboard />;
    case 'single_adult':
      return <SingleAdultDashboard />;
    case 'married_couple':
      return <MarriedCoupleDashboard />;
    case 'single_parent':
      return <SingleParentDashboard />;
    case 'two_parent_family':
      return <TwoParentFamilyDashboard />;
    case 'fixed_income':
      return <FixedIncomeDashboard />;
    default:
      // Fallback to single adult dashboard
      return <SingleAdultDashboard />;
  }
};