import { Component, type ErrorInfo, type ReactNode } from 'react';

interface AppErrorBoundaryProps {
  children: ReactNode;
}

interface AppErrorBoundaryState {
  hasError: boolean;
}

export class AppErrorBoundary extends Component<AppErrorBoundaryProps, AppErrorBoundaryState> {
  state: AppErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): AppErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('PurpleClaw render error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
          <div className="card p-8 max-w-lg w-full text-center">
            <p className="text-xs text-purple-400 uppercase tracking-wider mb-2">Application Error</p>
            <h1 className="text-xl font-semibold text-gray-200 mb-3">
              PurpleClaw could not render this view
            </h1>
            <p className="text-sm text-gray-500 mb-6 leading-6">
              A frontend runtime error occurred. The error has been logged to the browser console.
              Navigate to a different page or reload to continue.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                type="button"
                onClick={() => { this.setState({ hasError: false }); window.history.back(); }}
                className="btn-secondary"
              >
                Go Back
              </button>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="btn-primary"
              >
                Reload
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
