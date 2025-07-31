import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const TransactionsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Transactions</h1>
        <p className="text-muted-foreground">
          View and categorize your financial transactions with dual categorization system.
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Transaction Management</CardTitle>
          <CardDescription>
            Track spending with biblical stewardship categorization (needs vs wants).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            This page will display transaction history, filtering options, 
            and dual categorization features for needs vs wants classification.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};