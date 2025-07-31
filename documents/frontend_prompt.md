# Advanced React Web Application Development Prompt

You are tasked with creating a cutting-edge, immersive web application using React, TypeScript, and modern UI libraries. The application should feature sophisticated interactivity, advanced visual effects, and professional-grade architecture that can be adapted to any use case (blog, news magazine, portfolio, dashboard, etc.).

## Technology Stack Constraints

**Required Stack:**
- **Frontend Framework:** React 18.3+ with TypeScript
- **Build Tool:** Vite 5.4+
- **Styling:** Tailwind CSS 3.4+ with CSS Variables
- **UI Components:** Shadcn/ui with Radix UI primitives
- **Icons:** Lucide React
- **Routing:** React Router DOM 6.26+
- **State Management:** React Context + React Query
- **Form Handling:** React Hook Form with Zod validation
- **Animations:** Tailwind CSS animations + custom keyframes

**Prohibited Technologies:**
- No Next.js, Angular, Vue, Svelte, or other frameworks
- No backend code (Node.js, Python, Ruby, etc.)
- No server-side components
- No native mobile development

## Required Dependencies (Exact Versions)

```json
{
  "dependencies": {
    "@hookform/resolvers": "^3.9.0",
    "@radix-ui/react-accordion": "^1.2.0",
    "@radix-ui/react-alert-dialog": "^1.1.1",
    "@radix-ui/react-aspect-ratio": "^1.1.0",
    "@radix-ui/react-avatar": "^1.1.0",
    "@radix-ui/react-checkbox": "^1.1.1",
    "@radix-ui/react-collapsible": "^1.1.0",
    "@radix-ui/react-context-menu": "^2.2.1",
    "@radix-ui/react-dialog": "^1.1.2",
    "@radix-ui/react-dropdown-menu": "^2.1.1",
    "@radix-ui/react-hover-card": "^1.1.1",
    "@radix-ui/react-label": "^2.1.0",
    "@radix-ui/react-menubar": "^1.1.1",
    "@radix-ui/react-navigation-menu": "^1.2.0",
    "@radix-ui/react-popover": "^1.1.1",
    "@radix-ui/react-progress": "^1.1.0",
    "@radix-ui/react-radio-group": "^1.2.0",
    "@radix-ui/react-scroll-area": "^1.1.0",
    "@radix-ui/react-select": "^2.1.1",
    "@radix-ui/react-separator": "^1.1.0",
    "@radix-ui/react-slider": "^1.2.0",
    "@radix-ui/react-slot": "^1.1.0",
    "@radix-ui/react-switch": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toast": "^1.2.1",
    "@radix-ui/react-toggle": "^1.1.0",
    "@radix-ui/react-toggle-group": "^1.1.0",
    "@radix-ui/react-tooltip": "^1.1.4",
    "@tanstack/react-query": "^5.56.2",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.0.0",
    "date-fns": "^3.6.0",
    "embla-carousel-react": "^8.3.0",
    "input-otp": "^1.2.4",
    "lucide-react": "^0.462.0",
    "next-themes": "^0.3.0",
    "react": "^18.3.1",
    "react-day-picker": "^8.10.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.53.0",
    "react-resizable-panels": "^2.1.3",
    "react-router-dom": "^6.26.2",
    "recharts": "^2.12.7",
    "sonner": "^1.5.0",
    "tailwind-merge": "^2.5.2",
    "tailwindcss-animate": "^1.0.7",
    "vaul": "^0.9.3",
    "zod": "^3.23.8"
  }
}
```

## Project Structure & File Constraints

### Required Directory Structure:
```
project-root/
├── public/
│   ├── favicon.ico
│   ├── placeholder.svg
│   └── robots.txt
├── src/
│   ├── components/
│   │   ├── ui/           # Shadcn/ui components (auto-generated)
│   │   └── [custom]/     # Your custom components
│   ├── contexts/         # React Context providers
│   ├── hooks/           # Custom React hooks
│   ├── lib/
│   │   └── utils.ts     # Utility functions
│   ├── pages/           # Route components
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   ├── index.css        # Global styles
│   └── vite-env.d.ts    # Vite type definitions
├── components.json       # Shadcn/ui configuration
├── package.json
├── tailwind.config.ts
├── vite.config.ts
├── tsconfig.json
└── README.md
```

### File Modification Constraints:

**DO NOT MODIFY these auto-generated/configuration files:**
- `components.json`
- `vite.config.ts` (except for basic plugin additions)
- `tsconfig.json`
- `package.json` (dependencies are pre-defined)
- Any files in `src/components/ui/` (these are Shadcn/ui components)

**REQUIRED configuration files to create:**

**tailwind.config.ts:**
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "scale-in": {
          "0%": { transform: "scale(0.95)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.3s ease-out",
        "scale-in": "scale-in 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

**src/lib/utils.ts:**
```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

## Component Architecture Requirements

### 1. Main Layout Structure
- **App.tsx**: Router setup with QueryClient and providers
- **Main Layout Component**: Primary page structure with responsive design
- **Navigation Component**: Sophisticated menu system with collapse/expand states
- **Content Area**: Dynamic content region that adapts to layout changes

### 2. Context Providers (Required)
Create React Context providers for:
- **Settings/Theme Management**: Global app configuration
- **Layout State**: Menu collapse, sidebar states, responsive behavior
- **Data Management**: Mock data or API state management

### 3. Custom Components
Build sophisticated, reusable components:
- **Interactive Cards**: Hover effects, animations, dynamic content
- **Advanced Forms**: Multi-step, validation, real-time feedback
- **Data Visualization**: Charts, progress indicators, interactive elements
- **Modal/Dialog Systems**: Layered interactions, animations
- **Navigation Elements**: Breadcrumbs, pagination, search

## Advanced Styling Requirements

### 1. CSS Variables System (src/index.css)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Core colors */
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 84% 4.9%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
    --radius: 0.75rem;
  }
}
```

### 2. Advanced Visual Effects
Implement sophisticated visual elements:
- **Glass Morphism**: Backdrop blur, transparency, borders
- **Interactive Hover States**: Scale, glow, color transitions
- **Animated Backgrounds**: Gradients, particles, patterns
- **Advanced Shadows**: Multi-layered, colored, dynamic
- **Smooth Transitions**: Page changes, state updates, interactions

### 3. Custom Component Classes
```css
@layer components {
  .glass-panel {
    @apply bg-background/80 backdrop-blur-xl border border-border/50;
  }
  
  .interactive-card {
    @apply transition-all duration-300 hover:scale-105 hover:shadow-xl;
  }
  
  .glow-effect {
    @apply shadow-lg shadow-primary/25;
  }
}
```

## Layout & Responsive Design

### 1. Flexible Layout System
- **Mobile-First**: Responsive breakpoints (sm, md, lg, xl, 2xl)
- **Adaptive Navigation**: Collapsible menus, mobile-optimized interactions
- **Content Flow**: Proper spacing, typography scales, visual hierarchy
- **Cross-Device**: Touch-friendly interactions, keyboard navigation

### 2. Layout Patterns
- **Sidebar Layout**: Collapsible navigation with content adaptation
- **Grid Systems**: CSS Grid and Flexbox for complex layouts
- **Card-Based Design**: Flexible content containers with consistent spacing
- **Modal Layering**: Proper z-index management, backdrop handling

## Functional Requirements

### 1. State Management
- **Global State**: React Context for shared data
- **Local State**: Component-level state management
- **Form State**: React Hook Form with validation
- **API State**: React Query for data fetching (mock data acceptable)

### 2. Interactive Features
- **Real-time Updates**: Periodic data refresh, live status indicators
- **User Preferences**: Persistent settings, theme switching
- **Advanced Filtering**: Search, sort, category filtering
- **Dynamic Content**: Conditional rendering, progressive loading

### 3. User Experience
- **Loading States**: Skeletons, spinners, progressive enhancement
- **Error Handling**: User-friendly error messages, retry mechanisms
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support
- **Performance**: Optimized rendering, lazy loading, efficient updates

## Development Standards

### 1. Code Quality
- **TypeScript**: Strict typing, interface definitions, type safety
- **Component Structure**: Functional components, custom hooks, clean architecture
- **Error Boundaries**: Graceful error handling and recovery
- **Code Organization**: Logical file structure, clear naming conventions

### 2. Best Practices
- **Accessibility**: WCAG compliance, semantic HTML, proper ARIA usage
- **Performance**: React optimizations, efficient re-renders, bundle size
- **Maintainability**: Modular code, reusable components, clear documentation
- **Testing**: Component testing, user interaction testing

## Critical Constraints

### 1. Technology Limitations
- **Frontend Only**: No backend code, no server-side logic
- **Pure React**: No framework mixing, stick to React ecosystem
- **Vite Build**: Use Vite-specific features and optimizations
- **TypeScript Required**: All code must be properly typed

### 2. File Management
- **No Config Changes**: Don't modify build tools, package.json dependencies
- **Shadcn/ui Integrity**: Don't edit ui components, use composition instead
- **Path Aliases**: Use @/ for src imports consistently

### 3. Design Philosophy
- **Modern Aesthetics**: Contemporary design language, professional appearance
- **Immersive Experience**: Engaging interactions, smooth animations
- **Scalable Architecture**: Code that can grow and adapt to different use cases
- **Production Ready**: Code quality suitable for real-world deployment

## Success Criteria

The final application should demonstrate:
1. **Professional Grade UI**: Polished, modern interface with sophisticated interactions
2. **Responsive Excellence**: Flawless experience across all device sizes
3. **Advanced Interactivity**: Rich user interactions, smooth animations, engaging UX
4. **Clean Architecture**: Well-organized, maintainable, scalable codebase
5. **Performance Optimized**: Fast loading, smooth interactions, efficient rendering
6. **Accessibility Compliant**: Usable by everyone, keyboard navigable, screen reader friendly

Create an application that showcases the full potential of modern React development while maintaining the sophistication and immersive quality that makes users want to interact with and explore the interface.