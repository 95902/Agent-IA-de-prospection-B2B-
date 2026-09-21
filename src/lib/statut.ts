/** Libellés français et tonalités visuelles des statuts (prospects, campagnes, scores). */
export type Tone = "brand" | "success" | "warning" | "danger" | "info" | "muted";

export type Labelled = { label: string; tone: Tone };

// Valeurs du CHECK SQL prospects.statut (docker/postgres/init/01_schema.sql).
const PROSPECT_STATUTS: Record<string, Labelled> = {
  nouveau: { label: "Nouveau", tone: "muted" },
  qualifie: { label: "Qualifié", tone: "brand" },
  en_attente_appel: { label: "À appeler", tone: "info" },
  appele: { label: "Appelé", tone: "info" },
  rdv: { label: "RDV obtenu", tone: "success" },
  refus: { label: "Refus", tone: "danger" },
  absent: { label: "Absent", tone: "warning" },
  invalide: { label: "Hors cible", tone: "muted" },
};

// Valeurs du CHECK SQL campagnes.statut.
const CAMPAGNE_STATUTS: Record<string, Labelled> = {
  brouillon: { label: "Brouillon", tone: "muted" },
  en_cours: { label: "En cours", tone: "brand" },
  terminee: { label: "Terminée", tone: "success" },
  annulee: { label: "Annulée", tone: "danger" },
};

const unknown = (value: string | null | undefined): Labelled => ({
  label: value?.trim() ? value : "—",
  tone: "muted",
});

export function prospectStatut(statut: string | null | undefined): Labelled {
  return (statut && PROSPECT_STATUTS[statut]) || unknown(statut);
}

export function campagneStatut(statut: string | null | undefined): Labelled {
  return (statut && CAMPAGNE_STATUTS[statut]) || unknown(statut);
}

/** Bande de score (seuils pipeline 60 / 30) : Chaud / Tiède / Froid. */
export function scoreBand(score: number | null | undefined): Labelled {
  const s = score ?? 0;
  if (s >= 60) return { label: "Chaud", tone: "brand" };
  if (s >= 30) return { label: "Tiède", tone: "warning" };
  return { label: "Froid", tone: "muted" };
}

/** Classes Tailwind (tokens) d'une pastille selon sa tonalité. */
export const TONE_CLASSES: Record<Tone, string> = {
  brand: "bg-brand-soft text-brand",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  danger: "bg-danger-soft text-destructive",
  info: "bg-info/10 text-info",
  muted: "bg-muted text-muted-foreground",
};
