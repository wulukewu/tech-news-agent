'use client';

/**
 * AuthGuard Component
 *
 * A wrapper component that ensures the AuthProvider context is available
 * before rendering children that use useAuth. This prevents the
 * "useAuth must be used within AuthProvider" error during hydration.
 */

import { useContext } from 'react';
import { AuthContext } from '@/contexts/AuthContext';

interface AuthGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function AuthGuard({ children, fallback = null }: AuthGuardProps) {
  const context = useContext(AuthContext);

  // If context is not available, render fallback or nothing
  if (!context) {
    return <>{fallback}</>;
  }

  // Context is available, render children
  return <>{children}</>;
}
