/**
 * Pre-teen Dashboard - Gamified learning experience for young money managers
 * Features: Achievement system, visual progress tracking, age-appropriate financial education
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Star, 
  Target, 
  Heart, 
  DollarSign,
  Gift,
  Gamepad2,
  Trophy,
  BookOpen,
  Coins,
  Sparkles,
  Award,
  Home,
  Users,
  Calculator
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';
import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { TransactionCard } from '@/components/financial/TransactionCard';
import { EmergencyFundCard } from '@/components/financial/EmergencyFundCard';

export const PreTeenDashboard: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  // Mock data queries - replace with real API calls
  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: () => apiClient.getProfile(),
  });

  const { data: transactions } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => apiClient.getTransactions({ limit: 5 }),
  });

  const { data: goals } = useQuery({
    queryKey: ['savings-goals'],
    queryFn: () => apiClient.getSavingsGoals(),
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => apiClient.getAccounts(),
  });

  // Pre-teen specific dashboard stats
  const dashboardStats = {
    totalBalance: accounts?.reduce((sum, acc) => sum + acc.balance, 0) || 127.50,
    monthlyIncome: 60, // Allowance
    monthlyExpenses: 35,
    emergencyFundProgress: 64, // Good progress for pre-teen
    budgetProgress: 58,
    tithingPercentage: 10,
    savingsRate: 42
  };

  // Achievement system
  const achievements = [
    { name: "First Saver", emoji: "🏆", earned: true, description: "Saved your first dollar!" },
    { name: "Faithful Giver", emoji: "❤️", earned: true, description: "Gave your first tithe" },
    { name: "Goal Setter", emoji: "🎯", earned: true, description: "Set your first savings goal" },
    { name: "Weekly Winner", emoji: "⭐", earned: true, description: "Completed all chores this week" },
    { name: "Chore Champion", emoji: "💪", earned: true, description: "Did extra chores to earn more" },
    { name: "Smart Spender", emoji: "🧠", earned: true, description: "Thought before buying something" },
    { name: "Bible Student", emoji: "🌟", earned: true, description: "Learned a Bible verse about money" },
    { name: "Generous Heart", emoji: "💝", earned: true, description: "Gave extra offering" },
    { name: "Goal Achiever", emoji: "🎊", earned: false, description: "Reach your savings goal" },
    { name: "Money Master", emoji: "👑", earned: false, description: "Learn all money lessons" }
  ];

  // Learning progress
  const learningModules = [
    { title: "What is Money?", completed: true, fun: true, emoji: "💰" },
    { title: "Earning Money", completed: true, fun: true, emoji: "💪" },
    { title: "Saving Money", completed: true, fun: true, emoji: "🏦" },
    { title: "Spending Wisely", completed: false, fun: true, emoji: "🛒" },
    { title: "Giving to God", completed: true, fun: true, emoji: "❤️" },
    { title: "Helping Others", completed: false, fun: true, emoji: "🤝" }
  ];

  // Chore tracker
  const chores = [
    { name: "Make bed", completed: true, reward: 2 },
    { name: "Feed pets", completed: true, reward: 3 },
    { name: "Clean room", completed: false, reward: 5 },
    { name: "Take out trash", completed: true, reward: 4 },
    { name: "Help with dishes", completed: false, reward: 3 }
  ];

  return (
    <div className="container mx-auto p-6 space-y-6 bg-gradient-to-br from-orange-50 to-yellow-50 min-h-screen">
      {/* Fun Header with Big Greeting */}
      <div className="flex items-center justify-between bg-white rounded-xl p-6 border-4 border-orange-300 shadow-lg">
        <div className="flex items-center gap-4">
          <div className="text-6xl animate-bounce">🌟</div>
          <div>
            <h1 className="text-4xl font-bold text-orange-800">
              Great job, {profile?.display_name || 'Champion'}! 
            </h1>
            <p className="text-orange-600 text-lg mt-1">
              You're learning to be a faithful steward! 🙌
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg text-gray-600">My Savings</div>
          <div className="text-4xl font-bold text-orange-800">
            ${dashboardStats.totalBalance.toFixed(2)}
          </div>
          <Badge className="bg-orange-100 text-orange-800 text-lg px-4 py-2 mt-2">
            Super Saver! 
          </Badge>
        </div>
      </div>

      {/* Dashboard Statistics - Simplified for pre-teens */}
      <DashboardStats 
        persona="pre_teen" 
        stats={dashboardStats}
        className="mb-6" 
      />

      {/* Main Dashboard Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5 bg-white border-4 border-orange-200 h-16">
          <TabsTrigger value="overview" className="data-[state=active]:bg-orange-100 text-base">
            <Home className="h-5 w-5 mr-2" />
            Home
          </TabsTrigger>
          <TabsTrigger value="money" className="data-[state=active]:bg-orange-100 text-base">
            <Coins className="h-5 w-5 mr-2" />
            Money
          </TabsTrigger>
          <TabsTrigger value="goals" className="data-[state=active]:bg-orange-100 text-base">
            <Target className="h-5 w-5 mr-2" />
            Goals
          </TabsTrigger>
          <TabsTrigger value="learn" className="data-[state=active]:bg-orange-100 text-base">
            <BookOpen className="h-5 w-5 mr-2" />
            Learn
          </TabsTrigger>
          <TabsTrigger value="family" className="data-[state=active]:bg-orange-100 text-base">
            <Users className="h-5 w-5 mr-2" />
            Family
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Big Colorful Actions */}
            <Card className="border-4 border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="text-2xl text-green-800 flex items-center gap-3">
                  <Gamepad2 className="h-8 w-8" />
                  Fun Activities
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button className="w-full h-16 text-lg bg-green-600 hover:bg-green-700">
                  <Gift className="h-6 w-6 mr-3" />
                  Add My Allowance! 💰
                </Button>
                <Button className="w-full h-16 text-lg bg-red-600 hover:bg-red-700">
                  <Heart className="h-6 w-6 mr-3" />
                  Give My Tithe! ❤️
                </Button>
                <Button className="w-full h-16 text-lg bg-purple-600 hover:bg-purple-700">
                  <Target className="h-6 w-6 mr-3" />
                  Check My Goal! 🎯
                </Button>
              </CardContent>
            </Card>

            {/* Recent Money Moves */}
            <Card className="border-4 border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="text-2xl text-blue-800 flex items-center gap-3">
                  <Sparkles className="h-8 w-8" />
                  My Money Moves
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {transactions?.slice(0, 3).map((transaction) => (
                  <div key={transaction.id} className="p-3 bg-white rounded-lg border-2 border-blue-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">
                          {transaction.amount > 0 ? '💰' : '🛒'}
                        </div>
                        <div>
                          <p className="font-bold text-blue-800">{transaction.description}</p>
                          <p className="text-sm text-blue-600">
                            {new Date(transaction.date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className={`text-xl font-bold ${transaction.amount > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {transaction.amount > 0 ? '+' : ''}${Math.abs(transaction.amount).toFixed(2)}
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Chore Tracker */}
          <Card className="border-4 border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-2xl text-purple-800 flex items-center gap-3">
                <Award className="h-8 w-8" />
                My Chore Chart
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {chores.map((chore, index) => (
                  <div key={index} className={`p-4 rounded-lg border-3 ${chore.completed ? 'bg-green-100 border-green-300' : 'bg-white border-purple-200'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="text-2xl">
                          {chore.completed ? '✅' : '⏰'}
                        </div>
                        <div>
                          <p className="font-bold">{chore.name}</p>
                          <p className="text-sm text-gray-600">${chore.reward}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Money Tab */}
        <TabsContent value="money" className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="border-4 border-green-200 bg-green-50 text-center p-6">
              <div className="text-4xl mb-2">💰</div>
              <div className="text-2xl font-bold text-green-800">${dashboardStats.totalBalance.toFixed(2)}</div>
              <div className="text-green-600">My Savings</div>
            </Card>
            <Card className="border-4 border-blue-200 bg-blue-50 text-center p-6">
              <div className="text-4xl mb-2">💝</div>
              <div className="text-2xl font-bold text-blue-800">${(dashboardStats.totalBalance * 0.1).toFixed(2)}</div>
              <div className="text-blue-600">Tithing</div>
            </Card>
            <Card className="border-4 border-purple-200 bg-purple-50 text-center p-6">
              <div className="text-4xl mb-2">🎁</div>
              <div className="text-2xl font-bold text-purple-800">${dashboardStats.monthlyIncome}</div>
              <div className="text-purple-600">Allowance</div>
            </Card>
            <Card className="border-4 border-orange-200 bg-orange-50 text-center p-6">
              <div className="text-4xl mb-2">🛒</div>
              <div className="text-2xl font-bold text-orange-800">${dashboardStats.monthlyExpenses}</div>
              <div className="text-orange-600">Spending</div>
            </Card>
          </div>

          <Card className="border-4 border-yellow-200 bg-yellow-50">
            <CardHeader>
              <CardTitle className="text-2xl text-yellow-800 flex items-center gap-3">
                <Calculator className="h-8 w-8" />
                Money Calculator Fun!
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 bg-white rounded-lg border-2 border-yellow-300">
                  <h4 className="text-xl font-bold text-yellow-800 mb-3">If I save $5 every week...</h4>
                  <div className="space-y-2 text-lg">
                    <div>In 1 month: <span className="font-bold text-green-600">$20</span></div>
                    <div>In 3 months: <span className="font-bold text-green-600">$60</span></div>
                    <div>In 1 year: <span className="font-bold text-green-600">$260</span></div>
                  </div>
                </div>
                
                <div className="p-4 bg-white rounded-lg border-2 border-yellow-300">
                  <h4 className="text-xl font-bold text-yellow-800 mb-3">Tithing Helper</h4>
                  <div className="space-y-2 text-lg">
                    <div>$10 earned → <span className="font-bold text-red-600">$1</span> tithe</div>
                    <div>$20 earned → <span className="font-bold text-red-600">$2</span> tithe</div>
                    <div>$50 earned → <span className="font-bold text-red-600">$5</span> tithe</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Goals Tab */}
        <TabsContent value="goals" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {goals?.map((goal) => (
              <EmergencyFundCard
                key={goal.id}
                goal={goal}
                persona="pre_teen"
                onAddFunds={() => toast({
                  title: "Great job! 🌟",
                  description: "You're doing amazing at saving money!",
                })}
              />
            ))}
          </div>

          {/* Fun Goal Ideas */}
          <Card className="border-4 border-green-200 bg-green-50">
            <CardHeader>
              <CardTitle className="text-2xl text-green-800">Fun Things to Save For! 🎯</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-white rounded-lg border-2 border-green-200">
                  <div className="text-4xl mb-2">🚲</div>
                  <div className="font-bold">New Bike</div>
                  <div className="text-sm text-gray-600">$200</div>
                </div>
                <div className="text-center p-4 bg-white rounded-lg border-2 border-green-200">
                  <div className="text-4xl mb-2">🎮</div>
                  <div className="font-bold">Video Game</div>
                  <div className="text-sm text-gray-600">$60</div>
                </div>
                <div className="text-center p-4 bg-white rounded-lg border-2 border-green-200">
                  <div className="text-4xl mb-2">🧸</div>
                  <div className="font-bold">Special Toy</div>
                  <div className="text-sm text-gray-600">$25</div>
                </div>
                <div className="text-center p-4 bg-white rounded-lg border-2 border-green-200">
                  <div className="text-4xl mb-2">🎁</div>
                  <div className="font-bold">Gift for Family</div>
                  <div className="text-sm text-gray-600">$15</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Learn Tab */}
        <TabsContent value="learn" className="space-y-6">
          <Card className="border-4 border-purple-200 bg-purple-50">
            <CardHeader>
              <CardTitle className="text-2xl text-purple-800 flex items-center gap-3">
                <BookOpen className="h-8 w-8" />
                Money Learning Adventures! 📚
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {learningModules.map((module, index) => (
                <div key={index} className={`p-4 rounded-lg border-3 ${module.completed ? 'bg-green-100 border-green-300' : 'bg-white border-purple-200'}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="text-3xl">{module.emoji}</div>
                      <div>
                        <h4 className="text-xl font-bold">{module.title}</h4>
                        <p className="text-gray-600">{module.completed ? 'Completed! 🌟' : 'Ready to learn!'}</p>
                      </div>
                    </div>
                    <Button 
                      className={module.completed ? 'bg-green-600 hover:bg-green-700' : 'bg-purple-600 hover:bg-purple-700'}
                    >
                      {module.completed ? '✅ Review' : '📖 Start'}
                    </Button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Bible Verse */}
          <Card className="bg-gradient-to-r from-blue-100 to-purple-100 border-4 border-blue-200">
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <div className="text-6xl">🙏</div>
                <blockquote className="text-2xl font-bold text-blue-800">
                  "Give, and it will be given to you."
                </blockquote>
                <cite className="text-lg text-blue-600">- Luke 6:38</cite>
                <p className="text-blue-700">
                  God loves it when we share and give to others! 💕
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Family Tab */}
        <TabsContent value="family" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Parent Messages */}
            <Card className="border-4 border-pink-200 bg-pink-50">
              <CardHeader>
                <CardTitle className="text-2xl text-pink-800 flex items-center gap-3">
                  <Heart className="h-8 w-8" />
                  Messages from Mom & Dad
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-white rounded-lg border-2 border-pink-200">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="text-2xl">👏</div>
                    <div className="font-bold text-pink-800">Great job this week!</div>
                  </div>
                  <p className="text-pink-700">You did all your chores and saved $10. We're so proud!</p>
                </div>
                
                <div className="p-4 bg-white rounded-lg border-2 border-pink-200">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="text-2xl">🎁</div>
                    <div className="font-bold text-pink-800">Special Bonus!</div>
                  </div>
                  <p className="text-pink-700">Extra $5 for helping grandma with groceries!</p>
                </div>
              </CardContent>
            </Card>

            {/* Achievement Gallery */}
            <Card className="border-4 border-yellow-200 bg-yellow-50">
              <CardHeader>
                <CardTitle className="text-2xl text-yellow-800 flex items-center gap-3">
                  <Trophy className="h-8 w-8" />
                  My Achievement Badges
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  {achievements.slice(0, 9).map((achievement, index) => (
                    <div key={index} className={`text-center p-3 rounded-lg border-2 ${achievement.earned ? 'bg-white border-yellow-300' : 'bg-gray-100 border-gray-300 opacity-50'}`}>
                      <div className="text-3xl mb-1">{achievement.emoji}</div>
                      <div className="text-xs font-bold">{achievement.name}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 text-center">
                  <Badge className="bg-yellow-100 text-yellow-800 text-lg px-4 py-2">
                    {achievements.filter(a => a.earned).length} / {achievements.length} Earned! 
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};