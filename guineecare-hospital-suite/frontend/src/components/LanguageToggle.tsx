/**
 * Language toggle component — v1.3.0
 *
 * A compact dropdown that lets the user switch between supported locales.
 * Renders a globe icon + the current locale code. Clicking opens a small
 * menu with the supported locales.
 *
 * On locale change, persists the choice via the i18n provider (which
 * also stores it in localStorage) and triggers a catalog refetch.
 */
import { useState, useRef, useEffect } from "react";
import { useI18n, type Locale } from "../i18n";

const LOCALE_LABELS: Record<Locale, string> = {
  fr: "Français",
  en: "English",
};

const LOCALE_FLAGS: Record<Locale, string> = {
  fr: "🇫🇷",
  en: "🇬🇧",
};

export function LanguageToggle() {
  const { locale, setLocale, supportedLocales } = useI18n();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  return (
    <div ref={ref} style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        title="Change language"
        aria-label="Change language"
        aria-haspopup="menu"
        aria-expanded={open}
        style={{
          background: "transparent",
          border: "1px solid #e2e8f0",
          borderRadius: 6,
          padding: "4px 10px",
          cursor: "pointer",
          fontSize: 13,
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          color: "#475569",
        }}
      >
        <span aria-hidden>{LOCALE_FLAGS[locale]}</span>
        <span style={{ fontWeight: 600, textTransform: "uppercase" }}>{locale}</span>
      </button>
      {open && (
        <div
          role="menu"
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            right: 0,
            background: "white",
            border: "1px solid #e2e8f0",
            borderRadius: 6,
            boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
            zIndex: 1000,
            minWidth: 160,
            overflow: "hidden",
          }}
        >
          {supportedLocales.map((l) => (
            <button
              key={l}
              type="button"
              role="menuitemradio"
              aria-checked={l === locale}
              onClick={() => {
                setLocale(l);
                setOpen(false);
              }}
              style={{
                display: "flex",
                width: "100%",
                alignItems: "center",
                gap: 10,
                padding: "8px 12px",
                background: l === locale ? "#f0fdfa" : "transparent",
                border: "none",
                cursor: "pointer",
                fontSize: 13,
                textAlign: "left",
                color: "#1e293b",
              }}
            >
              <span aria-hidden style={{ fontSize: 16 }}>{LOCALE_FLAGS[l]}</span>
              <span>{LOCALE_LABELS[l]}</span>
              {l === locale && (
                <span style={{ marginLeft: "auto", color: "#0f766e", fontWeight: 700 }}>✓</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
