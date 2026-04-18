/**
 * Enhanced Error Boundary with Developer-Friendly Error Messages
 * Requirements: 13.1, 13.4
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { apiLogger } from '@/lib/api/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Generate unique error ID for tracking
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    return {
      hasError: true,
      error,
      errorId,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error with context
    apiLogger.error('React Error Boundary caught error', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      errorId: this.state.errorId,
      url: typeof window !== 'undefined' ? window.location.href : 'SSR',
      userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
      timestamp: new Date().toISOString(),
    });

    // Update state with error info
    this.setState({
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Send error to backend for logging (in production)
    if (process.env.NODE_ENV === 'production') {
      this.sendErrorToBackend(error, errorInfo);
    }
  }

  private async sendErrorToBackend(error: Error, errorInfo: ErrorInfo) {
    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          level: 'error',
          message: 'React Error Boundary',
          context: {
            error: error.message,
            stack: error.stack,
            componentStack: errorInfo.componentStack,
            errorId: this.state.errorId,
            url: typeof window !== 'undefined' ? window.location.href : 'SSR',
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'SSR',
          },
        }),
      });
    } catch (logError) {
      console.error('Failed to send error to backend:', logError);
    }
  }

  private getErrorSuggestions(error: Error): string[] {
    const suggestions: string[] = [];
    const message = error.message.toLowerCase();
    const stack = error.stack?.toLowerCase() || '';

    // Common React errors and suggestions
    if (message.includes('cannot read property') || message.includes('cannot read properties')) {
      suggestions.push('Check if the object exists before accessing its properties');
      suggestions.push('Use optional chaining (?.) or conditional rendering');
    }

    if (message.includes('undefined is not a function')) {
      suggestions.push('Verify that the function is properly imported and defined');
      suggestions.push('Check if the component is wrapped with the correct HOCs');
    }

    if (message.includes('hydration')) {
      suggestions.push('Ensure server and client render the same content');
      suggestions.push('Check for differences in data between SSR and client-side rendering');
    }

    if (stack.includes('useeffect') || stack.includes('usestate')) {
      suggestions.push('Verify hooks are called at the top level of the component');
      suggestions.push('Check hook dependencies and cleanup functions');
    }

    if (stack.includes('api') || stack.includes('fetch')) {
      suggestions.push('Check network connectivity and API endpoint availability');
      suggestions.push('Verify API response format and error handling');
    }

    if (suggestions.length === 0) {
      suggestions.push('Check the browser console for additional error details');
      suggestions.push('Verify all imports and dependencies are correct');
      suggestions.push('Try refreshing the page or clearing browser cache');
    }

    return suggestions;
  }

  private getComponentStack(): string[] {
    if (!this.state.errorInfo?.componentStack) return [];

    return this.state.errorInfo.componentStack
      .split('\n')
      .filter((line) => line.trim())
      .slice(0, 5) // Show only top 5 components
      .map((line) => line.trim());
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Development error UI with detailed information
      if (process.env.NODE_ENV === 'development') {
        return (
          <div className="min-h-screen bg-red-50 flex items-center justify-center p-4">
            <div className="max-w-4xl w-full bg-white rounded-lg shadow-lg border border-red-200">
              <div className="bg-red-600 text-white p-4 rounded-t-lg">
                <h1 className="text-xl font-bold flex items-center">
                  <span className="mr-2">🚨</span>
                  Application Error
                </h1>
                <p className="text-red-100 mt-1">Error ID: {this.state.errorId}</p>
              </div>

              <div className="p-6 space-y-6">
                {/* Error Message */}
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">Error Message</h2>
                  <div className="bg-gray-100 p-3 rounded border font-mono text-sm">
                    {this.state.error?.message || 'Unknown error occurred'}
                  </div>
                </div>

                {/* Suggestions */}
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-2">
                    💡 Suggested Solutions
                  </h2>
                  <ul className="space-y-2">
                    {this.getErrorSuggestions(this.state.error!).map((suggestion, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        <span className="text-gray-700">{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Component Stack */}
                {this.getComponentStack().length > 0 && (
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-2">Component Stack</h2>
                    <div className="bg-gray-100 p-3 rounded border font-mono text-sm space-y-1">
                      {this.getComponentStack().map((line, index) => (
                        <div key={index} className="text-gray-700">
                          {line}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Error Stack (collapsible) */}
                <details className="group">
                  <summary className="cursor-pointer text-lg font-semibold text-gray-900 mb-2 group-open:mb-4">
                    🔍 Full Error Stack (Click to expand)
                  </summary>
                  <div className="bg-gray-100 p-3 rounded border font-mono text-xs overflow-auto max-h-64">
                    <pre className="whitespace-pre-wrap text-gray-700">
                      {this.state.error?.stack || 'No stack trace available'}
                    </pre>
                  </div>
                </details>

                {/* Actions */}
                <div className="flex flex-wrap gap-3 pt-4 border-t">
                  <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  >
                    🔄 Reload Page
                  </button>
                  <button
                    onClick={() => window.history.back()}
                    className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                  >
                    ← Go Back
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(
                        `Error ID: ${this.state.errorId}\nMessage: ${this.state.error?.message}\nStack: ${this.state.error?.stack}`
                      );
                      alert('Error details copied to clipboard');
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                  >
                    📋 Copy Error Details
                  </button>
                </div>

                {/* Development Tips */}
                <div className="bg-blue-50 border border-blue-200 rounded p-4">
                  <h3 className="font-semibold text-blue-900 mb-2">🛠️ Development Tips</h3>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Check the browser console for additional error details</li>
                    <li>• Use React DevTools to inspect component state and props</li>
                    <li>• Enable "Pause on exceptions" in browser debugger</li>
                    <li>• Check Network tab for failed API requests</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        );
      }

      // Production error UI (minimal)
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg border p-6 text-center">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h1>
            <p className="text-gray-600 mb-6">
              We're sorry, but something unexpected happened. Please try refreshing the page.
            </p>
            <div className="space-y-3">
              <button
                onClick={() => window.location.reload()}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Refresh Page
              </button>
              <button
                onClick={() => window.history.back()}
                className="w-full px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 transition-colors"
              >
                Go Back
              </button>
            </div>
            {this.state.errorId && (
              <p className="text-xs text-gray-400 mt-4">Error ID: {this.state.errorId}</p>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Higher-order component for easy wrapping
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

export default ErrorBoundary;
