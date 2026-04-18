'use client';

/**
 * NotFoundContext
 *
 * Context to track if the current page is a 404 error page.
 * This helps ConditionalLayout avoid redirecting 404 pages to login.
 */

import { createContext, useContext, useState, ReactNode } from 'react';

interface NotFoundContextType {
  isNotFound: boolean;
  setIsNotFound: (value: boolean) => void;
}

const NotFoundContext = createContext<NotFoundContextType | undefined>(undefined);

export function NotFoundProvider({ children }: { children: ReactNode }) {
  const [isNotFound, setIsNotFound] = useState(false);

  return (
    <NotFoundContext.Provider value={{ isNotFound, setIsNotFound }}>
      {children}
    </NotFoundContext.Provider>
  );
}

export function useNotFound() {
  const context = useContext(NotFoundContext);
  if (context === undefined) {
    throw new Error('useNotFound must be used within a NotFoundProvider');
  }
  return context;
}
