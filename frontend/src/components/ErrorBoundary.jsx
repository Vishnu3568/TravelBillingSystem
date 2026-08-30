import React from "react";
import { AlertOctagon, RefreshCw, Home } from "lucide-react";

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error("Uncaught application error in React component tree:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6 font-sans">
          <div className="bg-slate-900 border border-rose-500/30 max-w-lg w-full p-8 shadow-2xl space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
              <div className="p-3 bg-rose-500/10 rounded-lg border border-rose-500/20 text-rose-400">
                <AlertOctagon size={28} />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white tracking-wide">Application Runtime Error</h1>
                <p className="text-xs text-slate-400">An unexpected component error occurred.</p>
              </div>
            </div>

            <div className="bg-slate-950 p-4 border border-slate-800 font-mono text-xs text-rose-300 max-h-40 overflow-y-auto">
              {this.state.error?.toString() || "Unknown rendering exception"}
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2 transition-colors"
              >
                <Home size={14} /> Go Home
              </button>
              <button
                onClick={this.handleReload}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center gap-2 transition-colors"
              >
                <RefreshCw size={14} /> Reload Application
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
