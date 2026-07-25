import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { I18nProvider } from "./i18n";
import { ThemeProvider } from "./contexts/ThemeContext";
import "./styles.css";

// --- PWA service worker registration (v1.3.0) ---
// Registers /sw.js in production. In dev (vite dev server) the SW is
// disabled to avoid caching source files that change on every HMR.
if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((reg) => console.info("[pwa] Service worker registered:", reg.scope))
      .catch((err) => console.warn("[pwa] Service worker registration failed:", err));
  });
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <I18nProvider>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </I18nProvider>
  </React.StrictMode>
);
