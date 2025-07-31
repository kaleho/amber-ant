import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const GoalsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Savings Goals</h1>
        <p className="text-muted-foreground">
          Set and track financial goals, especially emergency funds and major purchases.
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Goal Tracking</CardTitle>
          <CardDescription>
            Monitor progress toward emergency funds and other savings goals.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            This page will show goal progress, milestone celebrations,
            and persona-specific goal recommendations.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};