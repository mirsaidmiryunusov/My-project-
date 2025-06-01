/**
 * Main Application Component - GeminiVoiceConnect Dashboard
 * 
 * Revolutionary AI Call Center Agent Management Interface
 */

import React, { Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ChakraProvider, Box, Spinner, Center, Text, VStack } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { HelmetProvider } from 'react-helmet-async';
import { ErrorBoundary } from 'react-error-boundary';
import { Toaster } from 'react-hot-toast';

// Theme and styling
import { theme } from './theme';

// Store and state management
import { useAuthStore } from './stores/authStore';

// Layout components
import { DashboardLayout } from './components/Layout/DashboardLayout';

// Page components (lazy loaded for performance)
const LoginPage = React.lazy(() => import('./pages/Auth/LoginPage'));
const DashboardPage = React.lazy(() => import('./pages/Dashboard/DashboardPage'));

// Error components
import { ErrorFallback } from './components/Error/ErrorFallback';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
    },
  },
});

const LoadingSpinner: React.FC<{ message?: string }> = ({ message = "Loading..." }) => (
  <Center h="100vh" bg="gray.50">
    <VStack spacing={4}>
      <Spinner size="xl" color="blue.500" />
      <Text fontSize="lg" color="gray.600">{message}</Text>
    </VStack>
  </Center>
);

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <LoadingSpinner message="Authenticating..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <HelmetProvider>
      <ChakraProvider theme={theme}>
        <QueryClientProvider client={queryClient}>
          <ErrorBoundary FallbackComponent={ErrorFallback}>
            <Router>
              <Box minH="100vh" bg="gray.50">
                <Suspense fallback={<LoadingSpinner />}>
                  <Routes>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/" element={
                      <ProtectedRoute>
                        <DashboardLayout>
                          <DashboardPage />
                        </DashboardLayout>
                      </ProtectedRoute>
                    } />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </Suspense>
              </Box>
            </Router>
            <Toaster position="top-right" />
          </ErrorBoundary>
        </QueryClientProvider>
      </ChakraProvider>
    </HelmetProvider>
  );
};

export default App;