/**
 * Settings/Profile Page - Complete User Account Management
 * Biblical stewardship-focused settings with persona management
 */

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  User, 
  Settings, 
  Bell, 
  Shield, 
  CreditCard, 
  Heart,
  Users,
  BookOpen,
  Palette,
  Globe,
  DollarSign,
  Church,
  Target,
  Info,
  CheckCircle,
  AlertTriangle,
  Edit,
  Save,
  X
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { usePersona } from '@/contexts/PersonaContext';
import { useBudget } from '@/contexts/BudgetContext';
import { useTithing } from '@/contexts/TithingContext';
import { ThemeToggle } from '@/components/ui/theme-toggle';

export const SettingsPage: React.FC = () => {
  const { user, logout, updateUserProfile } = useAuth();
  const { currentPersona, setPersona, getPersonaColors } = usePersona();
  const { settings: budgetSettings } = useBudget();
  const { settings: tithingSettings } = useTithing();

  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    sms: false,
    budgetAlerts: true,
    tithingReminders: true,
    goalProgress: true,
    biblicalReminders: true,
  });

  const handleSaveProfile = async () => {
    try {
      await updateUserProfile(editedProfile);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const personaOptions = [
    { id: 'pre_teen', name: 'Pre-Teen (8-12)', description: 'Learning money basics' },
    { id: 'teen', name: 'Teen (13-17)', description: 'Building financial habits' },
    { id: 'college_student', name: 'College Student', description: 'Managing student finances' },
    { id: 'single_adult', name: 'Single Adult', description: 'Independent financial management' },
    { id: 'married_couple', name: 'Married Couple', description: 'Joint financial planning' },
    { id: 'single_parent', name: 'Single Parent', description: 'Family financial coordination' },
    { id: 'two_parent_family', name: 'Two-Parent Family', description: 'Comprehensive family finances' },
    { id: 'fixed_income', name: 'Fixed Income/Senior', description: 'Retirement financial management' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings & Profile</h1>
          <p className="text-muted-foreground">
            "She is clothed with strength and dignity" - Proverbs 31:25
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsEditing(!isEditing)}>
            {isEditing ? <X className="mr-2 h-4 w-4" /> : <Edit className="mr-2 h-4 w-4" />}
            {isEditing ? 'Cancel' : 'Edit Profile'}
          </Button>
          {isEditing && (
            <Button onClick={handleSaveProfile}>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="profile">
            <User className="mr-2 h-4 w-4" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="persona">
            <Users className="mr-2 h-4 w-4" />
            Persona
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="mr-2 h-4 w-4" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="stewardship">
            <Heart className="mr-2 h-4 w-4" />
            Stewardship
          </TabsTrigger>
          <TabsTrigger value="subscription">
            <CreditCard className="mr-2 h-4 w-4" />
            Subscription
          </TabsTrigger>
          <TabsTrigger value="privacy">
            <Shield className="mr-2 h-4 w-4" />
            Privacy
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>
                  Update your personal details and account information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={isEditing ? editedProfile.name : user?.name || ''}
                    onChange={(e) => setEditedProfile({ ...editedProfile, name: e.target.value })}
                    disabled={!isEditing}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={isEditing ? editedProfile.email : user?.email || ''}
                    onChange={(e) => setEditedProfile({ ...editedProfile, email: e.target.value })}
                    disabled={!isEditing}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Member Since</Label>
                  <p className="text-sm text-muted-foreground">
                    {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Recently joined'}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Account Status</CardTitle>
                <CardDescription>
                  Your faithful stewardship journey overview
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Account Status</span>
                  <Badge variant="default">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Active
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Current Persona</span>
                  <Badge variant="secondary">
                    {personaOptions.find(p => p.id === currentPersona)?.name || 'Single Adult'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Subscription Plan</span>
                  <Badge variant="outline">
                    {user?.subscription?.plan || 'Free'}
                  </Badge>
                </div>
                <div className="pt-4">
                  <Button variant="destructive" size="sm" onClick={logout} className="w-full">
                    Sign Out
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Your profile information is used to personalize your biblical stewardship experience. 
              All data is securely stored and never shared without your permission.
            </AlertDescription>
          </Alert>
        </TabsContent>

        {/* Persona Tab */}
        <TabsContent value="persona" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Choose Your Stewardship Journey</CardTitle>
              <CardDescription>
                Select the persona that best matches your life stage for tailored biblical financial guidance
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                {personaOptions.map((persona) => (
                  <div
                    key={persona.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      currentPersona === persona.id 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:border-primary/50'
                    }`}
                    onClick={() => setPersona(persona.id as any)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium">{persona.name}</h3>
                      {currentPersona === persona.id && (
                        <CheckCircle className="h-4 w-4 text-primary" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{persona.description}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Alert>
            <BookOpen className="h-4 w-4" />
            <AlertDescription>
              Each persona provides age-appropriate biblical financial wisdom, from teaching children 
              the joy of giving to helping seniors manage fixed incomes with faith.
            </AlertDescription>
          </Alert>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Choose how you'd like to receive updates about your financial stewardship
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">Delivery Methods</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Email Notifications</Label>
                      <p className="text-sm text-muted-foreground">Receive updates via email</p>
                    </div>
                    <Button
                      variant={notifications.email ? "default" : "outline"}
                      size="sm"
                      onClick={() => setNotifications({...notifications, email: !notifications.email})}
                    >
                      {notifications.email ? 'Enabled' : 'Disabled'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Push Notifications</Label>
                      <p className="text-sm text-muted-foreground">Browser and mobile alerts</p>
                    </div>
                    <Button
                      variant={notifications.push ? "default" : "outline"}
                      size="sm"
                      onClick={() => setNotifications({...notifications, push: !notifications.push})}
                    >
                      {notifications.push ? 'Enabled' : 'Disabled'}
                    </Button>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Stewardship Reminders</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <DollarSign className="h-4 w-4 text-green-600" />
                      <div>
                        <Label>Budget Alerts</Label>
                        <p className="text-sm text-muted-foreground">Spending limit warnings</p>
                      </div>
                    </div>
                    <Button
                      variant={notifications.budgetAlerts ? "default" : "outline"}
                      size="sm"
                      onClick={() => setNotifications({...notifications, budgetAlerts: !notifications.budgetAlerts})}
                    >
                      {notifications.budgetAlerts ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Church className="h-4 w-4 text-purple-600" />
                      <div>
                        <Label>Tithing Reminders</Label>
                        <p className="text-sm text-muted-foreground">Monthly giving prompts</p>
                      </div>
                    </div>
                    <Button
                      variant={notifications.tithingReminders ? "default" : "outline"}
                      size="sm"
                      onClick={() => setNotifications({...notifications, tithingReminders: !notifications.tithingReminders})}
                    >
                      {notifications.tithingReminders ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Target className="h-4 w-4 text-blue-600" />
                      <div>
                        <Label>Goal Progress</Label>
                        <p className="text-sm text-muted-foreground">Milestone celebrations</p>
                      </div>
                    </div>
                    <Button
                      variant={notifications.goalProgress ? "default" : "outline"}
                      size="sm"
                      onClick={() => setNotifications({...notifications, goalProgress: !notifications.goalProgress})}
                    >
                      {notifications.goalProgress ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <BookOpen className="h-4 w-4 text-amber-600" />
                      <div>
                        <Label>Biblical Wisdom</Label>
                        <p className="text-sm text-muted-foreground">Daily stewardship verses</p>
                      </div>
                    </div>
                    <Button
                      variant={notifications.biblicalReminders ? "default" : "outline"}
                      size="sm"
                      onClick={() => setNotifications({...notifications, biblicalReminders: !notifications.biblicalReminders})}
                    >
                      {notifications.biblicalReminders ? 'On' : 'Off'}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Stewardship Tab */}
        <TabsContent value="stewardship" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Tithing Preferences</CardTitle>
                <CardDescription>
                  Configure your giving and stewardship settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Default Tithing %</span>
                  <Badge variant="outline">{tithingSettings?.tithingPercentage || 10}%</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Calculation Base</span>
                  <Badge variant="secondary">{tithingSettings?.calculationBase || 'Gross'} Income</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Giving Goals</span>
                  <Badge variant="outline">3 Active</Badge>
                </div>
                <div className="pt-2">
                  <Button variant="outline" size="sm" className="w-full">
                    <Settings className="mr-2 h-4 w-4" />
                    Configure Giving Settings
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Budget Preferences</CardTitle>
                <CardDescription>
                  Your financial planning configurations
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Default Currency</span>
                  <Badge variant="outline">USD ($)</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Budget Period</span>
                  <Badge variant="secondary">Monthly</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Alert Threshold</span>
                  <Badge variant="outline">80%</Badge>
                </div>
                <div className="pt-2">
                  <Button variant="outline" size="sm" className="w-full">
                    <DollarSign className="mr-2 h-4 w-4" />
                    Budget Settings
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Biblical Stewardship Insights</CardTitle>
              <CardDescription>
                Your journey in faithful money management
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">12</div>
                  <div className="text-sm text-muted-foreground">Months of Faithful Tithing</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">85%</div>
                  <div className="text-sm text-muted-foreground">Budget Accuracy Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">3</div>
                  <div className="text-sm text-muted-foreground">Financial Goals Achieved</div>
                </div>
              </div>
              <div className="pt-4 text-center">
                <p className="text-sm text-muted-foreground italic">
                  "Commit to the Lord whatever you do, and he will establish your plans." - Proverbs 16:3
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Subscription Tab */}
        <TabsContent value="subscription" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Subscription Plan</CardTitle>
              <CardDescription>
                Manage your Faithful Finances subscription and billing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 border rounded-lg">
                <div>
                  <h3 className="font-medium">Free Plan</h3>
                  <p className="text-sm text-muted-foreground">Perfect for getting started with biblical stewardship</p>
                </div>
                <Badge variant="default">Current Plan</Badge>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-medium">Plan Features</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>✓ Basic budget tracking</li>
                  <li>✓ Tithing calculator</li>
                  <li>✓ Biblical financial wisdom</li>
                  <li>✓ Single persona access</li>
                  <li>✗ Family collaboration</li>
                  <li>✗ Advanced reporting</li>
                  <li>✗ Priority support</li>
                </ul>
              </div>

              <div className="pt-4">
                <Button className="w-full">
                  <CreditCard className="mr-2 h-4 w-4" />
                  Upgrade to Premium
                </Button>
              </div>
            </CardContent>
          </Card>

          <Alert>
            <Heart className="h-4 w-4" />
            <AlertDescription>
              Premium plans support our mission to provide biblical financial education to families worldwide. 
              Your upgrade helps us serve more people in their stewardship journey.
            </AlertDescription>
          </Alert>
        </TabsContent>

        {/* Privacy Tab */}
        <TabsContent value="privacy" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Privacy & Security</CardTitle>
              <CardDescription>
                Manage your data privacy and account security settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <h4 className="font-medium">Data & Privacy</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Share Usage Analytics</Label>
                      <p className="text-sm text-muted-foreground">Help improve the app with anonymous usage data</p>
                    </div>
                    <Button variant="outline" size="sm">Enabled</Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Marketing Communications</Label>
                      <p className="text-sm text-muted-foreground">Receive biblical stewardship tips and updates</p>
                    </div>
                    <Button variant="outline" size="sm">Disabled</Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Data Export</Label>
                      <p className="text-sm text-muted-foreground">Download all your financial data</p>
                    </div>
                    <Button variant="outline" size="sm">Download</Button>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium">Account Security</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Two-Factor Authentication</Label>
                      <p className="text-sm text-muted-foreground">Add an extra layer of security</p>
                    </div>
                    <Button variant="outline" size="sm">
                      <Shield className="mr-2 h-3 w-3" />
                      Enable
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Connected Apps</Label>
                      <p className="text-sm text-muted-foreground">Manage third-party integrations</p>
                    </div>
                    <Button variant="outline" size="sm">Manage</Button>
                  </div>
                </div>
              </div>

              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Delete Account:</strong> This action cannot be undone. All your financial data, 
                  goals, and stewardship history will be permanently removed.
                </AlertDescription>
              </Alert>

              <Button variant="destructive" size="sm">
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};