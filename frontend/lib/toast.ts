import { toast as sonnerToast } from 'sonner';

export const toast = {
  success: (message: string) => {
    sonnerToast.success(message, {
      duration: 3000,
      position: 'top-right',
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

  loading: (message: string) => {
    return sonnerToast.loading(message, {
      position: 'top-right',
    });
  },

  promise: <T>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string;
      error: string;
    },
  ) => {
    return sonnerToast.promise(promise, messages);
  },
};
