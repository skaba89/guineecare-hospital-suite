import { useEffect, useState } from "react";

export type ToastMessage = {
  id: string;
  text: string;
  type: "success" | "error";
};

let addToastFn: ((toast: Omit<ToastMessage, "id">) => void) | null = null;

export function showToast(text: string, type: "success" | "error" = "success") {
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
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3000);
    };
    return () => {
      addToastFn = null;
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast toast-${toast.type}`}>
          {toast.text}
        </div>
      ))}
    </div>
  );
}
