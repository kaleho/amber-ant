# Dual Categorization System: Plaid Categories + Fixed/Discretionary Types

## Overview
Every transaction in Faithful Finances requires **dual categorization**:
1. **Plaid Category** (merchant-based): groceries, health, rent, entertainment, etc.
2. **App Expense Type** (stewardship-based): fixed (needs) vs. discretionary (wants)

This system enables biblical financial stewardship by clearly distinguishing between essential needs and optional wants, while allowing for nuanced transaction splitting when a single purchase contains both types.

---

## The Dual Categorization Framework

### Plaid Categories (Merchant-Based)
Auto-assigned by Plaid based on merchant data:
- `groceries` - Food and household items
- `health` - Medical, pharmacy, fitness
- `rent` - Housing payments
- `transportation` - Gas, parking, public transit
- `entertainment` - Movies, dining out, streaming
- `shopping` - Retail purchases
- `utilities` - Electric, water, internet
- `education` - School, books, supplies
- And 50+ other standard categories...

### App Expense Types (Stewardship-Based)
User/system assigned based on biblical financial principles:
- **Fixed (Needs)**: Essential expenses required for basic living
- **Discretionary (Wants)**: Optional expenses that enhance lifestyle but aren't essential

### Transaction Splitting Capability
Any single transaction can be split between:
- **Same Plaid category, different expense types**: `groceries/fixed` + `groceries/discretionary`
- **Different combinations**: One grocery receipt could have `groceries/fixed` (eggs, milk) and `household/fixed` (cleaning supplies) and `groceries/discretionary` (cookies, wine)

---

## Persona-Specific Fixed vs. Discretionary Guidelines

### Pre-Teen (8-14 years)
**Educational Focus**: Learning to distinguish needs from wants

**Fixed Categories**:
- School supplies and required materials
- Essential clothing (basic school clothes)
- Required transportation to school/activities
- Tithing (10% of all income - highest priority)

**Discretionary Categories**:
- Toys and games
- Entertainment and movies  
- Candy and treats
- Premium clothing brands
- Extra activities beyond basic needs

**UI Approach**: Simple toggle with visual cues (Need 🏠 vs Want 🎁)

### Teen (15-17 years)
**Building Discipline**: Developing discernment with guidance

**Fixed Categories**:
- School supplies and textbooks
- Basic clothing and shoes
- Transportation to work/school
- Health and medical needs
- Required technology (basic phone plan)
- Tithing (10% priority)

**Discretionary Categories**:
- Entertainment and social activities
- Premium brands and fashion
- Eating out with friends
- Gaming and streaming subscriptions
- Upgraded technology beyond basic needs

**UI Approach**: Category suggestions with educational explanations

### College Student (18-22 years)
**Survival Budgeting**: Maximizing limited resources

**Fixed Categories**:
- Tuition and required fees
- Textbooks and academic materials
- Basic housing (dorm, essential furniture)
- Essential food and groceries
- Required transportation
- Basic health insurance and medical
- Minimum technology needed
- Tithing (even on limited income)

**Discretionary Categories**:
- Entertainment and social events
- Eating out and premium food
- Non-essential streaming services
- Fashion and premium brands
- Travel and vacations
- Upgraded technology

**UI Approach**: "Ramen mode" highlighting that helps minimize discretionary spending

### Single Adult (25-40 years)
**Professional Optimization**: Balancing career investment with stewardship

**Fixed Categories**:
- Housing (rent/mortgage, utilities, insurance)
- Essential transportation (car payment, gas, insurance)
- Basic food and household necessities
- Health insurance and medical care
- Emergency fund contributions
- Debt payments (student loans, etc.)
- Basic professional wardrobe
- Required technology and communications
- Tithing (first priority)

**Discretionary Categories**:
- Entertainment and dining out
- Premium food and beverages
- Travel and vacations
- Hobbies and recreational activities
- Premium brands and luxury items
- Professional development beyond required
- Upgraded technology and gadgets

**UI Approach**: Professional interface with investment vs. consumption analysis

### Married Couple (25-65 years)
**Joint Stewardship**: Coordinated needs vs. wants decisions

**Fixed Categories**:
- Housing and utilities
- Transportation for both spouses
- Essential food and household items
- Health insurance and medical care
- Joint emergency fund
- Debt payments
- Basic clothing and necessities
- Joint tithing (combined income)

**Discretionary Categories**:
- Entertainment and date nights
- Individual hobbies and interests
- Premium food and dining out
- Travel and recreation
- Individual allowances
- Luxury items and upgrades

**UI Approach**: Joint decision interface with individual allowance tracking

### Single Parent Family (25-45 years)
**Priority Protection**: Children's needs first, minimize discretionary

**Fixed Categories**:
- Housing and utilities
- Children's essential needs (food, clothing, medical)
- Childcare and education expenses
- Transportation to work/school
- Enhanced emergency fund (6-12 months)
- Basic adult necessities
- Children's required activities
- Tithing (trusting God's provision)

**Discretionary Categories**:
- Entertainment for family
- Non-essential children's activities
- Premium food and treats
- Adult personal items beyond basics
- Vacations and luxury experiences

**UI Approach**: Crisis prevention mode with children's needs prioritization

### Two Parent Family (30-50 years)
**Complex Coordination**: Managing multiple family member needs

**Fixed Categories**:
- Housing and utilities
- Transportation for family
- Children's essential needs (food, clothing, medical, education)
- Family health insurance
- Childcare when required for work
- Family emergency fund
- Basic adult necessities
- Required children's activities
- Family tithing

**Discretionary Categories**:
- Family entertainment and outings
- Children's extra activities and sports
- Family vacations and travel
- Premium food and dining out
- Individual parent discretionary allowances
- Luxury items and upgrades

**UI Approach**: Family coordination dashboard with member-specific tracking

### Fixed-Income (55+ years)
**Resource Conservation**: Maximizing limited retirement funds

**Fixed Categories**:
- Housing and utilities (often largest expense)
- Healthcare and medications (priority)
- Basic food and necessities
- Required transportation
- Insurance premiums
- Essential home maintenance
- Basic communication (phone, internet)
- Tithing (faithful stewardship continues)

**Discretionary Categories**:
- Entertainment and leisure activities
- Travel and vacations
- Premium food and dining out
- Gifts for family and charity beyond tithing
- Hobbies and recreational activities
- Luxury items and comfort upgrades

**UI Approach**: Healthcare-focused with clear fixed vs. luxury distinctions

---

## Transaction Splitting User Interface Design

### Splitting Workflow
1. **Transaction Import**: Plaid imports transaction with merchant category
2. **Initial Categorization**: System suggests fixed/discretionary based on learned patterns
3. **User Review**: User can accept, modify, or split the transaction
4. **Split Interface**: If splitting needed, user allocates amounts between categories
5. **Learning**: System learns from user decisions for future auto-categorization

### Split Transaction UI Components

#### TransactionSplitModal
```
Transaction: Walmart - $127.45
Plaid Category: groceries

Split Options:
┌─────────────────────────────────────┐
│ 🏠 Fixed (Needs)                    │
│ Amount: $89.23                      │
│ Categories: groceries/fixed         │
│           household/fixed           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🎁 Discretionary (Wants)            │
│ Amount: $38.22                      │
│ Categories: groceries/discretionary │
│           entertainment/discretionary│
└─────────────────────────────────────┘

Total: $127.45 ✓
[Save Split] [Cancel]
```

#### QuickSplitPresets
Common split patterns for different merchants:
- **Grocery Store**: 70% fixed / 30% discretionary
- **Target/Walmart**: 60% fixed / 40% discretionary  
- **Gas Station**: 90% fixed / 10% discretionary
- **Restaurant**: 10% fixed / 90% discretionary

### Smart Categorization Learning System

#### Machine Learning Categories
The system learns from user behavior to auto-suggest splits:

**Learning Factors**:
- Historical split patterns by merchant
- Persona-specific tendencies
- Transaction amounts and timing
- Seasonal variations (holidays, back-to-school)
- Family member who made the purchase

**Example Learning Patterns**:
- Target purchases on Sunday: 70% groceries/fixed, 30% household/discretionary
- Grocery store visits before holidays: 50% groceries/fixed, 50% groceries/discretionary
- Amazon purchases by teens: 20% fixed, 80% discretionary
- Pharmacy visits: 95% health/fixed, 5% health/discretionary

---

## Biblical Stewardship Integration

### Fixed vs. Discretionary Hierarchy
1. **Tithing** (10% of gross income) - Highest priority
2. **Fixed Expenses** (Essential needs) - Second priority
3. **Emergency Fund** - Third priority
4. **Discretionary Expenses** - Only after above are covered

### Stewardship Principles by Category Type

#### Fixed Expenses (Needs) - Biblical Justification
- "But if anyone does not provide for his relatives, and especially for members of his household, he has denied the faith and is worse than an unbeliever." (1 Timothy 5:8)
- Essential for family provision and basic living
- Should be minimized but not eliminated
- Quality vs. quantity decisions within needs

#### Discretionary Expenses (Wants) - Biblical Guidance
- "Keep your life free from love of money, and be content with what you have." (Hebrews 13:5)
- Should be enjoyed in moderation after obligations are met
- Opportunities for generosity beyond tithing
- Balance between enjoyment and excess

### Persona-Specific Stewardship Teachings

#### For Parents (Teaching Children)
- **Pre-Teen**: "We buy what we need first, then what we want if there's money left"
- **Teen**: "Learning to distinguish between needs and wants prepares you for adult financial responsibility"

#### For Adults (Personal Discipline)
- **Single Adult**: "Discretionary spending should align with your values and future goals"
- **Married Couple**: "Joint decisions on discretionary spending prevent conflict and promote unity"
- **Parents**: "Our spending choices model stewardship principles for our children"

#### For Seniors (Wisdom Sharing)
- **Fixed-Income**: "Experience teaches us the difference between what we need and what we think we need"

---

## Implementation Requirements

### Database Schema Updates

#### Transactions Table
```sql
transactions {
  id: string
  plaid_transaction_id: string
  amount: number
  date: date
  merchant_name: string
  plaid_category: string (groceries, health, etc.)
  
  -- New fields for dual categorization
  app_expense_type: enum('fixed', 'discretionary', 'split')
  fixed_amount: number (null if not split)
  discretionary_amount: number (null if not split)
  
  -- For split transactions
  is_split: boolean
  split_details: json {
    fixed_categories: [{category: string, amount: number}]
    discretionary_categories: [{category: string, amount: number}]
  }
}
```

#### Category Learning Table
```sql
category_learning {
  id: string
  user_id: string
  merchant_name: string
  plaid_category: string
  suggested_fixed_percentage: number
  confidence_score: number
  last_updated: timestamp
}
```

### API Endpoints

#### Transaction Categorization
- `POST /transactions/{id}/categorize` - Set fixed/discretionary type
- `POST /transactions/{id}/split` - Split transaction between categories
- `GET /transactions/categorization-suggestions` - Get AI suggestions for uncategorized

#### Learning System
- `POST /learning/update-pattern` - Update learning from user categorization
- `GET /learning/suggestions/{merchant}` - Get learned patterns for merchant

### UI Component Updates

#### Enhanced Transaction List
- Show dual categorization visually
- Quick categorization buttons
- Split transaction indicators
- Learning suggestion badges

#### Budget Planning Updates
- Separate fixed and discretionary budget categories
- Visual hierarchy showing tithing → fixed → discretionary
- Split transaction impact on multiple budget categories

#### Dashboard Enhancements
- Fixed vs. discretionary spending ratios
- "Stewardship score" based on needs-first prioritization
- Alerts when discretionary spending exceeds fixed spending

---

## Success Metrics

### Categorization Accuracy
- **Auto-categorization accuracy**: >85% for fixed vs. discretionary
- **User override rate**: <20% of transactions require manual adjustment
- **Learning improvement**: Accuracy increases 5% per month with usage

### Biblical Stewardship Metrics
- **Tithing first**: 95% of users pay tithing before discretionary expenses
- **Needs prioritization**: Fixed expenses covered before 80% of discretionary spending
- **Emergency fund**: 60% build emergency funds by reducing discretionary spending

### User Engagement
- **Transaction review rate**: 70% of users review and categorize transactions within 48 hours
- **Split usage**: 40% of users utilize transaction splitting feature monthly
- **Learning acceptance**: 80% acceptance rate of AI categorization suggestions

This dual categorization system ensures that Faithful Finances maintains biblical financial stewardship principles while providing the practical tools needed to distinguish between needs and wants in every spending decision.