"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

type Props = {
  children: ReactNode;
  fallback?: ReactNode;
};

type State = {
  hasError: boolean;
  error: Error | null;
};

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex min-h-[40vh] items-center justify-center p-8">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-white/5 p-8 text-center backdrop-blur-xl">
            <AlertTriangle className="mx-auto h-12 w-12 text-amber-400" />
            <h2 className="mt-4 text-lg font-semibold text-white">Something went wrong</h2>
            <p className="mt-2 text-sm text-slate-400">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <button
              onClick={this.handleRetry}
              className="mt-6 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-500 px-5 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90"
            >
              <RefreshCw className="h-4 w-4" />
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
