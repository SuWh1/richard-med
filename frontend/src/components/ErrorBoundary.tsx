import { Component, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-danger-soft">
          <AlertTriangle className="h-6 w-6 text-danger" />
        </span>
        <div>
          <h1 className="text-lg font-semibold text-foreground">Что-то пошло не так</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Попробуйте обновить страницу.
          </p>
        </div>
        <Button onClick={() => window.location.reload()}>Обновить</Button>
      </div>
    );
  }
}
