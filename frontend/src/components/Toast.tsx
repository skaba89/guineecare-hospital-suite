import { useEffect, useState } from "react";

export type ToastMessage = {
  id: string;
  text: string;
  type: "success" | "error" | "info" | "warning";
};

let addToastFn: ((toast: Omit<ToastMessage, "id">) => void) | null = null;

export function showToast(
  text: string,
  type: "success" | "error" | "info" | "warning" = "success"
) {
  if (addToastFn) {
    addToastFn({ text, type });
  }
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    addToastFn = (toast) => {
      const id = `toast-${Date.now()}-${Math.random()}`;
      setToasts((prev) => [...prev, { ...toast, id }]);
      // Auto-dismiss after 4s (was 3s — slightly longer for readability)
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    };
    return () => {
      addToastFn = null;
    };
  }, []);

  function dismiss(id: string) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  if (toasts.length === 0) return null;

  return (
    <div
      className="toast-container"
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast toast-${toast.type}`}
          role="alert"
        >
          <span>{toast.text}</span>
          <button
            type="button"
            className="toast-close"
            onClick={() => dismiss(toast.id)}
            aria-label="Fermer la notification"
            title="Fermer"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
