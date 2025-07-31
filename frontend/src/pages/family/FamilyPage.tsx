import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export const FamilyPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Family Management</h1>
        <p className="text-muted-foreground">
          Coordinate finances with family members and manage permissions.
        </p>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Family Coordination</CardTitle>
          <CardDescription>
            Manage family plans, invite members, and coordinate shared finances.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            This page will show family member management, permissions,
            shared goals, and coordinated budgeting features.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};