import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { UserProfile, MerchantMembership, UserRole } from '@/types/auth';
import { loginApi, getCurrentUserProfileApi, switchMerchantApi } from '@/api/auth';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  activeMerchant: MerchantMembership | null;
  availableMerchants: MerchantMembership[];
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  switchMerchant: (merchantId: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('recoverx_token'));
  const [user, setUser] = useState<UserProfile | null>(() => {
    const cached = localStorage.getItem('recoverx_user');
    return cached ? JSON.parse(cached) : null;
  });
  const [activeMerchant, setActiveMerchant] = useState<MerchantMembership | null>(() => {
    const cached = localStorage.getItem('recoverx_active_merchant');
    return cached ? JSON.parse(cached) : null;
  });
  const [availableMerchants, setAvailableMerchants] = useState<MerchantMembership[]>(() => {
    const cached = localStorage.getItem('recoverx_available_merchants');
    return cached ? JSON.parse(cached) : [];
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize and validate session on mount
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('recoverx_token');
      if (storedToken) {
        try {
          const profile = await getCurrentUserProfileApi();
          setUser(profile.user);
          setActiveMerchant(profile.active_membership);
          setAvailableMerchants(profile.available_merchants);
          localStorage.setItem('recoverx_user', JSON.stringify(profile.user));
          localStorage.setItem('recoverx_active_merchant', JSON.stringify(profile.active_membership));
          localStorage.setItem('recoverx_active_merchant_id', profile.active_membership.merchant_id);
          localStorage.setItem('recoverx_available_merchants', JSON.stringify(profile.available_merchants));
        } catch {
          // Token is invalid or expired
          logout();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await loginApi(email, password);
      setToken(resp.access_token);
      setUser(resp.user);
      setActiveMerchant(resp.active_merchant);
      setAvailableMerchants(resp.available_merchants);

      localStorage.setItem('recoverx_token', resp.access_token);
      localStorage.setItem('recoverx_user', JSON.stringify(resp.user));
      localStorage.setItem('recoverx_active_merchant', JSON.stringify(resp.active_merchant));
      localStorage.setItem('recoverx_active_merchant_id', resp.active_merchant.merchant_id);
      localStorage.setItem('recoverx_available_merchants', JSON.stringify(resp.available_merchants));

      await queryClient.invalidateQueries();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setActiveMerchant(null);
    setAvailableMerchants([]);

    localStorage.removeItem('recoverx_token');
    localStorage.removeItem('recoverx_user');
    localStorage.removeItem('recoverx_active_merchant');
    localStorage.removeItem('recoverx_active_merchant_id');
    localStorage.removeItem('recoverx_available_merchants');

    queryClient.clear();
  }, [queryClient]);

  const switchMerchant = async (merchantId: string) => {
    setIsLoading(true);
    try {
      const resp = await switchMerchantApi(merchantId);
      setActiveMerchant(resp.active_membership);
      setAvailableMerchants(resp.available_merchants);

      localStorage.setItem('recoverx_active_merchant', JSON.stringify(resp.active_membership));
      localStorage.setItem('recoverx_active_merchant_id', resp.active_membership.merchant_id);
      localStorage.setItem('recoverx_available_merchants', JSON.stringify(resp.available_merchants));

      // Invalidate all queries to trigger dashboard reload for the new tenant
      await queryClient.invalidateQueries();
    } finally {
      setIsLoading(false);
    }
  };

  const role = activeMerchant?.role || null;
  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        activeMerchant,
        availableMerchants,
        role,
        isAuthenticated,
        isLoading,
        login,
        logout,
        switchMerchant,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
