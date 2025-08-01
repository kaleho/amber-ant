import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Heart, 
  Plus, 
  Calculator, 
  Church, 
  TrendingUp, 
  Calendar,
  DollarSign,
  Target,
  Flame,
  Award,
  BookOpen
} from 'lucide-react';
import { useTithing } from '@/contexts/TithingContext';

export const TithingPage: React.FC = () => {
  const {
    tithingRecords,
    churches,
    activeChurch,
    givingGoals,
    settings,
    calculateTithe,
    calculateMonthlyTithe,
    getTotalTithedThisMonth,
    getTotalTithedYTD,
    getTithingStreak,
  } = useTithing();

  const [incomeInput, setIncomeInput] = useState('');
  const [calculatedTithe, setCalculatedTithe] = useState(0);

  const handleCalculate = () => {
    const income = parseFloat(incomeInput);
    if (!isNaN(income) && income > 0) {
      const tithe = calculateTithe(income);
      setCalculatedTithe(tithe);
    }
  };

  const monthlyTithe = calculateMonthlyTithe();
  const totalThisMonth = getTotalTithedThisMonth();
  const totalYTD = getTotalTithedYTD();
  const givingStreak = getTithingStreak();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const recentTithes = tithingRecords
    .slice()
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5);

  const biblicalVerses = [
    {
      verse: "Bring the whole tithe into the storehouse, that there may be food in my house.",
      reference: "Malachi 3:10"
    },
    {
      verse: "Honor the Lord with your wealth, with the firstfruits of all your crops.",
      reference: "Proverbs 3:9"
    },
    {
      verse: "Each of you should give what you have decided in your heart to give, not reluctantly or under compulsion, for God loves a cheerful giver.",
      reference: "2 Corinthians 9:7"
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tithing & Giving</h1>
          <p className="text-muted-foreground">
            "Give, and it will be given to you" - Luke 6:38
          </p>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Record Tithe
          </Button>
          <Button variant="outline">
            <Church className="mr-2 h-4 w-4" />
            Manage Churches
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <Heart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{formatCurrency(totalThisMonth)}</div>
            <p className="text-xs text-muted-foreground">
              Target: {formatCurrency(monthlyTithe)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Year to Date</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{formatCurrency(totalYTD)}</div>
            <p className="text-xs text-muted-foreground">
              {tithingRecords.filter(r => r.date.startsWith(new Date().getFullYear().toString())).length} contributions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Giving Streak</CardTitle>
            <Flame className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{givingStreak}</div>
            <p className="text-xs text-muted-foreground">
              {givingStreak === 1 ? 'month' : 'months'} consecutive
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Church</CardTitle>
            <Church className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold">{activeChurch?.name || 'Not Set'}</div>
            <p className="text-xs text-muted-foreground">
              {churches.length} churches configured
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Monthly Tithing Progress</CardTitle>
          <CardDescription>
            Track your progress toward your monthly giving goal
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Progress</span>
              <span className="text-sm text-muted-foreground">
                {formatCurrency(totalThisMonth)} / {formatCurrency(monthlyTithe)}
              </span>
            </div>
            <Progress 
              value={Math.min((totalThisMonth / monthlyTithe) * 100, 100)} 
              className="h-3"
            />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{((totalThisMonth / monthlyTithe) * 100).toFixed(1)}% complete</span>
              <span>{formatCurrency(Math.max(monthlyTithe - totalThisMonth, 0))} remaining</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Tithe Calculator */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Tithe Calculator
            </CardTitle>
            <CardDescription>
              Calculate your tithe based on {settings.tithingPercentage}% of {settings.calculationBase} income
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="income">Income Amount</Label>
              <Input
                id="income"
                type="number"
                placeholder="Enter income amount"
                value={incomeInput}
                onChange={(e) => setIncomeInput(e.target.value)}
              />
            </div>
            <Button onClick={handleCalculate} className="w-full">
              Calculate Tithe
            </Button>
            {calculatedTithe > 0 && (
              <div className="p-4 bg-purple-50 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {formatCurrency(calculatedTithe)}
                </div>
                <p className="text-sm text-purple-700">
                  {settings.tithingPercentage}% of {formatCurrency(parseFloat(incomeInput))}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Giving Goals */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Giving Goals
            </CardTitle>
            <CardDescription>
              Track your special giving commitments
            </CardDescription>
          </CardHeader>
          <CardContent>
            {givingGoals.length > 0 ? (
              <div className="space-y-4">
                {givingGoals.slice(0, 3).map((goal) => (
                  <div key={goal.id} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">{goal.title}</span>
                      <Badge variant="outline">{goal.category}</Badge>
                    </div>
                    <Progress 
                      value={(goal.currentAmount / goal.targetAmount) * 100} 
                      className="h-2"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{formatCurrency(goal.currentAmount)} raised</span>
                      <span>{formatCurrency(goal.targetAmount)} goal</span>
                    </div>
                  </div>
                ))}
                <Button variant="outline" size="sm" className="w-full">
                  View All Goals
                </Button>
              </div>
            ) : (
              <div className="text-center py-6">
                <Target className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No giving goals set</p>
                <Button variant="outline" size="sm" className="mt-2">
                  Create First Goal
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Contributions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Contributions</CardTitle>
            <CardDescription>
              Your latest tithing and giving records
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentTithes.length > 0 ? (
              <div className="space-y-4">
                {recentTithes.map((tithe) => (
                  <div key={tithe.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">
                        {churches.find(c => c.id === tithe.churchId)?.name || 'General Tithe'}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(tithe.date).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="text-sm font-bold text-purple-600">
                        {formatCurrency(tithe.amount)}
                      </span>
                      <Badge 
                        variant={tithe.status === 'completed' ? 'default' : 'secondary'}
                        className="text-xs"
                      >
                        {tithe.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <Heart className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No tithing records yet</p>
                <Button variant="outline" size="sm" className="mt-2">
                  Record First Tithe
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Biblical Encouragement */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Biblical Encouragement
            </CardTitle>
            <CardDescription>
              Scripture about giving and stewardship
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {biblicalVerses.map((verse, index) => (
                <div key={index} className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm italic text-blue-900">
                    "{verse.verse}"
                  </p>
                  <p className="text-xs text-blue-700 mt-2 font-medium">
                    - {verse.reference}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Achievements */}
      {givingStreak >= 3 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <Award className="h-5 w-5" />
              Faithful Giver Achievement
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-yellow-700">
              Congratulations! You've maintained a {givingStreak}-month giving streak. 
              Your faithfulness in tithing is a testament to your heart for God's kingdom.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};