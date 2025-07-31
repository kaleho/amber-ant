/**
 * Login Page with Auth0 Integration
 * Handles user authentication with persona-based redirection
 */

import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useToast } from '@/hooks/use-toast';

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated, isLoading, error, user, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  // Redirect authenticated users to their persona dashboard
  useEffect(() => {
    if (isAuthenticated && user) {
      const from = (location.state as any)?.from?.pathname || getPersonaDashboardPath(user.persona);
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location]);

  // Show error toast when error occurs
  useEffect(() => {
    if (error) {
      toast({
        title: 'Authentication Error',
        description: error,
        variant: 'destructive',
      });
      clearError();
    }
  }, [error, toast, clearError]);

  const getPersonaDashboardPath = (persona: string): string => {
    const personaPaths: Record<string, string> = {
      pre_teen: '/dashboard/pre-teen',
      teen: '/dashboard/teen',
      college_student: '/dashboard/college-student',
      single_adult: '/dashboard/single-adult',
      married_couple: '/dashboard/married-couple',
      single_parent: '/dashboard/single-parent',
      two_parent_family: '/dashboard/two-parent-family',
      fixed_income: '/dashboard/fixed-income',
    };
    return personaPaths[persona] || '/dashboard';
  };

  const handleLogin = () => {
    login();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <LoadingSpinner size="lg" />
            <p className="mt-4 text-muted-foreground">Signing you in...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-purple-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-900">
            Welcome to Faithful Finances
          </CardTitle>
          <CardDescription className="text-gray-600">
            Biblical stewardship for your financial journey
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Biblical verse */}
          <div className="text-center p-4 bg-blue-50 rounded-lg border-l-4 border-blue-500">
            <p className="text-sm text-blue-800 italic">
              "For where your treasure is, there your heart will be also."
            </p>
            <p className="text-xs text-blue-600 mt-1">Matthew 6:21</p>
          </div>

          {/* Login button */}
          <Button 
            onClick={handleLogin}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3"
            size="lg"
          >
            Sign in with Auth0
          </Button>

          {/* Features list */}
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Track expenses with biblical wisdom</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Manage tithing and charitable giving</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Build emergency funds with purpose</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Family financial coordination</span>
            </div>
          </div>

          {/* Persona information */}
          <div className="text-center text-xs text-gray-500">
            <p>Designed for ages 8-65+ with personalized experiences for:</p>
            <p className="mt-1">Pre-teens • Teens • College Students • Adults • Families • Seniors</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};