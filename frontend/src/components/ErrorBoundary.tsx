import { Component, type ReactNode } from "react";

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

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="card" style={{ padding: "32px", textAlign: "center" }}>
          <h2 style={{ color: "var(--danger)", marginBottom: "12px" }}>Une erreur est survenue</h2>
          <p className="muted" style={{ marginBottom: "16px" }}>
            {this.state.error?.message || "Erreur inattendue"}
          </p>
          <button
            className="primary-button"
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
          >
            Recharger la page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
