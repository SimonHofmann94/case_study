'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { authApi, User, LoginRequest, RegisterRequest } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const clearError = useCallback(() => setError(null), []);

  // Check for existing token on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      const storedUser = localStorage.getItem('user');

      if (token && storedUser) {
        try {
          // Verify token is still valid
          const userData = await authApi.me();
          setUser(userData);
          localStorage.setItem('user', JSON.stringify(userData));
        } catch {
          // Token invalid, clear storage
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (data: LoginRequest) => {
    try {
      setError(null);
      setIsLoading(true);
      const response = await authApi.login(data);

      localStorage.setItem('token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      setUser(response.user);

      router.push('/dashboard');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      const message = error.response?.data?.detail || 'Login failed. Please try again.';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterRequest) => {
    try {
      setError(null);
      setIsLoading(true);
      await authApi.register(data);

      // After registration, log in automatically
      const loginResponse = await authApi.login({
        email: data.email,
        password: data.password,
      });

      localStorage.setItem('token', loginResponse.access_token);
      localStorage.setItem('user', JSON.stringify(loginResponse.user));
      setUser(loginResponse.user);

      router.push('/dashboard');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      const message = error.response?.data?.detail || 'Registration failed. Please try again.';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    router.push('/auth/login');
  }, [router]);

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    error,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
