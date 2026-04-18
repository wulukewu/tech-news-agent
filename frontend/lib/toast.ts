// Placeholder toast functions to replace Sonner during SSR fix
export const toast = {
  success: async (message: string, options?: { description?: string; duration?: number }) => {
    console.log('Toast (success):', message, options);
    return '';
  },

  error: async (message: string) => {
    console.log('Toast (error):', message);
    return '';
  },

  info: async (message: string, options?: { description?: string; duration?: number }) => {
    console.log('Toast (info):', message, options);
    return '';
  },

  loading: async (message: string, options?: { description?: string }) => {
    console.log('Toast (loading):', message, options);
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
    console.log('Toast (promise):', messages);
    return promise;
  },

  dismiss: async (toastId?: string | number) => {
    console.log('Toast (dismiss):', toastId);
  },
};
