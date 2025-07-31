# Transaction Splitting UI Specifications

## Overview
This document provides detailed UI specifications for the transaction splitting interface that enables users to categorize single transactions into both Plaid merchant categories and Fixed/Discretionary expense types, with the ability to split amounts across multiple categories.

---

## Core Transaction Splitting Components

### 1. TransactionSplitModal

#### Component Purpose
Primary interface for splitting a single transaction into multiple categories with different fixed/discretionary classifications.

#### Visual Layout
```
┌─────────────────────────────────────────────────────────┐
│ Split Transaction                                    [X] │
├─────────────────────────────────────────────────────────┤
│ 🏪 Walmart Supercenter                    $127.45       │
│ Jan 15, 2025 • Original: groceries                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 🏠 FIXED EXPENSES (Needs)                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Amount: $89.23                                      │ │
│ │ ┌─────────────────────┐ ┌─────────────────────────┐ │ │
│ │ │ groceries/fixed     │ │ $65.50                  │ │ │
│ │ │ ▼                   │ │                         │ │ │
│ │ └─────────────────────┘ └─────────────────────────┘ │ │
│ │ ┌─────────────────────┐ ┌─────────────────────────┐ │ │
│ │ │ household/fixed     │ │ $23.73                  │ │ │
│ │ │ ▼                   │ │                         │ │ │
│ │ └─────────────────────┘ └─────────────────────────┘ │ │
│ │ [+ Add Category]                                    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ 🎁 DISCRETIONARY EXPENSES (Wants)                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Amount: $38.22                                      │ │
│ │ ┌─────────────────────┐ ┌─────────────────────────┐ │ │
│ │ │ groceries/discretion│ │ $38.22                  │ │ │
│ │ │ ▼                   │ │                         │ │ │
│ │ └─────────────────────┘ └─────────────────────────┘ │ │
│ │ [+ Add Category]                                    │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Total Allocated: $127.45 ✓                             │
│ Remaining: $0.00                                        │
│                                                         │
│ [Cancel]                                    [Save Split] │
└─────────────────────────────────────────────────────────┘
```

#### Interaction Features
- **Drag and Drop**: Drag amount sliders to adjust allocation
- **Smart Suggestions**: AI suggests common splits based on merchant
- **Quick Presets**: One-click common split ratios (70/30, 80/20, etc.)
- **Category Autocomplete**: Type-ahead for category selection
- **Running Total**: Real-time validation that split equals original amount

### 2. QuickSplitPresets

#### Component Purpose
One-click preset splits for common merchant types based on learned patterns.

#### Visual Layout
```
┌─────────────────────────────────────────────────────────┐
│ Quick Split Suggestions                                 │
├─────────────────────────────────────────────────────────┤
│ 🎯 Common for Walmart:                                  │
│                                                         │
│ [70% Fixed / 30% Discretionary]  [60% Fixed / 40% Disc] │
│                                                         │
│ [80% Fixed / 20% Discretionary]  [Custom Split ⚙️]      │
│                                                         │
│ 💡 Based on your spending patterns                      │
└─────────────────────────────────────────────────────────┘
```

### 3. TransactionCategorizationRow

#### Component Purpose
Enhanced transaction list item showing dual categorization with quick actions.

#### Visual Layout for Uncategorized Transaction
```
┌─────────────────────────────────────────────────────────┐
│ 🏪 Amazon.com                                   $45.67  │
│ Jan 16, 2025 • shopping                                 │
│ ⚠️ Needs categorization                                  │
│                                                         │
│ [🏠 Fixed] [🎁 Discretionary] [⚡ Split] [🤖 Auto]       │
└─────────────────────────────────────────────────────────┘
```

#### Visual Layout for Categorized Transaction
```
┌─────────────────────────────────────────────────────────┐
│ 🏪 Kroger                                       $67.89  │
│ Jan 16, 2025                                            │
│ 📊 groceries/fixed: $45.20 • groceries/discretionary: $22.69 │
│                                                         │
│ [✏️ Edit Split]                                          │
└─────────────────────────────────────────────────────────┘
```

### 4. StewardshipGuidancePanel

#### Component Purpose
Contextual guidance helping users understand fixed vs. discretionary decisions based on biblical principles.

#### Visual Layout
```
┌─────────────────────────────────────────────────────────┐
│ 💡 Stewardship Guidance                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 🏠 FIXED (Needs): Essential for basic living            │
│ • Basic groceries (eggs, milk, bread)                  │
│ • Household necessities (cleaning supplies)            │
│ • Health and medical items                             │
│                                                         │
│ 🎁 DISCRETIONARY (Wants): Enhance lifestyle            │
│ • Treats and snacks                                    │
│ • Premium brands                                        │
│ • Convenience items                                     │
│                                                         │
│ 📖 "But seek first his kingdom and his righteousness,  │
│    and all these things will be given to you as well." │
│    - Matthew 6:33                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Persona-Specific UI Adaptations

### Pre-Teen (8-14 years) - Simple Toggle Interface
```
┌─────────────────────────────────────────────────────────┐
│ 🏪 Target                                       $25.00  │
│ Your allowance purchase                                 │
│                                                         │
│ Is this something you NEED or WANT?                     │
│                                                         │
│ ┌─────────────────────┐    ┌─────────────────────────┐  │
│ │   🏠 NEED           │    │   🎁 WANT               │  │
│ │   (like food,       │    │   (like toys,           │  │
│ │    school supplies) │    │    games, treats)       │  │
│ │                     │    │                         │  │
│ │   [SELECT]          │    │   [SELECT]              │  │
│ └─────────────────────┘    └─────────────────────────┘  │
│                                                         │
│ 💡 Remember: Needs first, wants second!                 │
└─────────────────────────────────────────────────────────┘
```

### Teen (15-17 years) - Educational Interface
```
┌─────────────────────────────────────────────────────────┐
│ 🏪 Best Buy                                     $89.99  │
│ electronics • Jan 16, 2025                              │
│                                                         │
│ What type of expense is this?                           │
│                                                         │
│ 🔘 Fixed (Need) - Required for school or work          │
│ 🔘 Discretionary (Want) - Nice to have but not essential│
│ 🔘 Split - Part need, part want                        │
│                                                         │
│ 💭 Think about it: Is this item necessary for your     │
│    education or required activities? Or is it an       │
│    upgrade/entertainment purchase?                      │
│                                                         │
│ [Categorize] [Need Help?]                              │
└─────────────────────────────────────────────────────────┘
```

### Single Parent - Priority Alert Interface
```
┌─────────────────────────────────────────────────────────┐
│ 🏪 Target                                      $156.78  │
│ groceries • Jan 16, 2025                               │
│                                                         │
│ ⚡ Quick Categorization for Busy Parents                │
│                                                         │
│ 🎯 Smart Suggestion: 75% Fixed / 25% Discretionary     │
│ Based on your family's typical grocery patterns        │
│                                                         │
│ Family Fixed (Needs): $117.59                          │
│ • Basic groceries, household essentials                │
│                                                         │
│ Family Discretionary (Wants): $39.19                   │
│ • Treats, convenience items                            │
│                                                         │
│ [✓ Accept] [✏️ Adjust] [⚡ Save as Default]             │
│                                                         │
│ ⏱️ Categorized in 10 seconds!                           │
└─────────────────────────────────────────────────────────┘
```

### Fixed-Income - Simplified Healthcare Focus
```
┌─────────────────────────────────────────────────────────┐
│ 🏥 CVS Pharmacy                                 $47.83  │
│ health • Jan 16, 2025                                  │
│                                                         │
│ Healthcare Expense Type:                                │
│                                                         │
│ ┌─────────────────────┐    ┌─────────────────────────┐  │
│ │ 💊 ESSENTIAL        │    │ 🎁 OPTIONAL             │  │
│ │ Prescriptions       │    │ Vitamins, supplements   │  │
│ │ Medical supplies    │    │ Comfort items           │  │
│ │                     │    │                         │  │
│ │ [SELECT]            │    │ [SELECT]                │  │
│ └─────────────────────┘    └─────────────────────────┘  │
│                                                         │
│ 📋 Medicare/Insurance may cover essential items         │
└─────────────────────────────────────────────────────────┘
```

---

## Machine Learning Integration

### Smart Categorization Suggestions

#### Learning Algorithm Inputs
1. **Historical Patterns**: User's past categorization decisions
2. **Merchant Data**: Store type and typical purchase patterns
3. **Transaction Amount**: Large vs. small purchase implications
4. **Timing**: Day of week, season, holidays
5. **Persona Profile**: Age group and life stage tendencies
6. **Family Context**: Single vs. family purchases

#### Suggestion Confidence Levels
```
High Confidence (90%+): Auto-categorize with user review
Medium Confidence (70-89%): Suggest with explanation
Low Confidence (<70%): Present options with guidance
```

### Learning Feedback Loop

#### User Correction Learning
```
When user overrides suggestion:
1. Record override decision
2. Update merchant pattern weights
3. Adjust persona-specific tendencies
4. Improve future suggestions for similar transactions
```

#### Pattern Recognition Examples
- Amazon purchases on Sundays: 60% household/fixed, 40% shopping/discretionary
- Grocery store visits before holidays: 50% fixed, 50% discretionary
- Pharmacy visits by seniors: 90% health/fixed, 10% health/discretionary
- Teen clothing purchases: 30% clothing/fixed, 70% clothing/discretionary

---

## Error Handling and Validation

### Split Amount Validation
```javascript
validateSplit(originalAmount, allocatedAmounts) {
  const total = allocatedAmounts.reduce((sum, amount) => sum + amount, 0);
  
  if (total !== originalAmount) {
    return {
      valid: false,
      error: `Total allocated ($${total}) must equal original amount ($${originalAmount})`,
      difference: Math.abs(total - originalAmount)
    };
  }
  
  return { valid: true };
}
```

### Category Validation
- Ensure each split has a valid Plaid category
- Validate fixed/discretionary selection
- Check for minimum allocation amounts ($0.01)
- Prevent duplicate category combinations

### User Experience Enhancements
- **Auto-correction**: Suggest corrections for common input errors
- **Keyboard shortcuts**: Quick categorization with hotkeys
- **Undo functionality**: Easy reversal of categorization decisions
- **Bulk operations**: Categorize multiple similar transactions at once

---

## Performance Considerations

### Lazy Loading
- Load transaction history in chunks (50 transactions per page)
- Cache categorization suggestions for common merchants
- Preload next batch while user reviews current transactions

### Offline Support
- Cache uncategorized transactions for offline review
- Queue categorization decisions for sync when online
- Show clear indicators for offline mode limitations

### Mobile Optimization
- Touch-friendly buttons (minimum 44px target size)
- Swipe gestures for quick categorization
- Haptic feedback for successful categorizations
- Voice-to-text for category notes

---

## Accessibility Features

### Screen Reader Support
- Semantic HTML structure for transaction lists
- ARIA labels for categorization buttons
- Live regions for dynamic content updates
- Keyboard navigation for all interactive elements

### Visual Accessibility
- High contrast mode for categorization indicators
- Large text options for amount displays
- Color-blind friendly category indicators
- Reduced motion options for animations

### Motor Accessibility
- Large touch targets for mobile interfaces
- Keyboard alternatives for all mouse interactions
- Voice control integration where available
- Switch navigation support

This comprehensive UI specification ensures that the dual categorization system is user-friendly, persona-appropriate, and maintains the biblical stewardship principles while providing the technical sophistication needed for accurate financial tracking.