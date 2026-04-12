/**
 * Error Handling Examples
 *
 * This file demonstrates how to use the unified API client with error handling.
 * These examples show best practices for handling different error scenarios.
 */

import { apiClient, ApiError, ErrorCode } from '../index';

// ============================================================================
// Example 1: Basic Error Handling
// ============================================================================

export async function basicErrorHandling() {
  try {
    const users = await apiClient.get<any[]>('/api/users');
    console.log('Users:', users);
    return users;
  } catch (error) {
    if (error instanceof ApiError) {
      // Display user-friendly message
      console.error('Error:', error.getDisplayMessage());

      // Access error details
      console.error('Status:', error.statusCode);
      console.error('Code:', error.errorCode);
      console.error('Details:', error.details);
    }
    throw error;
  }
}

// ============================================================================
// Example 2: Specific Error Code Handling
// ============================================================================

export async function specificErrorHandling(userId: string) {
  try {
    const user = await apiClient.get<any>(`/api/users/${userId}`);
    return user;
  } catch (error) {
    if (error instanceof ApiError) {
      switch (error.errorCode) {
        case ErrorCode.NOT_FOUND:
          console.error('User not found');
          // Show "User not found" message to user
          break;

        case ErrorCode.AUTH_INVALID_TOKEN:
          console.error('Authentication failed');
          // Redirect to login (handled automatically by client)
          break;

        case ErrorCode.RATE_LIMIT_EXCEEDED:
          console.error('Rate limit exceeded');
          // Show "Please wait" message to user
          break;

        default:
          console.error('Error:', error.getDisplayMessage());
      }
    }
    throw error;
  }
}

// ============================================================================
// Example 3: Validation Error Handling
// ============================================================================

export async function validationErrorHandling(userData: any) {
  try {
    const user = await apiClient.post<any>('/api/users', userData);
    return user;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.errorCode === ErrorCode.VALIDATION_FAILED && error.details) {
        // Display field-specific validation errors
        error.details.forEach((detail) => {
          console.error(`${detail.field}: ${detail.message}`);
          // Show error next to form field
        });
      } else {
        console.error('Error:', error.getDisplayMessage());
      }
    }
    throw error;
  }
}

// ============================================================================
// Example 4: Retryable Error Handling
// ============================================================================

export async function retryableErrorHandling() {
  try {
    const data = await apiClient.get<any>('/api/external-service');
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.isRetryable()) {
        console.log('This error can be retried');
        // Show retry button to user
        // The client already retried automatically, but you can offer manual retry
      } else {
        console.error('Error cannot be retried:', error.getDisplayMessage());
      }
    }
    throw error;
  }
}

// ============================================================================
// Example 5: Custom Retry Configuration
// ============================================================================

export async function customRetryConfiguration() {
  // Configure retry behavior
  apiClient.setRetryConfig({
    maxRetries: 5,
    baseDelay: 2000,
    maxDelay: 60000,
    onRetry: (attempt, error, delay) => {
      console.log(`Retry attempt ${attempt} after ${delay}ms`);
      console.log(`Error: ${error.errorCode}`);
      // Show retry notification to user
    },
  });

  try {
    const data = await apiClient.get<any>('/api/unreliable-service');
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      console.error('All retries failed:', error.getDisplayMessage());
    }
    throw error;
  }
}

// ============================================================================
// Example 6: Error Logging
// ============================================================================

export async function errorLogging() {
  try {
    const data = await apiClient.get<any>('/api/data');
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      // Log error for debugging
      console.error('API Error:', error.toJSON());

      // Send error to monitoring service
      // sendToMonitoring(error.toJSON());

      // Display user-friendly message
      console.error('User message:', error.getDisplayMessage());
    }
    throw error;
  }
}

// ============================================================================
// Example 7: Multiple Error Types
// ============================================================================

export async function multipleErrorTypes() {
  try {
    const data = await apiClient.get<any>('/api/data');
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      // Handle API errors
      if (error.statusCode >= 500) {
        console.error('Server error:', error.getDisplayMessage());
        // Show "Server error, please try again" message
      } else if (error.statusCode >= 400) {
        console.error('Client error:', error.getDisplayMessage());
        // Show specific error message based on error code
      }
    } else {
      // Handle unexpected errors
      console.error('Unexpected error:', error);
      // Show generic error message
    }
    throw error;
  }
}

// ============================================================================
// Example 8: React Component Integration
// ============================================================================

export async function reactComponentExample() {
  // Example of how to use in React component
  /*
  import { useState } from 'react';
  import { apiClient, ApiError, ErrorCode } from '@/lib/api';
  import { toast } from '@/lib/toast';

  function UserProfile({ userId }: { userId: string }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function fetchUser() {
      setLoading(true);
      setError(null);

      try {
        const userData = await apiClient.get(`/api/users/${userId}`);
        setUser(userData);
      } catch (err) {
        if (err instanceof ApiError) {
          // Set error message for display
          setError(err.getDisplayMessage());

          // Show toast notification
          toast.error(err.getDisplayMessage());

          // Handle specific errors
          if (err.errorCode === ErrorCode.NOT_FOUND) {
            // Redirect to 404 page
          }
        } else {
          setError('An unexpected error occurred');
          toast.error('An unexpected error occurred');
        }
      } finally {
        setLoading(false);
      }
    }

    // ... rest of component
  }
  */
}

// ============================================================================
// Example 9: Form Submission with Validation
// ============================================================================

export async function formSubmissionExample(formData: any) {
  try {
    const result = await apiClient.post<any>('/api/forms', formData);
    console.log('Form submitted successfully:', result);
    return result;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.errorCode === ErrorCode.VALIDATION_FAILED && error.details) {
        // Create field error map for form
        const fieldErrors: Record<string, string> = {};
        error.details.forEach((detail) => {
          if (detail.field) {
            fieldErrors[detail.field] = detail.message;
          }
        });

        console.log('Field errors:', fieldErrors);
        // Return field errors to form
        return { success: false, errors: fieldErrors };
      } else {
        console.error('Form submission error:', error.getDisplayMessage());
        return { success: false, message: error.getDisplayMessage() };
      }
    }
    throw error;
  }
}

// ============================================================================
// Example 10: Graceful Degradation
// ============================================================================

export async function gracefulDegradation() {
  try {
    const recommendations = await apiClient.get<any[]>('/api/recommendations');
    return recommendations;
  } catch (error) {
    if (error instanceof ApiError) {
      console.warn('Failed to load recommendations:', error.getDisplayMessage());

      // Return empty array instead of failing
      // This allows the page to still render without recommendations
      return [];
    }
    throw error;
  }
}
