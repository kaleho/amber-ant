import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const TithingPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Tithing</h1>
        <p className="text-muted-foreground">
          Calculate and track your tithing with biblical principles and guidance.
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Faithful Giving</CardTitle>
          <CardDescription>
            Manage your tithe with automatic calculations and tracking.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            This page will calculate 10% tithing on gross income,
            track giving history, and provide biblical encouragement.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};