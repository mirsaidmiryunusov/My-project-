/**
 * Authentication Store for Project GeminiVoiceConnect Dashboard
 * 
 * This store manages user authentication state, login/logout functionality,
 * and user permissions using Zustand for state management.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'operator' | 'agent' | 'viewer';
  tenantId: string;
  avatar?: string;
  permissions: string[];
  lastLogin?: string;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
    notifications: {
      email: boolean;
      sms: boolean;
      push: boolean;
    };
  };
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
}

type AuthStore = AuthState & AuthActions;

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          // Simulate API call
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Mock successful login
          const mockUser: User = {
            id: '1',
            name: 'John Doe',
            email: email,
            role: 'admin',
            tenantId: 'tenant_1',
            avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face',
            permissions: [
              'calls:read',
              'calls:write',
              'sms:read',
              'sms:write',
              'customers:read',
              'customers:write',
              'campaigns:read',
              'campaigns:write',
              'analytics:read',
              'system:read',
              'system:write',
              'settings:read',
              'settings:write',
            ],
            lastLogin: new Date().toISOString(),
            preferences: {
              theme: 'system',
              language: 'en',
              timezone: 'UTC',
              notifications: {
                email: true,
                sms: false,
                push: true,
              },
            },
          };

          const mockToken = 'mock_jwt_token_' + Date.now();

          set({
            user: mockUser,
            token: mockToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Login failed',
          });
        }
      },

      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      refreshToken: async () => {
        const { token } = get();
        if (!token) return;

        try {
          // Simulate token refresh
          await new Promise(resolve => setTimeout(resolve, 500));
          
          const newToken = 'refreshed_token_' + Date.now();
          set({ token: newToken });
        } catch (error) {
          // If refresh fails, logout user
          get().logout();
        }
      },

      updateUser: (updates: Partial<User>) => {
        const { user } = get();
        if (user) {
          set({
            user: { ...user, ...updates },
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helper hooks for permissions
export const usePermissions = () => {
  const user = useAuthStore(state => state.user);
  
  const hasPermission = (permission: string): boolean => {
    return user?.permissions.includes(permission) || false;
  };

  const hasRole = (role: string): boolean => {
    return user?.role === role;
  };

  const hasAnyRole = (roles: string[]): boolean => {
    return roles.includes(user?.role || '');
  };

  return {
    hasPermission,
    hasRole,
    hasAnyRole,
    permissions: user?.permissions || [],
    role: user?.role,
  };
};