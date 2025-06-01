/**
 * Main Entry Point - GeminiVoiceConnect Dashboard
 * 
 * This is the main entry point for the React application with
 * performance optimizations, error handling, and development tools.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { ColorModeScript } from '@chakra-ui/react';
import App from './App';
import { theme } from './theme';

// Performance monitoring
if (typeof window !== 'undefined') {
  // Mark the start of React rendering
  performance.mark('react-start');
  
  // Log performance metrics
  window.addEventListener('load', () => {
    setTimeout(() => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      const paint = performance.getEntriesByType('paint');
      
      console.group('🚀 GeminiVoiceConnect Performance Metrics');
      console.log('📊 Navigation Timing:', {
        'DNS Lookup': `${navigation.domainLookupEnd - navigation.domainLookupStart}ms`,
        'TCP Connection': `${navigation.connectEnd - navigation.connectStart}ms`,
        'Request/Response': `${navigation.responseEnd - navigation.requestStart}ms`,
        'DOM Processing': `${navigation.domContentLoadedEventEnd - navigation.responseEnd}ms`,
        'Total Load Time': `${navigation.loadEventEnd - navigation.fetchStart}ms`,
      });
      
      if (paint.length > 0) {
        console.log('🎨 Paint Timing:', {
          'First Paint': `${paint[0]?.startTime.toFixed(2)}ms`,
          'First Contentful Paint': `${paint[1]?.startTime.toFixed(2)}ms`,
        });
      }
      
      // Log memory usage if available
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        console.log('💾 Memory Usage:', {
          'Used JS Heap': `${(memory.usedJSHeapSize / 1048576).toFixed(2)} MB`,
          'Total JS Heap': `${(memory.totalJSHeapSize / 1048576).toFixed(2)} MB`,
          'JS Heap Limit': `${(memory.jsHeapSizeLimit / 1048576).toFixed(2)} MB`,
        });
      }
      
      console.groupEnd();
    }, 1000);
  });
}

// Error handling for unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('🚨 Unhandled Promise Rejection:', event.reason);
  
  // You could send this to an error reporting service
  // errorReportingService.captureException(event.reason);
});

// Error handling for uncaught errors
window.addEventListener('error', (event) => {
  console.error('🚨 Uncaught Error:', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error,
  });
  
  // You could send this to an error reporting service
  // errorReportingService.captureException(event.error);
});

// Development tools
if ((import.meta as any).env.DEV) {
  console.log('🔧 Development Mode Enabled');
  
  // React DevTools detection
  if (typeof (window as any).__REACT_DEVTOOLS_GLOBAL_HOOK__ !== 'undefined') {
    console.log('⚛️ React DevTools detected');
  }
  
  // Performance observer for development
  if ('PerformanceObserver' in window) {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'measure') {
          console.log(`📏 ${entry.name}: ${entry.duration.toFixed(2)}ms`);
        }
      }
    });
    
    observer.observe({ entryTypes: ['measure'] });
  }
}

// Service Worker registration for PWA capabilities
if ('serviceWorker' in navigator && (import.meta as any).env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('✅ Service Worker registered:', registration);
      })
      .catch((error) => {
        console.log('❌ Service Worker registration failed:', error);
      });
  });
}

// Initialize React application
const container = document.getElementById('root');
if (!container) {
  throw new Error('Root container not found');
}

const root = ReactDOM.createRoot(container);

// Render the application
root.render(
  <React.StrictMode>
    <ColorModeScript initialColorMode={theme.config.initialColorMode} />
    <App />
  </React.StrictMode>
);

// Mark the end of React rendering
if (typeof window !== 'undefined') {
  performance.mark('react-end');
  performance.measure('react-render', 'react-start', 'react-end');
}

// Hot Module Replacement (HMR) for development
if ((import.meta as any).hot) {
  (import.meta as any).hot.accept();
}