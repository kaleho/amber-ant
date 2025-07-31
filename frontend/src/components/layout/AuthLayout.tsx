import React from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export const AuthLayout: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left side - Branding */}
      <div className="hidden lg:flex flex-col justify-center items-center bg-gradient-to-br from-primary to-primary/80 text-primary-foreground p-8">
        <div className="max-w-md text-center space-y-6">
          <h1 className="text-4xl font-bold">Faithful Finances</h1>
          <p className="text-xl opacity-90">
            Biblical stewardship made simple
          </p>
          <blockquote className="text-lg italic opacity-80">
            "For where your treasure is, there your heart will be also."
            <cite className="block text-sm mt-2 opacity-70">- Matthew 6:21</cite>
          </blockquote>
        </div>
      </div>

      {/* Right side - Auth forms */}
      <div className="flex flex-col justify-center items-center p-8">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center lg:hidden">
            <h1 className="text-2xl font-bold">Faithful Finances</h1>
            <p className="text-muted-foreground">Biblical stewardship made simple</p>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  );
};