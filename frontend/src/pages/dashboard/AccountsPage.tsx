import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const AccountsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Accounts</h1>
        <p className="text-muted-foreground">
          Manage your connected financial accounts and Plaid integrations.
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Accounts Management</CardTitle>
          <CardDescription>
            Connect and manage your bank accounts, credit cards, and investment accounts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            This page will show connected accounts, balances, and provide options to
            add new accounts via Plaid integration.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};