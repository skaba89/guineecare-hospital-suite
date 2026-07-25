/**
 * i18n module — v2.8.6
 *
 * v2.8.6 — FIX : catalog de fallback intégré au frontend.
 * Avant : si le backend était en cold start (Render free tier), le fetch
 * du catalog échouait → toutes les clés s'affichaient telles quelles
 * (login.title, login.email, etc.).
 * Maintenant : un catalog de fallback minimal est intégré au code, et
 * le fetch backend est retry avec timeout. Si le fetch échoue, on
 * utilise le fallback.
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getToken } from "../services/api";

export type Locale = "fr" | "en";

const DEFAULT_LOCALE: Locale = "fr";
const LOCALE_STORAGE_KEY = "guineecare_locale";
const SUPPORTED_LOCALES: Locale[] = ["fr", "en"];

type Catalog = Record<string, string>;

// v2.8.6 — Catalog de fallback FR intégré (pas de dépendance réseau)
const FALLBACK_FR: Catalog = {
  "login.title": "GuinéeCare",
  "login.subtitle": "Suite Hospitalière",
  "login.email": "Email",
  "login.password": "Mot de passe",
  "login.submit": "Se connecter",
  "login.connecting": "Connexion…",
  "login.error": "Identifiants invalides",
  "login.demo_link": "Utiliser les identifiants démo",
  "app.tagline": "Plateforme Hospitalière",
  "nav.dashboard": "Tableau de bord",
  "nav.patients": "Patients",
  "nav.admissions": "Admissions",
  "nav.emergency": "Urgences",
  "nav.pharmacy": "Pharmacie",
  "nav.laboratory": "Laboratoire",
  "nav.imaging": "Imagerie",
  "nav.surgery": "Bloc opératoire",
  "nav.billing": "Facturation",
  "nav.maternity": "Maternité",
  "nav.hospitalization": "Hospitalisation",
  "nav.quality": "Qualité",
  "nav.reporting": "Reporting",
  "nav.notifications": "Notifications",
  "nav.users": "Utilisateurs",
  "nav.rbac": "Rôles & Permissions",
  "nav.facilities": "Établissements",
  "nav.audit": "Audit",
  "nav.activity": "Activité",
  "nav.sms_admin": "SMS Admin",
  "nav.tasks_admin": "Tâches planifiées",
  "nav.logout": "Déconnexion",
  "nav.search": "Rechercher…",
  "nav.national": "Pilotage national",
  "nav.section.care": "SOINS",
  "nav.section.emergency": "URGENCES",
  "nav.section.services": "SERVICES",
  "nav.section.admin": "ADMIN",
  "nav.section.system": "SYSTÈME",
  "nav.section.national": "NATIONAL",
  "label.loading": "Chargement…",
  "label.patient": "Patient",
  "label.doctor": "Médecin",
  "label.type": "Type",
  "label.notes": "Notes",
  "label.category": "Catégorie",
  "label.description": "Description",
  "label.provider": "Fournisseur",
  "label.total": "Total",
  "label.email": "Email",
  "label.phone": "Téléphone",
  "label.address": "Adresse",
  "label.error": "Erreur",
  "label.success": "Succès",
  "label.no_data": "Aucune donnée",
  "label.retry": "Réessayer",
  "label.refresh": "Actualiser",
  "label.actions": "Actions",
  "label.status": "Statut",
  "label.date": "Date",
  "label.name": "Nom",
  "action.search": "Rechercher",
  "action.reset": "Réinitialiser",
  "action.previous": "Précédent",
  "action.next": "Suivant",
  "action.view": "Voir",
  "action.add": "Ajouter",
  "action.new": "Nouveau",
  "dashboard.title": "Tableau de bord",
  "patients.title": "Patients",
  "patients.search_placeholder": "Rechercher par nom, numéro, ID…",
  "patients.new": "Nouveau patient",
};

// v2.8.6 — Catalog de fallback EN intégré
const FALLBACK_EN: Catalog = {
  "login.title": "GuinéeCare",
  "login.subtitle": "Hospital Suite",
  "login.email": "Email",
  "login.password": "Password",
  "login.submit": "Sign in",
  "login.connecting": "Signing in…",
  "login.error": "Invalid credentials",
  "app.tagline": "Hospital Platform",
  "nav.dashboard": "Dashboard",
  "nav.patients": "Patients",
  "nav.admissions": "Admissions",
  "nav.emergency": "Emergency",
  "nav.pharmacy": "Pharmacy",
  "nav.laboratory": "Laboratory",
  "nav.imaging": "Imaging",
  "nav.surgery": "Surgery",
  "nav.billing": "Billing",
  "nav.maternity": "Maternity",
  "nav.hospitalization": "Hospitalization",
  "nav.quality": "Quality",
  "nav.reporting": "Reporting",
  "nav.notifications": "Notifications",
  "nav.users": "Users",
  "nav.rbac": "Roles & Permissions",
  "nav.facilities": "Facilities",
  "nav.audit": "Audit",
  "nav.activity": "Activity",
  "nav.sms_admin": "SMS Admin",
  "nav.tasks_admin": "Scheduled Tasks",
  "nav.logout": "Logout",
  "nav.search": "Search…",
  "label.loading": "Loading…",
  "label.error": "Error",
  "label.success": "Success",
  "label.no_data": "No data",
  "label.retry": "Retry",
  "label.refresh": "Refresh",
  "label.actions": "Actions",
  "label.status": "Status",
  "label.date": "Date",
  "label.name": "Name",
  "action.search": "Search",
  "action.reset": "Reset",
  "action.previous": "Previous",
  "action.next": "Next",
  "dashboard.title": "Dashboard",
  "patients.title": "Patients",
  "patients.search_placeholder": "Search by name, number, ID…",
  "patients.new": "New patient",
};

const FALLBACK_CATALOGS: Record<Locale, Catalog> = {
  fr: FALLBACK_FR,
  en: FALLBACK_EN,
};

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
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY) as Locale | null;
  if (stored && SUPPORTED_LOCALES.includes(stored)) return stored;
  const nav = navigator.language?.toLowerCase() || "";
  if (nav.startsWith("en")) return "en";
  return DEFAULT_LOCALE;
}

/** Simple {var} interpolation. Missing vars render as empty string. */
function interpolate(template: string, vars?: Record<string, string | number>): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (_, k) =>
    vars[k] !== undefined ? String(vars[k]) : ""
  );
}

/** Fetch a translation catalog from the backend with timeout + retry.
 * v2.8.7 — Cache localStorage pour éviter le re-fetch à chaque reload.
 */
const I18N_CACHE_KEY = "guineecare_i18n_cache";
const I18N_CACHE_TTL = 24 * 60 * 60 * 1000; // 24h

function loadCachedCatalog(locale: Locale): Catalog | null {
  try {
    const raw = localStorage.getItem(`${I18N_CACHE_KEY}_${locale}`);
    if (!raw) return null;
    const { catalog, timestamp } = JSON.parse(raw);
    if (Date.now() - timestamp > I18N_CACHE_TTL) return null; // expiré
    return catalog;
  } catch {
    return null;
  }
}

function saveCachedCatalog(locale: Locale, catalog: Catalog): void {
  try {
    localStorage.setItem(
      `${I18N_CACHE_KEY}_${locale}`,
      JSON.stringify({ catalog, timestamp: Date.now() })
    );
  } catch {
    // localStorage plein ou indisponible — ignorer
  }
}

async function fetchCatalog(locale: Locale): Promise<Catalog> {
  // v2.8.7 — D'abord vérifier le cache localStorage
  const cached = loadCachedCatalog(locale);
  if (cached) {
    // Retourner le cache immédiatement, refresh en arrière-plan
    fetchCatalogFromServer(locale);
    return cached;
  }
  // Pas de cache → fetch depuis le serveur
  return fetchCatalogFromServer(locale);
}

async function fetchCatalogFromServer(locale: Locale): Promise<Catalog> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const r = await fetch(`/api/v1/i18n/translations/${locale}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    const catalog = data.translations || {};
    // v2.8.7 — Sauvegarder en cache localStorage
    saveCachedCatalog(locale, catalog);
    return catalog;
  } catch (e) {
    console.warn(`[i18n] Failed to fetch catalog for ${locale}, using fallback:`, e);
    return FALLBACK_CATALOGS[locale] || FALLBACK_FR;
  }
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(detectInitialLocale);
  // v2.8.6 — Commencer avec le fallback au lieu de {} → les clés sont traduites immédiatement
  const [catalog, setCatalog] = useState<Catalog>(FALLBACK_CATALOGS[detectInitialLocale()] || FALLBACK_FR);
  const [loading, setLoading] = useState(true);

  // Fetch catalog whenever locale changes
  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    // v2.8.6 — Appliquer le fallback immédiatement (synchrone)
    setCatalog(FALLBACK_CATALOGS[locale] || FALLBACK_FR);

    // Puis fetch le catalog complet depuis le backend (async)
    fetchCatalog(locale).then((c) => {
      if (cancelled) return;
      // Merger : le catalog backend complète le fallback
      setCatalog({ ...FALLBACK_CATALOGS[locale], ...c });
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [locale]);

  const setLocale = useCallback((l: Locale) => {
    localStorage.setItem(LOCALE_STORAGE_KEY, l);
    document.documentElement.lang = l;
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
