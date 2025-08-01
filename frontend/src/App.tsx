import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { useAuth0 } from '@auth0/auth0-react';
import { queryClient } from '@/lib/api';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { BudgetProvider } from '@/contexts/BudgetContext';
import { FamilyProvider } from '@/contexts/FamilyContext';
import { TithingProvider } from '@/contexts/TithingContext';
import { PersonaProvider } from '@/contexts/PersonaContext';
import { Toaster } from 'sonner';

// Layout Components
import { RootLayout } from '@/components/layout/RootLayout';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { DashboardLayout } from '@/components/layout/DashboardLayout';

// Auth Pages
import { LoginPage } from '@/pages/auth/LoginPage';
import { SignupPage } from '@/pages/auth/SignupPage';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';

// Dashboard Pages
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { AccountsPage } from '@/pages/dashboard/AccountsPage';
import { TransactionsPage } from '@/pages/dashboard/TransactionsPage';
import { BudgetsPage } from '@/pages/dashboard/BudgetsPage';
import { GoalsPage } from '@/pages/dashboard/GoalsPage';
import { TithingPage } from '@/pages/dashboard/TithingPage';
import { FamilyPage } from '@/pages/family/FamilyPage';
import { SettingsPage } from '@/pages/settings/SettingsPage';

// Persona-specific pages
import { PreTeenDashboard } from '@/pages/dashboard/personas/PreTeenDashboard';
import { TeenDashboard } from '@/pages/dashboard/personas/TeenDashboard';
import { CollegeStudentDashboard } from '@/pages/dashboard/personas/CollegeStudentDashboard';
import { SingleAdultDashboard } from '@/pages/dashboard/personas/SingleAdultDashboard';
import { MarriedCoupleDashboard } from '@/pages/dashboard/personas/MarriedCoupleDashboard';
import { SingleParentDashboard } from '@/pages/dashboard/personas/SingleParentDashboard';
import { TwoParentFamilyDashboard } from '@/pages/dashboard/personas/TwoParentFamilyDashboard';
import { FixedIncomeDashboard } from '@/pages/dashboard/personas/FixedIncomeDashboard';

// Route Guards
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PersonaRoute } from '@/components/auth/PersonaRoute';

// Auth0 Loading Component
const Auth0LoadingWrapper = ({ children }: { children: React.ReactNode }) => {
  const { isLoading } = useAuth0();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background font-sans antialiased flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold mb-2">Faithful Finances</h2>
          <p className="text-muted-foreground">Loading your biblical stewardship journey...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="system" storageKey="faithful-finances-ui-theme">
        <AuthProvider>
          <Auth0LoadingWrapper>
            <PersonaProvider>
              <BudgetProvider>
                <FamilyProvider>
                  <TithingProvider>
                    <Router>
                      <div className="min-h-screen bg-background font-sans antialiased">
                        <Routes>
                        {/* Public routes */}
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        
                        {/* Demo routes for testing without auth */}
                        <Route path="/demo" element={<SingleAdultDashboard />} />
                        <Route path="/demo/goals" element={<GoalsPage />} />
                        <Route path="/demo/settings" element={<SettingsPage />} />
                        <Route path="/demo/accounts" element={<AccountsPage />} />
                        
                        {/* Auth routes */}
                        <Route element={<AuthLayout />}>
                          <Route path="/auth/login" element={<LoginPage />} />
                          <Route path="/auth/signup" element={<SignupPage />} />
                          <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
                        </Route>

                        {/* Protected routes */}
                        <Route element={<ProtectedRoute />}>
                          <Route element={<DashboardLayout />}>
                            {/* Default dashboard route */}
                            <Route path="/dashboard" element={<DashboardPage />} />
                            
                            {/* Persona-specific dashboards */}
                            <Route 
                              path="/dashboard/pre-teen" 
                              element={
                                <PersonaRoute allowedPersonas={['pre_teen']}>
                                  <PreTeenDashboard />
                                </PersonaRoute>
                              } 
                            />
                            <Route 
                              path="/dashboard/teen" 
                              element={
                                <PersonaRoute allowedPersonas={['teen']}>
                                  <TeenDashboard />
                                </PersonaRoute>
                              } 
                            />
                            <Route 
                              path="/dashboard/college-student" 
                              element={
                                <PersonaRoute allowedPersonas={['college_student']}>
                                  <CollegeStudentDashboard />
                                </PersonaRoute>
                              } 
                            />
                            <Route 
                              path="/dashboard/single-adult" 
                              element={
                                <PersonaRoute allowedPersonas={['single_adult']}>
                                  <SingleAdultDashboard />
                                </PersonaRoute>
                              } 
                            />
                            <Route 
                              path="/dashboard/married-couple" 
                              element={
                                <PersonaRoute allowedPersonas={['married_couple']}>
                                  <MarriedCoupleDashboard />
                                </PersonaRoute>
                              } 
                            />
                            <Route 
                              path="/dashboard/single-parent" 
                              element={
                                <PersonaRoute allowedPersonas={['single_parent']}>
                                  <SingleParentDashboard />
                                </PersonaRoute>
                              } 
                            />
                            <Route 
                              path="/dashboard/two-parent-family" 
                              element={
                                <PersonaRoute allowedPersonas={['two_parent_family']}>
                                  <TwoParentFamilyDashboard />
                                </PersonaRoute>
                              } 
                            />
                            <Route 
                              path="/dashboard/fixed-income" 
                              element={
                                <PersonaRoute allowedPersonas={['fixed_income']}>
                                  <FixedIncomeDashboard />
                                </PersonaRoute>
                              } 
                            />

                            {/* Feature pages */}
                            <Route path="/accounts" element={<AccountsPage />} />
                            <Route path="/transactions" element={<TransactionsPage />} />
                            <Route path="/budgets" element={<BudgetsPage />} />
                            <Route path="/goals" element={<GoalsPage />} />
                            <Route path="/tithing" element={<TithingPage />} />
                            <Route path="/family" element={<FamilyPage />} />
                            <Route path="/settings" element={<SettingsPage />} />
                          </Route>
                        </Route>

                        {/* Catch all route */}
                        <Route path="*" element={<Navigate to="/dashboard" replace />} />
                        </Routes>
                        
                        {/* Global toast notifications */}
                        <Toaster position="top-right" richColors />
                      </div>
                    </Router>
                  </TithingProvider>
                </FamilyProvider>
              </BudgetProvider>
            </PersonaProvider>
          </Auth0LoadingWrapper>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;