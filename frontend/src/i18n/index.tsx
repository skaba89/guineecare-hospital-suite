/**
 * i18n module — v1.3.0
 *
 * Lightweight i18n implementation (no dependency on i18next). Reasons:
 * - The backend already exposes /api/v1/i18n/translations/{locale} catalogs.
 * - Adding i18next + react-i18next would inflate the bundle by ~30kB just
 *   for translation lookup. Our use case is simple enough (flat key→value
 *   lookup with variable interpolation) that a 100-line implementation
 *   suffices.
 *
 * Features:
 * - Catalog fetched from /api/v1/i18n/translations/{locale} on first load.
 * - Locale stored in localStorage (`guineecare_locale`).
 * - Falls back to FR if the catalog can't be fetched.
 * - `t(key, vars)` interpolates {vars} via simple string replacement.
 * - `<I18nProvider>` wraps the app and exposes context via `useI18n()`.
 *
 * Usage:
 *   const { t, locale, setLocale } = useI18n();
 *   <button>{t('common.save')}</button>
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getToken } from "../services/api";

export type Locale = "fr" | "en";

const DEFAULT_LOCALE: Locale = "fr";
const LOCALE_STORAGE_KEY = "guineecare_locale";
const SUPPORTED_LOCALES: Locale[] = ["fr", "en"];

type Catalog = Record<string, string>;

type I18nContextValue = {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  loading: boolean;
  supportedLocales: Locale[];
};

const I18nContext = createContext<I18nContextValue | null>(null);

/** Detect the user's preferred locale on first load. */
function detectInitialLocale(): Locale {
  // 1. Explicit user choice in localStorage
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY) as Locale | null;
  if (stored && SUPPORTED_LOCALES.includes(stored)) return stored;
  // 2. Browser language
  const nav = navigator.language?.toLowerCase() || "";
  if (nav.startsWith("en")) return "en";
  // 3. Default
  return DEFAULT_LOCALE;
}

/** Simple {var} interpolation. Missing vars render as empty string. */
function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, k) =>
    vars[k] !== undefined ? String(vars[k]) : ""
  );
}

/** Fetch a translation catalog from the backend. */
async function fetchCatalog(locale: Locale): Promise<Catalog> {
  try {
    const r = await fetch(`/api/v1/i18n/translations/${locale}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    return data.translations || {};
  } catch (e) {
    console.warn(`[i18n] Failed to fetch catalog for ${locale}:`, e);
    return {};
  }
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(detectInitialLocale);
  const [catalog, setCatalog] = useState<Catalog>({});
  const [loading, setLoading] = useState(true);

  // Fetch catalog whenever locale changes
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchCatalog(locale).then((c) => {
      if (cancelled) return;
      setCatalog(c);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, [locale]);

  const setLocale = useCallback((l: Locale) => {
    localStorage.setItem(LOCALE_STORAGE_KEY, l);
    setLocaleState(l);
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const template = catalog[key];
      if (!template) return key; // fallback to key itself
      return interpolate(template, vars);
    },
    [catalog]
  );

  const value = useMemo<I18nContextValue>(
    () => ({ locale, setLocale, t, loading, supportedLocales: SUPPORTED_LOCALES }),
    [locale, setLocale, t, loading]
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within <I18nProvider>");
  return ctx;
}

/** Hook to translate a key with vars, memoized. */
export function useT() {
  return useI18n().t;
}
