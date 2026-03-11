import { Component, type ErrorInfo, type ReactNode, useState, useEffect } from "react";
import { Button } from "@/shared/components/ui/button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * React error boundary — catches render-time exceptions and shows a fallback UI
 * instead of a blank screen.
 */
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

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return <ErrorFallback error={this.state.error} onReset={this.handleReset} />;
    }
    return this.props.children;
  }
}

// Functional wrapper so hooks (useTranslation) can be used
function ErrorFallback({ error, onReset }: { error: Error | null; onReset: () => void }) {
  const [labels, setLabels] = useState({
    title: "Something went wrong",
    unexpected: "An unexpected error occurred.",
    tryAgain: "Try again",
  });

  useEffect(() => {
    // Dynamically resolve translations after i18n initialises
    import("../../i18n").then(({ default: i18n }) => {
      const t = (k: string) => i18n.t(k);
      setLabels({
        title: t("error.title"),
        unexpected: t("error.unexpected"),
        tryAgain: t("error.tryAgain"),
      });
    });
  }, []);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 text-center">
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">{labels.title}</h2>
        <p className="text-muted-foreground text-sm max-w-md">
          {error?.message ?? labels.unexpected}
        </p>
      </div>
      <Button onClick={onReset} variant="outline">
        {labels.tryAgain}
      </Button>
    </div>
  );
}
