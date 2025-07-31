# Faithful Finances - Functional Requirements Document
**Version:** 1.0  
**Date:** July 31, 2025  
**Project:** Personal Finance Application Based on Biblical Stewardship Principles

## 1. Introduction

### 1.1 Purpose
This document defines the functional requirements for Faithful Finances, a personal finance application designed around biblical stewardship principles. The application serves eight distinct user personas with a focus on tithing, budgeting, and savings management.

### 1.2 Scope
The functional requirements are based on seven MVP features and designed to serve eight user personas:
- **Pre-Teen (8-14 years)**
- **Teen (15-17 years)**
- **College Student (18-22 years)**
- **Single Adult (25-40 years)**
- **Married Couple (25-65 years)**
- **Single Parent Family (25-45 years)**
- **Two Parent Family (30-50 years)**
- **Fixed-Income (55+ years)**

### 1.3 Biblical Foundation
All requirements are grounded in biblical principles of stewardship, with tithing as the cornerstone practice (Malachi 3:10, Deuteronomy 14:22).

## 2. User Stories by Feature

### 2.1 Plaid Integration for Automated Transaction Data Retrieval

#### FR-001: Account Connection
**As a** user across all personas,  
**I want to** securely connect my bank accounts and credit cards through Plaid,  
**So that** my transaction data is automatically retrieved without manual entry.

**Acceptance Criteria:**
- Support for checking, savings, and credit card accounts
- AES-256 encryption and TLS security
- Multi-factor authentication support
- Real-time transaction updates via webhooks
- Plaid Portal integration for account management

**Persona-Specific Requirements:**
- **Pre-Teen:** No bank account linking allowed; manual entry only with parental oversight
- **Teen:** Parental consent required for account linking
- **College Student:** Student account type recognition
- **Fixed-Income:** Enhanced fraud protection and verification
- **Married Couple:** Joint account sharing capabilities
- **Single Parent:** Quick setup with minimal steps

#### FR-002: Transaction Categorization
**As a** user,  
**I want** transactions to be automatically categorized,  
**So that** my budgeting and tithing calculations are accurate.

**Acceptance Criteria:**
- >90% accuracy in transaction categorization
- Manual category override capability
- Custom category creation
- Income deposit recognition for tithing calculation

### 2.2 Tithing Calculator and Tracking

#### FR-003: Tithe Calculation
**As a** faithful steward,  
**I want** to calculate my tithe as 10% of gross income,  
**So that** I honor the biblical principle of first fruits.

**Acceptance Criteria:**
- 10% gross income calculation (universal across all personas)
- Manual adjustment capability for special circumstances
- Multiple income source support
- Historical tithe tracking
- Tax reporting support

**Persona-Specific Requirements:**
- **Pre-Teen:** Focus on allowance and chore money tracking; simplified 10% calculation with parental oversight
- **Teen:** Educational tooltips about tithing principles
- **College Student:** Variable income pattern recognition
- **Fixed-Income:** Social Security and benefit income support
- **Single Parent:** Child support income considerations

#### FR-004: Tithe Payment Tracking
**As a** user,  
**I want to** track my tithe payments,  
**So that** I can ensure consistent biblical obedience.

**Acceptance Criteria:**
- Manual tithe payment logging
- Payment method tracking (cash, check, online)
- Church/organization designation
- Payment reminder notifications
- Annual giving statements

#### FR-004A: Parent-Child Financial Collaboration
**As a** parent with a pre-teen child,  
**I want** to collaborate with my child on their financial tracking,  
**So that** I can guide their learning while they practice financial responsibility.

**Acceptance Criteria:**
- Parent-child shared access to pre-teen's financial data
- Parental approval workflow for spending decisions
- Simple transaction logging for allowance and chore money
- Parent oversight of tithing and savings goals
- Basic reporting for parent-child financial discussions

**Pre-Teen Specific Features:**
- Simple allowance and chore money tracking
- Parent-approved spending categories
- Visual progress tracking for savings goals
- Parent notification system for spending requests

### 2.3 Basic Budgeting Tool with Plaid Integration

#### FR-005: Budget Creation
**As a** user,  
**I want to** create a monthly budget with pre-defined categories,  
**So that** I can live within my means according to biblical principles.

**Acceptance Criteria:**
- Pre-built budget template based on biblical stewardship
- Fixed and discretionary spending categories
- Automated transaction categorization
- Budget vs. actual spending tracking
- Overspending alerts

**Persona-Specific Requirements:**
- **Pre-Teen:** Basic spend/save/give categories with parental approval
- **Teen:** Simplified categories with educational content
- **College Student:** Academic calendar-based budgeting
- **Married Couple:** Joint budget management
- **Two Parent Family:** Child-related expense categories
- **Fixed-Income:** Healthcare and prescription categories

#### FR-006: Budget Monitoring
**As a** user,  
**I want to** monitor my spending against my budget,  
**So that** I can maintain financial discipline.

**Acceptance Criteria:**
- Real-time spending updates
- Category-specific overspending alerts
- Visual progress indicators
- Budget adjustment recommendations
- End-of-month budget reports

### 2.4 Savings Goal Tracker for Emergency Fund

#### FR-007: Savings Goal Setting
**As a** responsible steward,  
**I want to** set and track an emergency fund savings goal,  
**So that** I'm prepared for unexpected expenses.

**Acceptance Criteria:**
- Single savings goal focus (emergency fund)
- Goal amount and target date setting
- Automated savings tracking via Plaid
- Progress visualization
- Achievement notifications

**Persona-Specific Requirements:**
- **Pre-Teen:** Small, achievable savings goals (toy, bike, etc.) with parent-supervised progress tracking
- **Teen:** Age-appropriate savings targets
- **College Student:** Semester-based goal setting
- **Single Parent:** Priority-based savings allocation
- **Fixed-Income:** Healthcare emergency fund focus

#### FR-008: Savings Progress Tracking
**As a** user,  
**I want to** track my progress toward my savings goal,  
**So that** I stay motivated and on track.

**Acceptance Criteria:**
- Visual progress bar
- Milestone celebrations
- Goal at-risk alerts
- Contribution suggestions
- Achievement badges

### 2.5 User-Friendly Dashboard

#### FR-009: Financial Overview
**As a** user,  
**I want** a centralized dashboard showing my financial status,  
**So that** I can quickly understand my stewardship position.

**Acceptance Criteria:**
- Account balance summary
- Budget status overview
- Tithing progress display
- Savings goal progress
- Recent transaction summary
- Quick-access tithing calculator

**Persona-Specific Requirements:**
- **Pre-Teen:** Simple dashboard with basic progress bars and parent-shared view
- **Teen:** Gamified progress elements
- **College Student:** Mobile-optimized layout
- **Fixed-Income:** Large fonts and high contrast
- **Married Couple:** Joint financial overview

#### FR-010: Dashboard Customization
**As a** user,  
**I want to** customize my dashboard widgets,  
**So that** I see the most relevant information first.

**Acceptance Criteria:**
- Widget reordering capability
- Show/hide widget options
- Persona-based default layouts
- Color theme customization

### 2.6 Secure Data Management and Privacy Controls

#### FR-011: Data Security
**As a** user,  
**I want** my financial data to be secure,  
**So that** I can trust the application with sensitive information.

**Acceptance Criteria:**
- AES-256 encryption for data at rest
- TLS encryption for data in transit
- Multi-factor authentication
- Regular security audits
- GDPR/CCPA compliance

#### FR-012: Privacy Controls
**As a** user,  
**I want to** control my data privacy settings,  
**So that** I maintain control over my personal information.

**Acceptance Criteria:**
- Plaid Portal integration for account management
- Data sharing preferences
- Account connection revocation
- Data export capability
- Account deletion option

### 2.7 Goal-Based Notifications

#### FR-013: Progress Notifications
**As a** user,  
**I want to** receive notifications about my financial progress,  
**So that** I stay engaged with my stewardship goals.

**Acceptance Criteria:**
- Savings milestone notifications
- Budget overspending alerts
- Tithe payment reminders
- Goal achievement celebrations
- Weekly progress summaries

**Persona-Specific Requirements:**
- **Pre-Teen:** Simple progress notifications; parental alerts for all activities
- **Teen:** Gamified achievement notifications
- **College Student:** Text-based notifications
- **Fixed-Income:** Email notification preference
- **Single Parent:** Priority-based alert system

#### FR-014: Customizable Alerts
**As a** user,  
**I want to** customize my notification preferences,  
**So that** I receive relevant alerts without overwhelm.

**Acceptance Criteria:**
- Notification type selection
- Frequency preferences
- Delivery method options (push, email, SMS)
- Quiet hours setting
- Emergency alert override

### 2.8 Subscription and Plan Management

#### FR-015: Plan-Based Feature Access
**As a** user,  
**I want** to access features based on my subscription plan,  
**So that** I can use appropriate functionality for my life stage and financial capacity.

**Acceptance Criteria:**
- Plan-based feature enablement and restrictions
- Automatic plan transitions based on age and life stage
- Usage monitoring and limit enforcement
- Upgrade prompts when approaching plan limits
- Grace period for plan transitions

**Plan-Specific Features:**
- **Free Plans:** Basic features with usage limits
- **Single Plan:** Advanced features and unlimited usage  
- **Family Plans:** Collaborative features and multi-user access

#### FR-016: Family Invitation System
**As a** family plan subscriber,  
**I want** to invite family members via email,  
**So that** we can collaborate on our family's financial stewardship.

**Acceptance Criteria:**
- Application-generated email invitations with secure tokens
- Role-based invitation templates (spouse, teen, pre-teen, extended family)
- Invitation acceptance workflow linking to existing or new Auth0 accounts
- Token-based security with expiration and single-use validation
- Invitation status tracking and management

**Invitation Workflow:**
1. **Family Administrator** creates invitation with specified role
2. **System generates** secure invitation token and email template
3. **Email sent** to recipient with role-specific invitation message
4. **Recipient clicks** secure invitation link
5. **System validates** token and redirects to Auth0 login/registration
6. **Upon authentication**, system links Auth0 user to family with assigned role
7. **Family membership** established in application database

**Invitation Management:**
- View pending, accepted, and expired invitations
- Resend invitations with new tokens
- Revoke pending invitations
- Remove family members and revoke access
- Audit trail of all invitation activities

#### FR-017: Subscription Management
**As a** paid plan subscriber,  
**I want** to manage my subscription and billing,  
**So that** I can control my account and payments.

**Acceptance Criteria:**
- Stripe-based subscription signup and payment processing
- Plan upgrade and downgrade functionality via Stripe portal
- Billing history and invoice access through Stripe integration
- Payment method management (cards, bank accounts, digital wallets)
- Subscription cancellation with configurable data retention
- Webhook handling for subscription state changes

**Stripe Integration Features:**
- Monthly and annual billing cycles with Stripe subscriptions
- Automatic plan transitions with proration handling
- Failed payment retry logic and dunning management
- Tax calculation and invoice generation
- Customer portal for self-service billing management
- Usage-based billing alerts and plan optimization recommendations

**Technical Requirements:**
- Stripe API integration for subscription lifecycle management
- Secure webhook endpoint for real-time subscription updates
- PCI DSS compliance through Stripe's secure payment processing
- Multi-currency support for international users

#### FR-018: Authentication
**As a** user,  
**I want** secure authentication,  
**So that** my financial data is protected with industry-standard security.

**Acceptance Criteria:**
- Auth0 integration for authentication (free plan features only)
- Social login options (Google, Apple, Facebook - limited connections)
- Multi-factor authentication (MFA) support via Auth0
- User registration and login management
- Password reset and recovery functionality
- Basic user profile management

**Auth0 Free Plan Features:**
- Universal Login for consistent user experience
- Database connections for username/password authentication
- Social connections (limited number on free plan)
- Basic MFA support (TOTP, SMS where available)
- User Management API for basic operations
- JWT token issuance with basic user claims
- Password policy enforcement

**Security Features:**
- Breach password detection via Auth0
- Basic anomaly detection for unusual login patterns
- Secure password storage and hashing
- Account lockout protection
- Email verification for new accounts

#### FR-019: Application-Level Family Management
**As a** family plan subscriber,  
**I want** to manage my family members and their permissions within the application,  
**So that** we can collaborate on our financial stewardship with appropriate access controls.

**Acceptance Criteria:**
- Family membership management within application database
- Role-based permission system implemented in application logic
- Family member invitation via application-generated emails
- User role assignment and management interface
- Family hierarchy and relationship tracking
- Permission inheritance and override capabilities

**Family Management Features:**
- **Family Creation:** Establish family units with primary administrator
- **Member Invitation:** Send email invitations with secure tokens
- **Role Assignment:** Assign and modify family member roles
- **Permission Management:** Granular control over financial data access
- **Member Removal:** Remove family members and revoke access
- **Family Settings:** Configure family-wide preferences and policies

**Application-Managed Roles:**
- **Administrator:** Full family financial management and member control
  - Invite/remove family members
  - Assign/modify roles and permissions
  - Access all family financial data
  - Manage subscription and billing
- **Spouse:** Joint financial management with collaborative access
  - View and edit joint financial data
  - Invite children to family (with admin approval)
  - Shared budgeting and goal management
- **Teen (15-17):** Supervised financial tracking with parental oversight
  - Personal financial tracking with parental visibility
  - Request spending approvals
  - Limited account linking with parental consent
- **Pre-Teen (8-14):** Basic tracking with full parental supervision
  - Manual entry only with parental approval
  - Parent-supervised savings goals
  - All transactions require parental confirmation
- **Extended Family:** Read-only access for transparency and accountability
  - View family financial health indicators
  - No editing or transaction capabilities
- **Support:** Time-bound technical support access (disabled by default)
  - Administrator-granted temporary access with specified duration (hours)
  - Full Account database access equivalent to Administrator when active
  - All activities logged in Global database audit trail
  - Automatic access revocation after time limit expires
  - Cannot modify Administrator permissions or billing information
- **Agent:** Automated process control role (Administrator controlled)
  - Controls all automated processes within Account database
  - Handles transaction categorization, notifications, calculations
  - Administrator can enable/disable with impact warnings
  - When disabled: all automation stops, Administrator performs manually
  - Activity logging within Account database

**Database Schema Requirements:**

**Global Database Schema:**
- User accounts linked to Auth0 user IDs with Account database mapping
- Account database metadata (size, users, Turso location)
- Support role access grants with time-bound controls
- Stripe subscription and billing management
- Administrator reset tokens and audit trails
- Cross-account operational data (no financial information)

**Account Database Schema (Per Account/Plan):**
- Family membership tables with role assignments
- Permission matrices for feature access control
- All financial data (transactions, budgets, goals, tithing)
- Plaid account connections and transaction data
- Agent automation settings and activity logs
- User financial history and personalized reports
- Invitation tokens and expiration management (family-specific)
- Audit trails for role changes and family modifications

#### FR-020: Support Role Management
**As an** Administrator,  
**I want** to grant time-bound technical support access to my account,  
**So that** support staff can help resolve issues while maintaining security and control.

**Acceptance Criteria:**
- Administrator can grant Support role access for specified duration (1-48 hours)
- Support access request and approval workflow with clear impact disclosure
- Support role gains temporary Administrator-level access to Account database only
- All Support activities logged in Global database with detailed audit trail
- Automatic access revocation after specified time limit expires
- Support role cannot modify Administrator permissions or billing information
- Administrator can revoke Support access at any time before expiration
- Clear notification system for when Support access is granted, active, and revoked

**Support Access Workflow:**
1. **Support Request:** Technical support requests account access with justification
2. **Administrator Notification:** Administrator receives access request with impact details
3. **Access Grant:** Administrator approves with specific time duration (1-48 hours)
4. **Token Generation:** Secure access token created in Global database
5. **Support Access:** Support staff gains temporary Account database access
6. **Activity Logging:** All Support actions logged with timestamps and details
7. **Automatic Revocation:** Access automatically revoked after time limit
8. **Access Audit:** Complete audit trail available to Administrator

**Security Requirements:**
- Support access tokens stored securely in Global database
- No permanent Support access - all grants are time-bound
- Complete activity logging for compliance and transparency
- Administrator maintains ultimate control over Support access
- Support role cannot invite new users or modify critical account settings

#### FR-021: Agent Role Management
**As an** Administrator,  
**I want** to control automated processes in my account,  
**So that** I can choose between automation and manual control based on my preferences.

**Acceptance Criteria:**
- Administrator can enable/disable Agent role with clear impact warnings
- Agent role controls ALL automated processes within Account database
- When enabled: automatic transaction categorization, notifications, calculations, alerts
- When disabled: Administrator must perform all operations manually
- Clear impact disclosure when disabling Agent role (loss of automation features)
- Agent activity logging within Account database for transparency
- Default Agent role setting (enabled) with opt-out capability
- Granular automation control for specific features (future enhancement placeholder)

**Automated Processes Controlled by Agent Role:**
- **Transaction Categorization:** Automatic categorization of Plaid transaction data
- **Tithing Calculations:** Automated 10% gross income calculations from deposits
- **Budget Monitoring:** Automatic spending alerts and overspending notifications
- **Savings Progress:** Automated goal progress tracking and milestone notifications
- **Payment Reminders:** Automatic tithing and bill payment reminders
- **Data Synchronization:** Automated Plaid data refresh and account balance updates
- **Report Generation:** Automated monthly and annual financial report creation

**Impact Warning System:**
- Clear explanation of features that will stop working when Agent role is disabled
- List of manual tasks Administrator must perform when automation is disabled
- Option to re-enable Agent role at any time
- Confirmation dialog for disabling Agent role with impact checklist
- Help documentation for manual processes when automation is disabled

**Manual Fallback Requirements:**
- All automated processes must have manual Administrator alternatives
- Clear instructions for manual execution of each automated process
- User interface adaptations when Agent role is disabled (manual action buttons)
- Data integrity maintained whether using automated or manual processes

## 3. Business Rules

### BR-001: Tithing Priority
Tithing calculations and tracking must always take priority over other financial allocations in the application interface and logic.

### BR-002: Universal Tithing Rate
The standard tithing rate is 10% of gross income across all personas, with manual override capability for special circumstances.

### BR-003: Data Accuracy
All financial calculations must be accurate to two decimal places with proper rounding according to standard accounting principles.

### BR-004: Privacy First
User financial data must never be shared with third parties without explicit user consent, following biblical principles of trustworthiness.

### BR-005: Age Verification and Parental Oversight
Users under 18 require parental consent for account linking and financial data access. Pre-teens (8-14) are restricted to manual entry only with full parental oversight.

### BR-006: Collaboration Priority for Young Users
Pre-teen users must operate under full parental supervision with shared access to all financial data and approval workflows for spending decisions.

### BR-007: Free Plan Accessibility
Pre-teen, Teen, College Student, and Fixed Income users must have access to core biblical financial stewardship features at no cost to support formation and accessibility.

### BR-008: Family Plan Authority
Family plan administrators have ultimate authority over family member access, permissions, and financial data visibility within the family unit.

### BR-009: Plan-Based Feature Limits
Feature access and usage limits must be enforced based on subscription plan with clear upgrade paths for users approaching limits.

### BR-010: Database Isolation Mandatory
All financial data must be completely isolated in separate Account databases with no cross-database queries to ensure complete privacy and security between accounts.

### BR-011: Support Access Time-Bound and Audited
Support role access must always be time-bound (1-48 hours), require Administrator approval, and maintain complete audit trails in the Global database.

### BR-012: Agent Role Controls Automation Features
The Agent role must control ALL automated processes within an account, and when disabled, all automation must stop with clear manual alternatives provided to the Administrator.

## 4. Constraints and Assumptions

### 4.1 Technical Constraints
- Plaid API integration required for automated transaction data
- Stripe API integration required for all payment processing and subscription management
- Auth0 integration required for authentication, authorization, and user management
- Turso database architecture required for Global and Account database separation
- Complete database isolation - no cross-database queries permitted
- Mobile-first design approach
- Progressive Web App (PWA) implementation
- Browser compatibility: Chrome, Safari, Firefox, Edge

### 4.2 Regulatory Constraints
- PCI DSS compliance for payment card data
- GDPR compliance for European users
- CCPA compliance for California users
- Financial services regulations as applicable

### 4.3 Business Assumptions
- Users have basic smartphone or computer access
- Users maintain active bank accounts
- Users are motivated by faith-based financial principles
- Initial user base will be primarily English-speaking

## 5. Acceptance Criteria Summary

All functional requirements must be:
- **Testable:** Clear success criteria defined
- **Traceable:** Linked to specific MVP features and personas
- **Measurable:** Quantifiable outcomes specified
- **Faith-Based:** Aligned with biblical stewardship principles
- **Accessible:** Usable across all defined personas

## 6. Future Considerations

While outside the current MVP scope, future enhancements may include:
- Multiple savings goals
- Investment tracking
- Tax preparation integration
- Church giving integration
- Financial education modules
- Community accountability features

---

**Document Control:**
- Author: Product Management Team
- Reviewers: Development Team, Faith Advisory Board
- Approval: Product Owner
- Next Review Date: August 31, 2025