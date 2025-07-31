import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Performance utilities
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

// Memory-efficient formatters with memoization
const formatCache = new Map();

export const formatCurrency = (amount: number, currency = 'USD'): string => {
  const key = `${amount}-${currency}`;
  if (formatCache.has(key)) {
    return formatCache.get(key);
  }
  
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
  
  // Keep cache size reasonable
  if (formatCache.size > 100) {
    const firstKey = formatCache.keys().next().value;
    formatCache.delete(firstKey);
  }
  
  formatCache.set(key, formatted);
  return formatted;
};

export const formatPercentage = (value: number): string => {
  const key = `pct-${value}`;
  if (formatCache.has(key)) {
    return formatCache.get(key);
  }
  
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);
  
  if (formatCache.size > 100) {
    const firstKey = formatCache.keys().next().value;
    formatCache.delete(firstKey);
  }
  
  formatCache.set(key, formatted);
  return formatted;
};

// Lazy loading utilities
export const createLazyComponent = <T extends React.ComponentType<any>>(
  importFunc: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) => {
  return React.lazy(() => importFunc());
};

// Virtual scrolling utilities
export const getVisibleRange = (
  scrollTop: number,
  containerHeight: number,
  itemHeight: number,
  totalItems: number,
  overscan = 5
) => {
  const start = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const end = Math.min(totalItems, start + visibleCount + overscan * 2);
  
  return { start, end };
};

// Image optimization utilities
export const getOptimizedImageUrl = (
  url: string,
  width?: number,
  quality = 80
): string => {
  if (!url) return '';
  
  // Add optimization parameters for supported services
  const urlObj = new URL(url);
  if (width) urlObj.searchParams.set('w', width.toString());
  urlObj.searchParams.set('q', quality.toString());
  
  return urlObj.toString();
};

// Bundle size optimization
export const preloadRoute = (routeComponent: () => Promise<any>) => {
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.as = 'script';
  // This would be dynamically set based on the route
  document.head.appendChild(link);
};

import React from 'react';