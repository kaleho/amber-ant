/**
 * Goals Page - Complete Biblical Stewardship Financial Goals Management
 * Comprehensive goal setting, tracking, and biblical financial planning
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Target, 
  PlusCircle, 
  TrendingUp, 
  DollarSign, 
  Calendar, 
  CheckCircle, 
  AlertTriangle,
  Home,
  Car,
  GraduationCap,
  Heart,
  Plane,
  Shield,
  BookOpen,
  Church,
  Users,
  Clock,
  Trophy,
  Edit,
  Trash2,
  Star
} from 'lucide-react';
import { usePersona } from '@/contexts/PersonaContext';
import { useBudget } from '@/contexts/BudgetContext';
import { ThemeToggle } from '@/components/ui/theme-toggle';

interface Goal {
  id: string;
  title: string;
  description: string;
  targetAmount: number;
  currentAmount: number;
  category: 'emergency' | 'home' | 'education' | 'vehicle' | 'vacation' | 'retirement' | 'giving' | 'other';
  priority: 'low' | 'medium' | 'high' | 'critical';
  targetDate: string;
  isCompleted: boolean;
  biblicalVerse?: string;
  createdAt: string;
}

export const GoalsPage: React.FC = () => {
  const { currentPersona } = usePersona();
  const { budgets } = useBudget();

  // Sample goals data - in real app this would come from context/API
  const [goals, setGoals] = useState<Goal[]>([
    {
      id: '1',
      title: 'Emergency Fund - 6 Months',
      description: 'Build a complete emergency fund covering 6 months of expenses for financial security.',
      targetAmount: 18000,
      currentAmount: 7500,
      category: 'emergency',
      priority: 'critical',
      targetDate: '2025-12-31',
      isCompleted: false,
      biblicalVerse: 'The wise store up choice food and olive oil, but fools gulp theirs down. - Proverbs 21:20',
      createdAt: '2024-01-15'
    },
    {
      id: '2',
      title: 'House Down Payment',
      description: 'Save for a 20% down payment on a faithful stewardship home.',
      targetAmount: 60000,
      currentAmount: 22000,
      category: 'home',
      priority: 'high',
      targetDate: '2026-06-30',
      isCompleted: false,
      biblicalVerse: 'By wisdom a house is built, and through understanding it is established. - Proverbs 24:3',
      createdAt: '2024-02-01'
    },
    {
      id: '3',
      title: 'Tithing Goal Fund',
      description: 'Special fund for additional giving opportunities and ministry support.',
      targetAmount: 5000,
      currentAmount: 5000,
      category: 'giving',
      priority: 'high',
      targetDate: '2024-12-31',
      isCompleted: true,
      biblicalVerse: 'Each of you should give what you have decided in your heart to give. - 2 Corinthians 9:7',
      createdAt: '2024-01-01'
    },
    {
      id: '4',
      title: 'Education Fund',
      description: 'Continuing education and biblical financial training resources.',
      targetAmount: 3000,
      currentAmount: 1200,
      category: 'education',
      priority: 'medium',
      targetDate: '2025-08-31',
      isCompleted: false,
      biblicalVerse: 'Plans fail for lack of counsel, but with many advisers they succeed. - Proverbs 15:22',
      createdAt: '2024-03-15'
    }
  ]);

  const [isAddingGoal, setIsAddingGoal] = useState(false);
  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    targetAmount: '',
    category: 'other' as Goal['category'],
    priority: 'medium' as Goal['priority'],
    targetDate: ''
  });

  const calculateProgress = (current: number, target: number) => {
    return Math.min((current / target) * 100, 100);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getGoalIcon = (category: Goal['category']) => {
    switch (category) {
      case 'emergency': return <Shield className="h-5 w-5 text-red-600" />;
      case 'home': return <Home className="h-5 w-5 text-blue-600" />;
      case 'education': return <GraduationCap className="h-5 w-5 text-purple-600" />;
      case 'vehicle': return <Car className="h-5 w-5 text-gray-600" />;
      case 'vacation': return <Plane className="h-5 w-5 text-green-600" />;
      case 'giving': return <Church className="h-5 w-5 text-amber-600" />;
      default: return <Target className="h-5 w-5 text-indigo-600" />;
    }
  };

  const getPriorityColor = (priority: Goal['priority']) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  const activeGoals = goals.filter(goal => !goal.isCompleted);
  const completedGoals = goals.filter(goal => goal.isCompleted);
  const totalTargetAmount = activeGoals.reduce((sum, goal) => sum + goal.targetAmount, 0);
  const totalCurrentAmount = activeGoals.reduce((sum, goal) => sum + goal.currentAmount, 0);
  const overallProgress = totalTargetAmount > 0 ? (totalCurrentAmount / totalTargetAmount) * 100 : 0;

  const handleAddGoal = () => {
    if (!newGoal.title || !newGoal.targetAmount || !newGoal.targetDate) return;

    const goal: Goal = {
      id: Date.now().toString(),
      title: newGoal.title,
      description: newGoal.description,
      targetAmount: parseFloat(newGoal.targetAmount),
      currentAmount: 0,
      category: newGoal.category,
      priority: newGoal.priority,
      targetDate: newGoal.targetDate,
      isCompleted: false,
      createdAt: new Date().toISOString()
    };

    setGoals([...goals, goal]);
    setNewGoal({
      title: '',
      description: '',
      targetAmount: '',
      category: 'other',
      priority: 'medium',
      targetDate: ''
    });
    setIsAddingGoal(false);
  };

  const updateGoalProgress = (goalId: string, amount: number) => {
    setGoals(goals.map(goal => 
      goal.id === goalId 
        ? { ...goal, currentAmount: Math.max(0, amount) }
        : goal
    ));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Financial Goals</h1>
          <p className="text-muted-foreground">
            "Commit to the Lord whatever you do, and he will establish your plans." - Proverbs 16:3
          </p>
        </div>
        <div className="flex gap-2">
          <ThemeToggle />
          <Button 
            onClick={() => setIsAddingGoal(true)}
            className="flex items-center gap-2"
          >
            <PlusCircle className="h-4 w-4" />
            Add New Goal
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Active Goals</p>
                <p className="text-2xl font-bold">{activeGoals.length}</p>
              </div>
              <Target className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Target</p>
                <p className="text-2xl font-bold">{formatCurrency(totalTargetAmount)}</p>
              </div>
              <DollarSign className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Saved</p>
                <p className="text-2xl font-bold">{formatCurrency(totalCurrentAmount)}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Overall Progress</p>
                <p className="text-2xl font-bold">{overallProgress.toFixed(1)}%</p>
              </div>
              <Trophy className="h-8 w-8 text-amber-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Overall Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Goals Progress</CardTitle>
          <CardDescription>Your faithful stewardship journey toward financial goals</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress: {formatCurrency(totalCurrentAmount)} of {formatCurrency(totalTargetAmount)}</span>
              <span>{overallProgress.toFixed(1)}%</span>
            </div>
            <Progress value={overallProgress} className="h-3" />
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="active" className="space-y-6">
        <TabsList>
          <TabsTrigger value="active">
            <Target className="mr-2 h-4 w-4" />
            Active Goals ({activeGoals.length})
          </TabsTrigger>
          <TabsTrigger value="completed">
            <CheckCircle className="mr-2 h-4 w-4" />
            Completed ({completedGoals.length})
          </TabsTrigger>
          <TabsTrigger value="insights">
            <BookOpen className="mr-2 h-4 w-4" />
            Biblical Insights
          </TabsTrigger>
        </TabsList>

        {/* Active Goals Tab */}
        <TabsContent value="active" className="space-y-4">
          {activeGoals.map((goal) => (
            <Card key={goal.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getGoalIcon(goal.category)}
                    <div>
                      <CardTitle className="text-lg">{goal.title}</CardTitle>
                      <CardDescription>{goal.description}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getPriorityColor(goal.priority)}>
                      {goal.priority.charAt(0).toUpperCase() + goal.priority.slice(1)}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <Label className="text-sm font-medium">Target Amount</Label>
                    <p className="text-xl font-bold text-green-600">{formatCurrency(goal.targetAmount)}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Current Amount</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={goal.currentAmount}
                        onChange={(e) => updateGoalProgress(goal.id, parseFloat(e.target.value) || 0)}
                        className="w-24"
                      />
                      <span className="text-sm text-muted-foreground">
                        ({formatCurrency(goal.currentAmount)})
                      </span>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Target Date</Label>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <span>{new Date(goal.targetDate).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>{calculateProgress(goal.currentAmount, goal.targetAmount).toFixed(1)}%</span>
                  </div>
                  <Progress value={calculateProgress(goal.currentAmount, goal.targetAmount)} className="h-2" />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{formatCurrency(goal.currentAmount)} saved</span>
                    <span>{formatCurrency(goal.targetAmount - goal.currentAmount)} remaining</span>
                  </div>
                </div>

                {goal.biblicalVerse && (
                  <Alert>
                    <BookOpen className="h-4 w-4" />
                    <AlertDescription className="italic">
                      "{goal.biblicalVerse}"
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          ))}

          {activeGoals.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No Active Goals</h3>
                <p className="text-muted-foreground mb-4">
                  Start your faithful stewardship journey by setting your first financial goal.
                </p>
                <Button onClick={() => setIsAddingGoal(true)}>
                  <PlusCircle className="mr-2 h-4 w-4" />
                  Create Your First Goal
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Completed Goals Tab */}
        <TabsContent value="completed" className="space-y-4">
          {completedGoals.map((goal) => (
            <Card key={goal.id} className="bg-green-50 border-green-200">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <CardTitle className="text-lg text-green-800">{goal.title}</CardTitle>
                      <CardDescription>{goal.description}</CardDescription>
                    </div>
                  </div>
                  <Badge className="bg-green-100 text-green-800 border-green-200">
                    Completed
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">
                    Achieved: {formatCurrency(goal.targetAmount)}
                  </span>
                  <span className="text-sm text-green-600 font-medium">
                    🎉 Goal Completed!
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}

          {completedGoals.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <Trophy className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium mb-2">No Completed Goals Yet</h3>
                <p className="text-muted-foreground">
                  Keep working toward your active goals to see your achievements here.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Biblical Insights Tab */}
        <TabsContent value="insights" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Biblical Wisdom on Goals</CardTitle>
                <CardDescription>Scripture-based guidance for financial planning</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 border-l-4 border-blue-500 bg-blue-50">
                  <p className="text-sm italic mb-2">
                    "Plans fail for lack of counsel, but with many advisers they succeed."
                  </p>
                  <p className="text-xs text-muted-foreground">Proverbs 15:22</p>
                </div>
                <div className="p-4 border-l-4 border-green-500 bg-green-50">
                  <p className="text-sm italic mb-2">
                    "The plans of the diligent lead to profit as surely as haste leads to poverty."
                  </p>
                  <p className="text-xs text-muted-foreground">Proverbs 21:5</p>
                </div>
                <div className="p-4 border-l-4 border-purple-500 bg-purple-50">
                  <p className="text-sm italic mb-2">
                    "Commit to the Lord whatever you do, and he will establish your plans."
                  </p>
                  <p className="text-xs text-muted-foreground">Proverbs 16:3</p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Stewardship Goal Categories</CardTitle>
                <CardDescription>Biblical priorities for financial planning</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-red-50">
                  <Shield className="h-5 w-5 text-red-600" />
                  <div>
                    <h4 className="font-medium">Emergency Fund</h4>
                    <p className="text-sm text-muted-foreground">Prepare for unexpected needs</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-amber-50">
                  <Church className="h-5 w-5 text-amber-600" />
                  <div>
                    <h4 className="font-medium">Generous Giving</h4>
                    <p className="text-sm text-muted-foreground">Special funds for ministry and charity</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-50">
                  <Home className="h-5 w-5 text-blue-600" />
                  <div>
                    <h4 className="font-medium">Home & Family</h4>
                    <p className="text-sm text-muted-foreground">Shelter and family provisions</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 rounded-lg bg-purple-50">
                  <GraduationCap className="h-5 w-5 text-purple-600" />
                  <div>
                    <h4 className="font-medium">Education & Growth</h4>
                    <p className="text-sm text-muted-foreground">Wisdom and skill development</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Monthly Stewardship Challenge</CardTitle>
              <CardDescription>Biblical challenges to grow in faithful money management</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center p-4 border rounded-lg">
                  <Star className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
                  <h4 className="font-medium">Prayer Before Planning</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Commit each financial goal to prayer before setting targets
                  </p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <Users className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                  <h4 className="font-medium">Accountability Partner</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Share your goals with a trusted friend or mentor
                  </p>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <Heart className="h-8 w-8 text-red-600 mx-auto mb-2" />
                  <h4 className="font-medium">Generosity First</h4>
                  <p className="text-sm text-muted-foreground mt-1">
                    Include giving goals alongside personal financial targets
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Goal Modal/Form */}
      {isAddingGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Add New Goal</CardTitle>
              <CardDescription>Create a new financial goal for your stewardship journey</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Goal Title</Label>
                <Input
                  id="title"
                  value={newGoal.title}
                  onChange={(e) => setNewGoal({...newGoal, title: e.target.value})}
                  placeholder="e.g., Emergency Fund"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={newGoal.description}
                  onChange={(e) => setNewGoal({...newGoal, description: e.target.value})}
                  placeholder="Brief description of your goal"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="amount">Target Amount</Label>
                  <Input
                    id="amount"
                    type="number"
                    value={newGoal.targetAmount}
                    onChange={(e) => setNewGoal({...newGoal, targetAmount: e.target.value})}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="date">Target Date</Label>
                  <Input
                    id="date"
                    type="date"
                    value={newGoal.targetDate}
                    onChange={(e) => setNewGoal({...newGoal, targetDate: e.target.value})}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <select
                    id="category"
                    value={newGoal.category}
                    onChange={(e) => setNewGoal({...newGoal, category: e.target.value as Goal['category']})}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="emergency">Emergency Fund</option>
                    <option value="home">Home & Family</option>
                    <option value="education">Education</option>
                    <option value="vehicle">Vehicle</option>
                    <option value="vacation">Vacation</option>
                    <option value="giving">Giving</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="priority">Priority</Label>
                  <select
                    id="priority"
                    value={newGoal.priority}
                    onChange={(e) => setNewGoal({...newGoal, priority: e.target.value as Goal['priority']})}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
            </CardContent>
            <div className="flex justify-end gap-2 p-6 pt-0">
              <Button variant="outline" onClick={() => setIsAddingGoal(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddGoal}>
                Create Goal
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};