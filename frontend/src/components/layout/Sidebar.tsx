import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  CreditCard, 
  Receipt, 
  PiggyBank, 
  Target, 
  Heart, 
  Users, 
  Settings,
  X,
  ChevronRight,
  DollarSign,
  TrendingUp,
  Shield,
  BookOpen,
  Gamepad2,
  GraduationCap
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { PersonaType } from '@/types';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  userPersona?: PersonaType;
}

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  personas?: PersonaType[];
  badge?: string;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Accounts', href: '/accounts', icon: CreditCard },
  { name: 'Transactions', href: '/transactions', icon: Receipt },
  { name: 'Budgets', href: '/budgets', icon: PiggyBank },
  { name: 'Goals', href: '/goals', icon: Target },
  { name: 'Tithing', href: '/tithing', icon: Heart },
  { 
    name: 'Family', 
    href: '/family', 
    icon: Users,
    personas: ['married_couple', 'single_parent', 'two_parent_family']
  },
  { name: 'Settings', href: '/settings', icon: Settings },
];

// Persona-specific quick actions
const personaActions = {
  pre_teen: [
    { name: 'Add Allowance', href: '/transactions/new', icon: DollarSign },
    { name: 'Savings Goal', href: '/goals', icon: Target },
    { name: 'Learn & Play', href: '/education', icon: Gamepad2 },
  ],
  teen: [
    { name: 'Job Income', href: '/transactions/new', icon: TrendingUp },
    { name: 'Emergency Fund', href: '/goals', icon: Shield },
    { name: 'Learn Finance', href: '/education', icon: BookOpen },
  ],
  college_student: [
    { name: 'Financial Aid', href: '/transactions/new', icon: GraduationCap },
    { name: 'Textbook Budget', href: '/budgets', icon: BookOpen },
    { name: 'Emergency Fund', href: '/goals', icon: Shield },
  ],
  single_adult: [
    { name: 'Quick Transaction', href: '/transactions/new', icon: Receipt },
    { name: 'Investment Goals', href: '/goals', icon: TrendingUp },
    { name: 'Career Budget', href: '/budgets', icon: Target },
  ],
  married_couple: [
    { name: 'Joint Budget', href: '/budgets', icon: PiggyBank },
    { name: 'Family Goals', href: '/goals', icon: Target },
    { name: 'Spouse Overview', href: '/family', icon: Users },
  ],
  single_parent: [
    { name: 'Child Expenses', href: '/transactions', icon: Receipt },
    { name: 'Emergency Fund', href: '/goals', icon: Shield },
    { name: 'Quick Budget', href: '/budgets', icon: PiggyBank },
  ],
  two_parent_family: [
    { name: 'Family Budget', href: '/budgets', icon: PiggyBank },
    { name: 'Education Fund', href: '/goals', icon: GraduationCap },
    { name: 'Family Overview', href: '/family', icon: Users },
  ],
  fixed_income: [
    { name: 'Healthcare Budget', href: '/budgets', icon: Shield },
    { name: 'Fixed Expenses', href: '/transactions', icon: Receipt },
    { name: 'Retirement Goals', href: '/goals', icon: Target },
  ],
};

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, userPersona }) => {
  const location = useLocation();

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return location.pathname === '/dashboard' || location.pathname.startsWith('/dashboard/');
    }
    return location.pathname.startsWith(href);
  };

  const shouldShowNavItem = (item: NavItem) => {
    if (!item.personas) return true;
    return userPersona && item.personas.includes(userPersona);
  };

  const getPersonaName = (persona: PersonaType) => {
    const names = {
      pre_teen: 'Pre-Teen',
      teen: 'Teen',
      college_student: 'College Student',
      single_adult: 'Single Adult',
      married_couple: 'Married Couple',
      single_parent: 'Single Parent',
      two_parent_family: 'Two Parent Family',
      fixed_income: 'Fixed Income'
    };
    return names[persona] || persona;
  };

  return (
    <>
      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r transform transition-transform duration-300 ease-in-out lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center justify-between px-4 border-b">
            <div className="flex items-center gap-2">
              <Heart className="h-8 w-8 text-primary" />
              <span className="font-bold text-lg">Faithful Finances</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Persona indicator */}
          {userPersona && (
            <div className="px-4 py-3 bg-muted/30 border-b">
              <p className="text-sm text-muted-foreground">Your profile</p>
              <p className="text-sm font-medium">{getPersonaName(userPersona)}</p>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
            {navigation.filter(shouldShowNavItem).map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive(item.href)
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                  {item.badge && (
                    <span className="ml-auto bg-primary text-primary-foreground text-xs px-2 py-0.5 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}

            {/* Persona-specific quick actions */}
            {userPersona && personaActions[userPersona] && (
              <div className="pt-4 mt-4 border-t">
                <p className="px-3 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Quick Actions
                </p>
                <div className="space-y-1">
                  {personaActions[userPersona].map((action) => {
                    const Icon = action.icon;
                    return (
                      <Link
                        key={action.name}
                        to={action.href}
                        onClick={onClose}
                        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors text-muted-foreground hover:bg-muted hover:text-foreground"
                      >
                        <Icon className="h-4 w-4" />
                        {action.name}
                        <ChevronRight className="ml-auto h-4 w-4" />
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}
          </nav>

          {/* Footer */}
          <div className="border-t p-4">
            <p className="text-xs text-muted-foreground text-center">
              "For where your treasure is, there your heart will be also." - Matthew 6:21
            </p>
          </div>
        </div>
      </div>
    </>
  );
};