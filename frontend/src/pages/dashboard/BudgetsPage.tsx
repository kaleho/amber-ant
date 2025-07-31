import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const BudgetsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Budgets</h1>
        <p className="text-muted-foreground">
          Create and manage budgets with persona-specific categories and biblical priorities.
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Budget Planning</CardTitle>
          <CardDescription>
            Build budgets that prioritize tithing, needs, and responsible spending.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            This page will include budget creation tools, category management,
            and progress tracking with biblical stewardship principles.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};