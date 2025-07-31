# Faithful Finances API Contracts

This directory contains the API contract specifications and mock data for the Faithful Finances application, enabling parallel frontend and backend development.

## Files

### `openapi-contract.json`
Comprehensive OpenAPI 3.0.3 specification defining all API endpoints, request/response schemas, and authentication requirements.

### `mock-data.json`
Sample data representing all entities in the system, including users across different personas, transactions with dual categorization, family structures, and financial goals.

## Key Features Covered

### 🔐 Authentication & Authorization
- Auth0 JWT token authentication
- Role-based access control for family members
- API key authentication for service-to-service communication

### 👥 User Management (8 Personas)
- **Pre-Teen (8-14)**: Supervised financial learning with parental approval
- **Teen (15-17)**: Building independence with parental oversight
- **College Student (18-22)**: Managing irregular income and academic expenses
- **Single Adult (25-40)**: Complete financial independence and career focus
- **Married Couple (25-65)**: Joint financial management and coordination
- **Single Parent (25-45)**: Priority-based budgeting with crisis prevention
- **Two Parent Family (30-50)**: Complex family financial coordination
- **Fixed Income (55+)**: Healthcare-focused retirement planning

### 💰 Financial Management
- **Plaid Integration**: Bank account connection and transaction sync
- **Dual Categorization**: Plaid categories + Fixed/Discretionary expense types
- **Transaction Splitting**: Split single transactions across multiple categories
- **Budget Management**: Persona-specific budget templates and tracking
- **Savings Goals**: Emergency fund management with persona-appropriate targets

### ⛪ Biblical Stewardship
- **Tithing Calculation**: 10% of gross income tracking and reporting
- **Fixed vs Discretionary**: Biblical needs vs wants classification
- **Stewardship Principles**: Built into categorization and budgeting logic

### 👨‍👩‍👧‍👦 Family Collaboration
- **Family Plans**: Multi-user coordination with role-based permissions
- **Parental Controls**: Approval workflows for minors
- **Member Invitations**: Secure email-based family member onboarding
- **Permission Management**: Granular control over financial data access

### 💳 Subscription Management
- **Free Plan**: Basic features for all personas
- **Premium Individual**: Advanced features for single users
- **Premium Family**: Full family collaboration and advanced features

## API Endpoints Overview

### System
- `GET /health` - Health check and status monitoring

### Authentication & Users
- `GET /auth/me` - Current user profile
- `POST /users` - Create new user account
- `GET|PUT /users/{userId}` - User profile management

### Bank Integration
- `POST /plaid/link-token` - Initialize bank account connection
- `POST /plaid/exchange-token` - Complete account linking
- `GET /accounts` - Connected financial accounts

### Transactions
- `GET /transactions` - Transaction history with filtering
- `POST /transactions` - Manual transaction entry (pre-teen persona)
- `PUT /transactions/{transactionId}` - Update categorization
- `POST /transactions/{transactionId}/split` - Split transaction

### Budgeting & Goals
- `GET|POST /budgets` - Budget management
- `GET|POST /goals` - Savings goal tracking
- `GET|POST /tithing` - Tithing calculation and payments

### Family Management
- `POST /families` - Create family plan
- `POST /families/{familyId}/invitations` - Invite family members
- `PUT /families/{familyId}/members/{memberId}/permissions` - Manage permissions

### Subscriptions
- `GET|POST|PUT|DELETE /subscriptions` - Subscription plan management

## Mock Data Structure

### Users (8 personas represented)
- Complete user profiles with persona-specific preferences
- Family relationships and role assignments
- Notification preferences and settings

### Financial Data
- Realistic bank accounts with current balances
- Transaction history showing dual categorization
- Split transactions demonstrating mixed needs/wants purchases
- Income transactions marked for tithing calculation

### Family Structures
- **Johnson Family**: Married couple with teen daughter
- **Williams Family**: Single parent with pre-teen child
- Invitation system and permission management examples

### Budgets & Goals
- Persona-appropriate budget categories and amounts
- Emergency fund goals with realistic progress tracking
- Tithing summaries showing faithful stewardship

### Templates & Patterns
- Common transaction split patterns by merchant type
- Persona-specific budget templates
- Categorization learning data for smart suggestions

## Usage for Development

### Frontend Development
Use the OpenAPI specification to:
1. Generate TypeScript interfaces and API client code
2. Mock API responses during development
3. Validate request/response structures
4. Build persona-specific UI components

### Backend Development
Use the specification to:
1. Implement FastAPI endpoints with automatic validation
2. Generate API documentation
3. Create database schemas matching the data models
4. Implement business logic for dual categorization

### Testing
Use mock data for:
1. Component testing with realistic data scenarios
2. Integration testing across different personas
3. Family workflow testing
4. Edge case validation (split transactions, permissions)

## Biblical Stewardship Integration

The API design reflects core biblical financial principles:

### Tithing Priority
- All income detection automatically calculates 10% tithing obligation
- Tithing tracking is prominent across all personas
- Annual giving statements for tax purposes

### Needs vs Wants Classification
- Every transaction requires fixed (needs) or discretionary (wants) classification
- Smart suggestions based on biblical stewardship principles
- Visual indicators helping users make godly financial decisions

### Family Stewardship
- Joint tithing calculation for married couples
- Parental oversight for children's financial education
- Family coordination preventing financial conflict

### Emergency Fund Emphasis
- Single primary savings goal (emergency fund) to avoid complexity
- Persona-appropriate emergency fund targets
- Progress tracking encouraging faithful preparation

This contract enables development teams to work independently while ensuring the final application maintains biblical stewardship principles and serves all 8 target personas effectively.