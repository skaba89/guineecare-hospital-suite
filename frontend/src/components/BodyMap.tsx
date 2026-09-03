/**
 * BodyMap.tsx — Carte corporelle interactive
 * ============================================================================
 * Composant SVG interactif du corps humain permettant de sélectionner
 * (multi-sélection) des régions anatomiques. Inspiré des applications de
 * fitness grand public mais adapté à l'usage clinique hospitalier :
 *  - Localisation de la douleur
 *  - Marquage de lésions / plaies
 *  - Zones d'examen clinique
 *  - Sites d'injection / ponction
 *
 * Fonctionnalités :
 *  - Vue antérieure (face) / postérieure (dos) commutable
 *  - 14 régions anatomiques par vue, cliquables individuellement
 *  - Multi-sélection avec surbrillance (couleur primaire du design system)
 *  - Survol interactif (tooltip natif + halos)
 *  - Accessibilité : rôle bouton, ARIA-label, navigation clavier
 *  - Synchronisation des régions sélectionnées entre les vues (les régions
 *    qui existent sur les deux vues — membres, tête — restent cochées)
 *  - Mode lecture seule (affichage d'une sélection existante)
 *
 * Conventions :
 *  - Aucune dépendance externe — SVG inline, TypeScript strict
 *  - Utilise les variables CSS du design system (--primary, --border, etc.)
 *  - Fonctionne en mode clair ET sombre (variables CSS automatiques)
 * ============================================================================
 */

import { useMemo, useState } from "react";

// ─── Types ─────────────────────────────────────────────────────────────

export type BodyView = "anterior" | "posterior";

export type BodyRegionId =
  | "head"
  | "neck"
  | "chest"
  | "abdomen"
  | "pelvis"
  | "left_upper_arm"
  | "right_upper_arm"
  | "left_forearm"
  | "right_forearm"
  | "left_hand"
  | "right_hand"
  | "left_thigh"
  | "right_thigh"
  | "left_calf"
  | "right_calf"
  | "left_foot"
  | "right_foot"
  | "upper_back"
  | "lower_back";

interface RegionDef {
  id: BodyRegionId;
  /** Libellé en français affiché dans le tooltip et la liste */
  label: string;
  /** Vue où la région est visible — "both" si elle existe sur les deux vues */
  views: BodyView[] | "both";
  /** Path SVG (d) — coordonnées dans un viewBox 0 0 240 540 */
  d: string;
}

// ─── Catalogue des régions anatomiques ─────────────────────────────────
//
// Les chemins SVG ont été tracés à la main pour donner une silhouette
// humaine stylisée mais reconnaissable. ViewBox: 240 × 540.
// L'origine (0,0) est en haut à gauche. Le corps est centré horizontalement
// autour de x=120.
//
const REGIONS: RegionDef[] = [
  // ─── Tête ───
  {
    id: "head",
    label: "Tête / Crâne",
    views: "both",
    d: "M120 18 C138 18 152 32 152 52 C152 72 138 86 120 86 C102 86 88 72 88 52 C88 32 102 18 120 18 Z",
  },
  // ─── Cou ───
  {
    id: "neck",
    label: "Cou",
    views: "both",
    d: "M108 86 L132 86 L132 108 L108 108 Z",
  },
  // ─── Thorax (face) / Haut du dos (derrière) ───
  {
    id: "chest",
    label: "Thorax",
    views: ["anterior"],
    d: "M88 108 L152 108 C160 116 168 130 168 150 L168 200 C168 210 162 218 152 218 L88 218 C78 218 72 210 72 200 L72 150 C72 130 80 116 88 108 Z",
  },
  {
    id: "upper_back",
    label: "Haut du dos",
    views: ["posterior"],
    d: "M88 108 L152 108 C160 116 168 130 168 150 L168 200 C168 210 162 218 152 218 L88 218 C78 218 72 210 72 200 L72 150 C72 130 80 116 88 108 Z",
  },
  // ─── Abdomen (face) / Bas du dos (derrière) ───
  {
    id: "abdomen",
    label: "Abdomen",
    views: ["anterior"],
    d: "M88 218 L152 218 L152 282 L88 282 Z",
  },
  {
    id: "lower_back",
    label: "Lombaires",
    views: ["posterior"],
    d: "M88 218 L152 218 L152 282 L88 282 Z",
  },
  // ─── Bassin ───
  {
    id: "pelvis",
    label: "Bassin / Hanches",
    views: "both",
    d: "M80 282 L160 282 C168 290 172 300 172 312 L168 322 L72 322 L68 312 C68 300 72 290 80 282 Z",
  },
  // ─── Bras gauche (droit du point de vue du patient face à nous) ───
  // Note: "left" = côté gauche du patient (donc à droite sur la vue antérieure)
  {
    id: "left_upper_arm",
    label: "Bras G (haut)",
    views: "both",
    d: "M168 118 C176 120 182 128 184 140 L184 188 C184 196 178 200 172 198 L168 196 L168 150 Z",
  },
  {
    id: "right_upper_arm",
    label: "Bras D (haut)",
    views: "both",
    d: "M72 118 C64 120 58 128 56 140 L56 188 C56 196 62 200 68 198 L72 196 L72 150 Z",
  },
  {
    id: "left_forearm",
    label: "Avant-bras G",
    views: "both",
    d: "M170 200 L184 200 L188 268 L174 270 Z",
  },
  {
    id: "right_forearm",
    label: "Avant-bras D",
    views: "both",
    d: "M70 200 L56 200 L52 268 L66 270 Z",
  },
  {
    id: "left_hand",
    label: "Main G",
    views: "both",
    d: "M172 270 L190 270 L194 296 L188 304 L176 304 L170 296 Z",
  },
  {
    id: "right_hand",
    label: "Main D",
    views: "both",
    d: "M68 270 L50 270 L46 296 L52 304 L64 304 L70 296 Z",
  },
  // ─── Cuisse gauche ───
  {
    id: "left_thigh",
    label: "Cuisse G",
    views: "both",
    d: "M104 322 L148 322 L144 410 L108 410 Z",
  },
  {
    id: "right_thigh",
    label: "Cuisse D",
    views: "both",
    d: "M92 322 L48 322 L52 410 L92 410 Z",
  },
  // Note: les cuisses sont inversées car "left" du patient = droite de l'écran
  // en vue antérieure. Mais on garde la même position en vue postérieure.
  // Pour simplifier, on utilise les mêmes chemins sur les deux vues.
  {
    id: "left_calf",
    label: "Mollet G",
    views: "both",
    d: "M108 410 L144 410 L140 490 L112 490 Z",
  },
  {
    id: "right_calf",
    label: "Mollet D",
    views: "both",
    d: "M92 410 L52 410 L56 490 L92 490 Z",
  },
  {
    id: "left_foot",
    label: "Pied G",
    views: "both",
    d: "M108 490 L144 490 L150 510 L100 510 Z",
  },
  {
    id: "right_foot",
    label: "Pied D",
    views: "both",
    d: "M92 490 L52 490 L48 510 L96 510 Z",
  },
];

// ─── Index rapide par vue ──────────────────────────────────────────────

const REGIONS_BY_VIEW: Record<BodyView, RegionDef[]> = {
  anterior: REGIONS.filter((r) => r.views === "both" || r.views.includes("anterior")),
  posterior: REGIONS.filter((r) => r.views === "both" || r.views.includes("posterior")),
};

// ─── Composant principal ───────────────────────────────────────────────

export interface BodyMapProps {
  /** Régions sélectionnées (controlled component) */
  selected?: BodyRegionId[];
  /** Callback appelé à chaque changement de sélection */
  onChange?: (selected: BodyRegionId[]) => void;
  /** Vue initiale — défaut "anterior" */
  defaultView?: BodyView;
  /** Mode lecture seule — aucune interaction, juste l'affichage */
  readOnly?: boolean;
  /** Hauteur du SVG en pixels — défaut 480 */
  height?: number;
  /** Classe CSS additionnelle pour le conteneur */
  className?: string;
  /** Couleur de remplissage des régions sélectionnées — défaut var(--danger) */
  selectedColor?: string;
}

export function BodyMap({
  selected = [],
  onChange,
  defaultView = "anterior",
  readOnly = false,
  height = 480,
  className = "",
  selectedColor,
}: BodyMapProps) {
  const [view, setView] = useState<BodyView>(defaultView);
  const [hovered, setHovered] = useState<BodyRegionId | null>(null);

  const regions = useMemo(() => REGIONS_BY_VIEW[view], [view]);

  function toggleRegion(id: BodyRegionId) {
    if (readOnly || !onChange) return;
    if (selected.includes(id)) {
      onChange(selected.filter((r) => r !== id));
    } else {
      onChange([...selected, id]);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent, id: BodyRegionId) {
    if (readOnly) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleRegion(id);
    }
  }

  const width = Math.round((height * 240) / 540);

  return (
    <div className={`body-map ${className}`.trim()}>
      {/* ─── Toolbar : vue antérieure / postérieure + nb sélectionné ─── */}
      <div className="body-map-toolbar">
        <div className="body-map-view-toggle" role="tablist" aria-label="Vue du corps">
          <button
            type="button"
            role="tab"
            aria-selected={view === "anterior"}
            className={view === "anterior" ? "active" : ""}
            onClick={() => setView("anterior")}
          >
            Face
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={view === "posterior"}
            className={view === "posterior" ? "active" : ""}
            onClick={() => setView("posterior")}
          >
            Dos
          </button>
        </div>
        <div className="body-map-counter">
          {selected.length === 0
            ? "Aucune région sélectionnée"
            : `${selected.length} région${selected.length > 1 ? "s" : ""} sélectionnée${selected.length > 1 ? "s" : ""}`}
        </div>
      </div>

      {/* ─── SVG du corps ─── */}
      <div className="body-map-canvas" style={{ minHeight: height }}>
        <svg
          viewBox="0 0 240 540"
          width={width}
          height={height}
          role="group"
          aria-label={`Carte corporelle — vue ${view === "anterior" ? "antérieure" : "postérieure"}`}
          style={{ display: "block", margin: "0 auto" }}
        >
          {/* ─── Silhouette de fond (corps global) ─── */}
          <path
            d={`
              M120 18
              C138 18 152 32 152 52 C152 72 138 86 120 86 C102 86 88 72 88 52 C88 32 102 18 120 18 Z
              M108 86 L132 86 L132 108 L108 108 Z
              M88 108 L152 108 C160 116 168 130 168 150 L168 200 C168 210 162 218 152 218 L88 218 C78 218 72 210 72 200 L72 150 C72 130 80 116 88 108 Z
              M88 218 L152 218 L152 282 L88 282 Z
              M80 282 L160 282 C168 290 172 300 172 312 L168 322 L72 322 L68 312 C68 300 72 290 80 282 Z
            `}
            fill="var(--border-light)"
            stroke="var(--border)"
            strokeWidth="1"
            opacity="0.4"
          />
          {/* ─── Régions cliquables ─── */}
          {regions.map((region) => {
            const isSelected = selected.includes(region.id);
            const isHovered = hovered === region.id;
            return (
              <path
                key={`${view}-${region.id}`}
                d={region.d}
                role={readOnly ? undefined : "button"}
                tabIndex={readOnly ? -1 : 0}
                aria-label={region.label}
                aria-pressed={isSelected}
                className={[
                  "body-map-region",
                  isSelected ? "selected" : "",
                  isHovered ? "hovered" : "",
                  readOnly ? "readonly" : "",
                ].filter(Boolean).join(" ")}
                style={
                  selectedColor && isSelected
                    ? { fill: selectedColor }
                    : undefined
                }
                onClick={() => toggleRegion(region.id)}
                onKeyDown={(e) => handleKeyDown(e, region.id)}
                onMouseEnter={() => setHovered(region.id)}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(region.id)}
                onBlur={() => setHovered(null)}
              >
                <title>{`${region.label}${isSelected ? " (sélectionnée)" : ""}`}</title>
              </path>
            );
          })}
        </svg>
      </div>

      {/* ─── Liste des régions sélectionnées ─── */}
      {selected.length > 0 && (
        <div className="body-map-selected-list">
          <div className="body-map-selected-label">Régions sélectionnées :</div>
          <div className="body-map-selected-chips">
            {selected.map((id) => {
              const region = REGIONS.find((r) => r.id === id);
              if (!region) return null;
              return (
                <span key={id} className="body-map-chip">
                  {region.label}
                  {!readOnly && onChange && (
                    <button
                      type="button"
                      className="body-map-chip-remove"
                      aria-label={`Retirer ${region.label}`}
                      onClick={() => toggleRegion(id)}
                    >
                      ×
                    </button>
                  )}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Helpers exports ───────────────────────────────────────────────────

/** Récupère le libellé français d'une région par ID */
export function getRegionLabel(id: BodyRegionId): string {
  return REGIONS.find((r) => r.id === id)?.label || id;
}

/** Liste toutes les régions disponibles (toutes vues confondues) */
export function getAllRegions(): RegionDef[] {
  return REGIONS;
}

/** Convertit une liste d'IDs en libellés français (séparés par virgule) */
export function regionsToLabels(ids: BodyRegionId[]): string {
  return ids.map(getRegionLabel).join(", ");
}

/** Parse une chaîne (IDs séparés par virgule) en liste d'IDs valides */
export function parseRegions(s: string): BodyRegionId[] {
  if (!s) return [];
  const valid = new Set(REGIONS.map((r) => r.id));
  return s
    .split(",")
    .map((x) => x.trim())
    .filter((x): x is BodyRegionId => valid.has(x as BodyRegionId));
}

/** Sérialise une liste d'IDs en chaîne (IDs séparés par virgule) */
export function serializeRegions(ids: BodyRegionId[]): string {
  return ids.join(",");
}
