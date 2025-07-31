# Faithful Finances Frontend

A React-based web application for biblical stewardship and personal finance management, supporting 8 distinct personas with tailored financial guidance.

## 🚀 Features

### Core Functionality
- **Persona-Based Experience**: 8 unique user personas with tailored interfaces and workflows
- **Biblical Stewardship**: Tithing calculation and tracking with faith-based principles
- **Dual Categorization**: Transaction classification as needs vs wants
- **Plaid Integration**: Automatic bank account connection and transaction import
- **Family Management**: Multi-user coordination with permissions and oversight
- **Emergency Fund Tracking**: Persona-specific savings goals and progress monitoring

### Supported Personas
1. **Pre-Teen (8-14)**: Colorful, gamified interface with parental controls
2. **Teen (15-17)**: Independence building with oversight features
3. **College Student (18-22)**: Irregular income and semester-based budgeting
4. **Single Adult (25-40)**: Professional financial management
5. **Married Couple (25-65)**: Joint financial coordination
6. **Single Parent (25-45)**: Family-focused expense prioritization
7. **Two Parent Family (30-50)**: Dual-income family management
8. **Fixed Income (55+)**: Retirement and healthcare expense focus

## 🛠 Technology Stack

- **Framework**: React 18.3+ with TypeScript
- **Build Tool**: Vite 5.4+
- **Styling**: Tailwind CSS 3.4+ with CSS Variables
- **UI Components**: Shadcn/ui with Radix UI primitives
- **Icons**: Lucide React
- **Routing**: React Router DOM 6.26+
- **State Management**: React Context + React Query
- **Form Handling**: React Hook Form with Zod validation
- **Animations**: Tailwind CSS animations + custom keyframes

## 📁 Project Structure

```
src/
├── components/
│   ├── ui/           # Shadcn/ui components
│   ├── layout/       # Layout components (Header, Sidebar, etc.)
│   ├── auth/         # Authentication components
│   ├── dashboard/    # Dashboard-specific components
│   └── financial/    # Financial feature components
├── contexts/         # React Context providers
├── hooks/           # Custom React hooks
├── lib/
│   ├── api.ts       # API client and React Query setup
│   └── utils.ts     # Utility functions
├── pages/           # Route components
│   ├── auth/        # Authentication pages
│   ├── dashboard/   # Dashboard pages
│   │   └── personas/ # Persona-specific dashboards
│   ├── family/      # Family management
│   └── settings/    # User settings
├── types/           # TypeScript type definitions
├── App.tsx          # Main app component
└── main.tsx         # Entry point
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18.0 or higher
- npm or yarn package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd faithful-finances-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run typecheck` - Run TypeScript type checking

## 🎨 Design System

### Theme Configuration
The application uses a sophisticated theme system with CSS variables for consistent styling across all personas while allowing for persona-specific customizations.

### Color Palette
- **Primary**: Biblical-inspired blues and purples
- **Secondary**: Warm grays and off-whites
- **Success**: Forest greens for positive financial actions
- **Warning**: Amber for alerts and cautions
- **Error**: Muted reds for validation and errors

### Typography
- **Headings**: Bold, modern sans-serif
- **Body**: Readable sans-serif with proper line spacing
- **UI Elements**: Consistent sizing and spacing scale

## 🔐 Authentication & Security

- **Auth0 Integration**: Secure authentication with JWT tokens
- **Role-Based Access**: Persona and family role-based route protection
- **API Security**: Bearer token authentication for all API calls
- **Privacy Controls**: Granular permissions for family sharing

## 📱 Responsive Design

- **Mobile-First**: Optimized for smartphones and tablets
- **Breakpoints**: 
  - `sm`: 640px+
  - `md`: 768px+
  - `lg`: 1024px+
  - `xl`: 1280px+
  - `2xl`: 1536px+

## 🧪 Testing & Quality

- **TypeScript**: Strict type checking enabled
- **ESLint**: Code quality and consistency
- **Prettier**: Code formatting (recommended)
- **Accessibility**: WCAG 2.1 AA compliance target

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

The build output will be in the `dist/` directory, ready for deployment to any static hosting service.

### Environment Variables for Production
- `VITE_API_URL`: Backend API endpoint
- `VITE_AUTH0_DOMAIN`: Auth0 domain
- `VITE_AUTH0_CLIENT_ID`: Auth0 client ID
- `VITE_AUTH0_AUDIENCE`: Auth0 API audience

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 API Integration

The frontend integrates with the Faithful Finances REST API for:
- User authentication and profile management
- Plaid bank account connections
- Transaction data synchronization
- Budget and goal management
- Family coordination features
- Tithing calculation and tracking

See the OpenAPI specification in `/contracts/openapi-contract.json` for complete API documentation.

## 🎯 Persona-Specific Features

### Pre-Teen Dashboard
- Large, colorful buttons and icons
- Gamified progress tracking with badges
- Parent approval workflows
- Educational content with biblical principles

### Teen Dashboard
- Modern, appealing interface
- Part-time job income tracking
- Budget learning tools
- Parental oversight toggle

### College Student Dashboard
- Semester-based budgeting
- Financial aid integration
- Emergency fund focus
- Study-friendly scheduling

### Adult Dashboards
- Professional interfaces
- Comprehensive financial analytics
- Investment tracking
- Advanced goal setting

### Family Dashboards
- Multi-user coordination
- Child expense prioritization
- Shared goal management
- Communication tools

### Fixed Income Dashboard
- Large fonts and high contrast
- Healthcare expense focus
- Simplified navigation
- Voice-friendly features

## 📖 Biblical Integration

The application incorporates biblical stewardship principles throughout:
- **Tithing Priority**: 10% calculation on gross income
- **Needs vs Wants**: Classification based on biblical wisdom
- **Scripture Integration**: Relevant verses and encouragement
- **Faithful Giving**: Tracking and celebrating generosity
- **Stewardship Education**: Age-appropriate biblical financial principles

## 🔮 Future Enhancements

- Progressive Web App (PWA) capabilities
- Advanced analytics and reporting
- Investment portfolio tracking
- Church giving integration
- Financial education modules
- Multi-language support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with faith-based principles for biblical stewardship
- Designed to serve families across all life stages
- Inspired by Matthew 6:21: "For where your treasure is, there your heart will be also."