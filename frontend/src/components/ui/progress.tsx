import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const progressVariants = cva(
  "relative h-4 w-full overflow-hidden rounded-full bg-secondary",
  {
    variants: {
      variant: {
        default: "",
        faithful: "bg-faithful-100",
        stewardship: "bg-stewardship-100", 
        blessing: "bg-blessing-100",
        // Budget status variants
        under: "bg-green-100",
        "on-track": "bg-blue-100",
        warning: "bg-yellow-100",
        over: "bg-red-100",
      },
      size: {
        default: "h-4",
        sm: "h-2",
        lg: "h-6",
        xl: "h-8",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const progressIndicatorVariants = cva(
  "h-full w-full flex-1 bg-primary transition-all duration-300 ease-in-out",
  {
    variants: {
      variant: {
        default: "bg-primary",
        faithful: "bg-faithful-600",
        stewardship: "bg-stewardship-600",
        blessing: "bg-blessing-600",
        // Budget status variants
        under: "bg-green-600",
        "on-track": "bg-blue-600", 
        warning: "bg-yellow-600",
        over: "bg-red-600",
      }
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface ProgressProps
  extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>,
    VariantProps<typeof progressVariants> {
  value?: number
  max?: number
  showValue?: boolean
  showLabel?: boolean
  label?: string
  formatValue?: (value: number, max: number) => string
}

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  ProgressProps
>(({ 
  className, 
  value = 0, 
  max = 100,
  variant,
  size,
  showValue = false,
  showLabel = false,
  label,
  formatValue,
  ...props 
}, ref) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
  
  const defaultFormatValue = (val: number, maxVal: number) => 
    `${Math.round((val / maxVal) * 100)}%`
  
  const formattedValue = formatValue 
    ? formatValue(value, max)
    : defaultFormatValue(value, max)

  return (
    <div className="w-full">
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          {label && (
            <span className="text-sm font-medium text-foreground">
              {label}
            </span>
          )}
          {showValue && (
            <span className="text-sm text-muted-foreground">
              {formattedValue}
            </span>
          )}
        </div>
      )}
      
      <ProgressPrimitive.Root
        ref={ref}
        className={cn(progressVariants({ variant, size }), className)}
        value={percentage}
        max={100}
        {...props}
      >
        <ProgressPrimitive.Indicator
          className={cn(progressIndicatorVariants({ variant }))}
          style={{ transform: `translateX(-${100 - percentage}%)` }}
        />
      </ProgressPrimitive.Root>
      
      {/* Screen reader announcement */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {label && `${label}: `}{formattedValue}
      </div>
    </div>
  )
})
Progress.displayName = ProgressPrimitive.Root.displayName

// Specialized progress components for financial contexts
export interface BudgetProgressProps extends Omit<ProgressProps, 'variant'> {
  spent: number
  budget: number
  status?: 'under' | 'on-track' | 'warning' | 'over'
}

const BudgetProgress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  BudgetProgressProps
>(({ spent, budget, status, formatValue, ...props }, ref) => {
  // Auto-determine status if not provided
  const percentage = (spent / budget) * 100
  const autoStatus = !status
    ? percentage <= 50 ? 'under'
      : percentage <= 85 ? 'on-track'
      : percentage <= 100 ? 'warning'
      : 'over'
    : status

  const defaultBudgetFormatter = (val: number, maxVal: number) => 
    `$${val.toFixed(0)} of $${maxVal.toFixed(0)}`

  return (
    <Progress
      ref={ref}
      value={spent}
      max={budget}
      variant={autoStatus}
      formatValue={formatValue || defaultBudgetFormatter}
      {...props}
    />
  )
})
BudgetProgress.displayName = "BudgetProgress"

export interface SavingsProgressProps extends Omit<ProgressProps, 'variant'> {
  current: number
  target: number
  showRemaining?: boolean
}

const SavingsProgress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  SavingsProgressProps
>(({ current, target, showRemaining = false, formatValue, ...props }, ref) => {
  const remaining = target - current
  
  const defaultSavingsFormatter = (val: number, maxVal: number) => {
    if (showRemaining) {
      return `$${(maxVal - val).toFixed(0)} remaining`
    }
    return `$${val.toFixed(0)} of $${maxVal.toFixed(0)}`
  }

  return (
    <Progress
      ref={ref}
      value={current}
      max={target}
      variant="blessing"
      formatValue={formatValue || defaultSavingsFormatter}
      {...props}
    />
  )
})
SavingsProgress.displayName = "SavingsProgress"

export { Progress, BudgetProgress, SavingsProgress, progressVariants }