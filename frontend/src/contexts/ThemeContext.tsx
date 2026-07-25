import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

/**
 * Theme Context — v2.9.2
 *
 * Gère le toggle mode clair / mode sombre.
 * La préférence est persistée dans localStorage (clé "guineecare_theme").
 * Au premier chargement, on respecte la préférence système
 * (prefers-color-scheme) si l'utilisateur n'a pas encore choisi.
 *
 * Usage :
 *   <ThemeProvider><App /></ThemeProvider>
 *
 *   const { theme, toggleTheme } = useTheme();
 *   <button onClick={toggleTheme}>{theme === "dark" ? "☀️" : "🌙"}</button>
 */

type Theme = "light" | "dark";

type ThemeContextValue = {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (t: Theme) => void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "guineecare_theme";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";

  // 1. Préférence utilisateur explicite
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") {
    return stored;
  }

  // 2. Préférence système
  if (window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }

  // 3. Défaut
  return "light";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  // Applique le thème sur <html data-theme="...">
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  // Écoute les changements de préférence système (si l'utilisateur n'a pas
  // explicitement choisi, on suit le système en temps réel)
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;

    const handler = (e: MediaQueryListEvent) => {
      const stored = localStorage.getItem(STORAGE_KEY);
      // Seulement si l'utilisateur n'a pas explicitement choisi
      if (!stored) {
        setThemeState(e.matches ? "dark" : "light");
      }
    };

    mq.addEventListener?.("change", handler);
    return () => mq.removeEventListener?.("change", handler);
  }, []);

  const setTheme = (t: Theme) => setThemeState(t);
  const toggleTheme = () =>
    setThemeState((prev) => (prev === "dark" ? "light" : "dark"));

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
}
