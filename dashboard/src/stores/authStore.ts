/**
 * Authentication Store for Project GeminiVoiceConnect Dashboard
 * 
 * This store manages user authentication state, login/logout functionality,
 * and user permissions using Zustand for state management.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, wsClient, User as ApiUser, LoginCredentials, RegisterData } from '../services/api';

export interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: string;
  tenantId: string;
  avatar?: string;
  permissions: string[];
  lastLogin?: string;
  preferences?: {
    theme: string;
    language: string;
    timezone: string;
    emailNotifications: boolean;
    smsNotifications: boolean;
    pushNotifications: boolean;
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
  login: (email: string, password: string) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
  updateProfile: (updates: Partial<User>) => Promise<boolean>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
  getCurrentUser: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  initializeAuth: () => Promise<void>;
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
          const response = await apiClient.login({ email, password });
          
          if (response.success && response.data) {
            const { user, accessToken, refreshToken } = response.data;
            
            // Store tokens
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('refreshToken', refreshToken);
            
            // Set API client token
            apiClient.setToken(accessToken);
            
            // Connect WebSocket
            wsClient.connect(accessToken);
            
            set({
              user: {
                id: user.id,
                firstName: user.firstName,
                lastName: user.lastName,
                email: user.email,
                role: user.role,
                tenantId: user.tenantId,
                permissions: user.permissions,
                preferences: user.preferences,
              },
              token: accessToken,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            
            return true;
          } else {
            set({
              isLoading: false,
              error: response.message || 'Login failed',
            });
            return false;
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Login failed',
          });
          return false;
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await apiClient.register(data);
          
          if (response.success && response.data) {
            const { user, accessToken, refreshToken } = response.data;
            
            // Store tokens
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('refreshToken', refreshToken);
            
            // Set API client token
            apiClient.setToken(accessToken);
            
            // Connect WebSocket
            wsClient.connect(accessToken);
            
            set({
              user: {
                id: user.id,
                firstName: user.firstName,
                lastName: user.lastName,
                email: user.email,
                role: user.role,
                tenantId: user.tenantId,
                permissions: user.permissions,
                preferences: user.preferences,
              },
              token: accessToken,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
            
            return true;
          } else {
            set({
              isLoading: false,
              error: response.message || 'Registration failed',
            });
            return false;
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Registration failed',
          });
          return false;
        }
      },

      logout: async () => {
        try {
          await apiClient.logout();
        } catch (error) {
          console.error('Logout error:', error);
        }
        
        // Clear tokens and disconnect
        apiClient.clearAuth();
        wsClient.disconnect();
        
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      refreshToken: async () => {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          get().logout();
          return;
        }

        try {
          const response = await apiClient.refreshToken(refreshToken);
          
          if (response.success && response.data) {
            const { accessToken, refreshToken: newRefreshToken } = response.data;
            
            // Update tokens
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('refreshToken', newRefreshToken);
            
            // Set API client token
            apiClient.setToken(accessToken);
            
            set({ token: accessToken });
          } else {
            get().logout();
          }
        } catch (error) {
          console.error('Token refresh failed:', error);
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

      updateProfile: async (updates: Partial<User>) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await apiClient.updateProfile(updates);
          
          if (response.success && response.data) {
            const updatedUser = response.data;
            set({
              user: {
                id: updatedUser.id,
                firstName: updatedUser.firstName,
                lastName: updatedUser.lastName,
                email: updatedUser.email,
                role: updatedUser.role,
                tenantId: updatedUser.tenantId,
                permissions: updatedUser.permissions,
                preferences: updatedUser.preferences,
              },
              isLoading: false,
            });
            return true;
          } else {
            set({
              isLoading: false,
              error: response.message || 'Failed to update profile',
            });
            return false;
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to update profile',
          });
          return false;
        }
      },

      changePassword: async (currentPassword: string, newPassword: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await apiClient.changePassword(currentPassword, newPassword);
          
          if (response.success) {
            set({ isLoading: false });
            return true;
          } else {
            set({
              isLoading: false,
              error: response.message || 'Failed to change password',
            });
            return false;
          }
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to change password',
          });
          return false;
        }
      },

      getCurrentUser: async () => {
        try {
          const response = await apiClient.getCurrentUser();
          
          if (response.success && response.data) {
            const user = response.data;
            set({
              user: {
                id: user.id,
                firstName: user.firstName,
                lastName: user.lastName,
                email: user.email,
                role: user.role,
                tenantId: user.tenantId,
                permissions: user.permissions,
                preferences: user.preferences,
              },
            });
          }
        } catch (error) {
          console.error('Failed to get current user:', error);
        }
      },

      initializeAuth: async () => {
        const token = localStorage.getItem('accessToken');
        if (token) {
          apiClient.setToken(token);
          set({ token, isAuthenticated: true });
          
          try {
            await get().getCurrentUser();
            wsClient.connect(token);
          } catch (error) {
            console.error('Failed to initialize auth:', error);
            get().logout();
          }
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