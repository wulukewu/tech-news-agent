import { toast as sonnerToast } from 'sonner';

export const toast = {
  success: (message: string, options?: { description?: string; duration?: number }) => {
    sonnerToast.success(message, {
      duration: options?.duration || 3000,
      position: 'top-right',
      description: options?.description,
    });
  },

  error: (message: string) => {
    sonnerToast.error(message, {
      duration: 5000,
      position: 'top-right',
      action: {
        label: 'Dismiss',
        onClick: () => {},
      },
    });
  },

  info: (message: string, options?: { description?: string; duration?: number }) => {
    sonnerToast.info(message, {
      duration: options?.duration || 3000,
      position: 'top-right',
      description: options?.description,
    });
  },

  loading: (message: string, options?: { description?: string }) => {
    return sonnerToast.loading(message, {
      position: 'top-right',
      description: options?.description,
    });
  },

  promise: <T>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    }
  ) => {
    return sonnerToast.promise(promise, messages);
  },

  dismiss: (toastId?: string | number) => {
    sonnerToast.dismiss(toastId);
  },
};
