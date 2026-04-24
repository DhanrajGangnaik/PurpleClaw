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
        <div className="app-shell">
          <div className="app-backdrop fixed inset-0" />
          <div className="app-grid fixed inset-0" />
          <main className="relative z-[1] mx-auto flex min-h-screen max-w-3xl items-center px-4 py-12">
            <section className="workspace-panel w-full p-6 sm:p-8">
              <p className="workspace-eyebrow">Application Error</p>
              <h1 className="mt-3 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                PurpleClaw could not render this view
              </h1>
              <p className="mt-3 text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
                A frontend runtime error occurred. Reload the application to retry. The error has been logged to the browser console.
              </p>
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="theme-button-primary mt-6 rounded-2xl px-4 py-3 text-sm font-semibold"
              >
                Reload Application
              </button>
            </section>
          </main>
        </div>
      );
    }

    return this.props.children;
  }
}
