import { rest } from 'msw';

// Mock API responses for testing
export const handlers = [
  // Budget API endpoints
  rest.get('/api/budgets', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        categories: [
          {
            id: 'category-1',
            name: 'Housing',
            budgetedAmount: 1500,
            spentAmount: 1200,
            period: 'monthly',
            startDate: '2024-01-01T00:00:00.000Z',
            endDate: '2024-01-31T23:59:59.999Z',
            color: '#3B82F6',
            isActive: true,
            tags: ['essential', 'fixed'],
            priority: 'high',
            rollover: false,
            alerts: {
              at50Percent: false,
              at75Percent: true,
              at90Percent: true,
              at100Percent: true,
              customAlerts: []
            }
          },
          {
            id: 'category-2',
            name: 'Food & Dining',
            budgetedAmount: 600,
            spentAmount: 450,
            period: 'monthly',
            startDate: '2024-01-01T00:00:00.000Z',
            endDate: '2024-01-31T23:59:59.999Z',
            color: '#10B981',
            isActive: true,
            tags: ['essential', 'variable'],
            priority: 'high',
            rollover: false,
            alerts: {
              at50Percent: false,
              at75Percent: true,
              at90Percent: true,
              at100Percent: true,
              customAlerts: []
            }
          }
        ]
      })
    );
  }),

  rest.post('/api/budgets/categories', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 'category-new',
        ...req.body,
        createdAt: new Date().toISOString()
      })
    );
  }),

  rest.put('/api/budgets/categories/:id', (req, res, ctx) => {
    const { id } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        id,
        ...req.body,
        updatedAt: new Date().toISOString()
      })
    );
  }),

  rest.delete('/api/budgets/categories/:id', (req, res, ctx) => {
    return res(ctx.status(204));
  }),

  // Transaction API endpoints
  rest.get('/api/transactions', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        transactions: [
          {
            id: 'transaction-1',
            amount: 50.00,
            description: 'Grocery shopping',
            categoryId: 'category-2',
            date: new Date().toISOString(),
            tags: ['groceries', 'essentials'],
            status: 'completed'
          },
          {
            id: 'transaction-2',
            amount: 25.99,
            description: 'Gas station',
            categoryId: 'category-3',
            date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
            tags: ['fuel', 'transportation'],
            status: 'completed'
          }
        ]
      })
    );
  }),

  rest.post('/api/transactions', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 'transaction-new',
        ...req.body,
        createdAt: new Date().toISOString(),
        status: 'completed'
      })
    );
  }),

  // Family API endpoints
  rest.get('/api/family/members', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        members: [
          {
            id: 'member-1',
            name: 'Parent User',
            email: 'parent@example.com',
            role: 'parent',
            age: 35,
            permissions: {
              canViewFamilyFinances: true,
              canMakeTransactions: true,
              canViewOwnTransactions: true,
              canSetSavingsGoals: true,
              canReceiveAllowance: false,
              canGiveTithe: true,
              maxTransactionAmount: 10000,
              requiresParentalApproval: false,
              canInviteMembers: true,
              canManageFamily: true,
              canViewReports: true,
              canExportData: true
            },
            savings: {
              balance: 0,
              goals: []
            }
          },
          {
            id: 'member-2',
            name: 'Teen Child',
            email: 'teen@example.com',
            role: 'teen',
            age: 16,
            permissions: {
              canViewFamilyFinances: true,
              canMakeTransactions: true,
              canViewOwnTransactions: true,
              canSetSavingsGoals: true,
              canReceiveAllowance: true,
              canGiveTithe: true,
              maxTransactionAmount: 200,
              requiresParentalApproval: true,
              canInviteMembers: false,
              canManageFamily: false,
              canViewReports: false,
              canExportData: false
            },
            allowance: {
              amount: 50,
              frequency: 'weekly',
              nextDue: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
            },
            savings: {
              balance: 125,
              goals: []
            }
          }
        ]
      })
    );
  }),

  rest.post('/api/family/members', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 'member-new',
        ...req.body,
        createdAt: new Date().toISOString()
      })
    );
  }),

  rest.post('/api/family/transactions/approve', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        transactionId: req.body.transactionId,
        status: 'approved',
        approvedBy: req.body.approverId,
        approvedAt: new Date().toISOString()
      })
    );
  }),

  // Tithing API endpoints
  rest.get('/api/tithing/records', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        records: [
          {
            id: 'tithe-1',
            amount: 500,
            date: new Date().toISOString(),
            source: 'salary',
            paymentMethod: 'check',
            churchId: 'church-1',
            status: 'completed',
            taxDeductible: true
          },
          {
            id: 'tithe-2',
            amount: 100,
            date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
            source: 'bonus',
            paymentMethod: 'online',
            churchId: 'church-1',
            status: 'completed',
            taxDeductible: true
          }
        ]
      })
    );
  }),

  rest.post('/api/tithing/records', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 'tithe-new',
        ...req.body,
        createdAt: new Date().toISOString(),
        status: 'completed'
      })
    );
  }),

  rest.get('/api/tithing/churches', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        churches: [
          {
            id: 'church-1',
            name: 'Community Church',
            address: '123 Church St, City, State 12345',
            pastor: 'Pastor Smith',
            denomination: 'Non-denominational',
            isActive: true,
            onlineGiving: {
              enabled: true,
              url: 'https://church.com/give',
              methods: ['credit_card', 'bank_transfer']
            }
          }
        ]
      })
    );
  }),

  // Reports API endpoints
  rest.get('/api/reports/budget/:period', (req, res, ctx) => {
    const { period } = req.params;
    return res(
      ctx.status(200),
      ctx.json({
        period,
        totalBudgeted: 3500,
        totalSpent: 2850,
        variance: 650,
        categories: [
          {
            categoryId: 'category-1',
            name: 'Housing',
            budgeted: 1500,
            spent: 1200,
            variance: 300,
            percentage: 80
          },
          {
            categoryId: 'category-2',
            name: 'Food & Dining',
            budgeted: 600,
            spent: 450,
            variance: 150,
            percentage: 75
          }
        ],
        insights: [
          'You are spending 15% less on entertainment compared to last month',
          'Food expenses are trending upward this quarter'
        ],
        recommendations: [
          'Consider increasing your emergency fund allocation',
          'Review subscription services in entertainment category'
        ]
      })
    );
  }),

  // Error scenarios for testing
  rest.post('/api/budgets/categories/error', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({
        error: 'Internal server error',
        message: 'Failed to create budget category'
      })
    );
  }),

  rest.get('/api/network-error', (req, res, ctx) => {
    return res.networkError('Network connection failed');
  }),

  // Auth0 mock endpoints
  rest.get('/.well-known/jwks.json', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        keys: [
          {
            kty: 'RSA',
            use: 'sig',
            kid: 'test-key-id',
            n: 'test-n-value',
            e: 'AQAB'
          }
        ]
      })
    );
  }),

  // Plaid mock endpoints (if needed)
  rest.post('/api/plaid/link_token', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        link_token: 'link-test-token-123',
        expiration: new Date(Date.now() + 30 * 60 * 1000).toISOString()
      })
    );
  }),

  rest.post('/api/plaid/exchange_public_token', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        access_token: 'access-test-token-123',
        item_id: 'item-test-id-123'
      })
    );
  })
];

// Helper function to create error handlers for testing
export const createErrorHandler = (endpoint: string, status: number, message: string) => {
  return rest.get(endpoint, (req, res, ctx) => {
    return res(
      ctx.status(status),
      ctx.json({
        error: 'Test error',
        message
      })
    );
  });
};

// Helper function to create delayed response handlers
export const createDelayedHandler = (endpoint: string, delay: number) => {
  return rest.get(endpoint, (req, res, ctx) => {
    return res(
      ctx.delay(delay),
      ctx.status(200),
      ctx.json({ message: 'Delayed response' })
    );
  });
};