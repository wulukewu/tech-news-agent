// Placeholder toast functions to replace Sonner during SSR fix
import { logger } from '@/lib/utils/logger';
export const toast = {
  success: async (message: string, options?: { description?: string; duration?: number }) => {
    logger.debug('Toast (success):', message, options);
    return '';
  },

  error: async (message: string) => {
    logger.debug('Toast (error):', message);
    return '';
  },

  info: async (message: string, options?: { description?: string; duration?: number }) => {
    logger.debug('Toast (info):', message, options);
    return '';
  },

  loading: async (message: string, options?: { description?: string }) => {
    logger.debug('Toast (loading):', message, options);
    return '';
  },

  promise: async <T>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    }
  ) => {
    logger.debug('Toast (promise):', messages);
    return promise;
  },

  dismiss: async (toastId?: string | number) => {
    logger.debug('Toast (dismiss):', toastId);
  },
};
