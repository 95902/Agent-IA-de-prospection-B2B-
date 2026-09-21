import type { ProspectRow } from "@/lib/api";
import { departementLabel, LEXIQUE } from "@/features/campaigns/nl/lexicon";
import { isQualified, isReachable } from "@/lib/reachability";
import { matchesQuery } from "@/lib/text";

/** Filtres de la liste des prospects (reflétés dans l'URL : /prospects?…). */
export type ProspectFilters = {
  q?: string;
  /** Départements, séparés par des virgules dans l'URL (« 75,92 »). */
  dep?: string;
  /** Code NAF au format INSEE à point (« 55.10Z »), comme dans les prospects. */
  naf?: string;
  joignables?: boolean;
  qualifies?: boolean;
};

export const depList = (dep?: string): string[] =>
  (dep ?? "").split(",").map((d) => d.trim()).filter(Boolean);

/** Valide les paramètres d'URL (tout champ inconnu ou mal typé est ignoré). */
export function parseProspectSearch(search: Record<string, unknown>): ProspectFilters {
  const out: ProspectFilters = {};
  const str = (v: unknown) => (typeof v === "string" && v.trim() ? v.trim() : undefined);
  const bool = (v: unknown) => v === true || v === 1 || v === "1" || v === "true";
  if (str(search.q)) out.q = str(search.q);
  if (str(search.dep)) out.dep = depList(str(search.dep)).join(",");
  if (str(search.naf)) out.naf = str(search.naf);
  if (bool(search.joignables)) out.joignables = true;
  if (bool(search.qualifies)) out.qualifies = true;
  return out;
}

export function hasActiveFilters(f: ProspectFilters): boolean {
  return Boolean(f.q || f.dep || f.naf || f.joignables || f.qualifies);
}

export function filterProspects(items: ReadonlyArray<ProspectRow>, f: ProspectFilters): ProspectRow[] {
  const deps = depList(f.dep);
  return items.filter((p) => {
    if (f.q && !matchesQuery(f.q, [p.nom_entreprise, p.ville, p.code_naf])) return false;
    if (f.joignables && !isReachable(p)) return false;
    if (f.qualifies && !isQualified(p)) return false;
    if (deps.length && !deps.includes(p.departement ?? "")) return false;
    if (f.naf && p.code_naf !== f.naf) return false;
    return true;
  });
}

const NAF_LABELS = new Map(
  LEXIQUE.secteurs.flatMap((s) => s.naf.map((n) => [n.code, n.libelle] as const)),
);

export type Facet = { value: string; label: string; count: number };

/** Options de filtre tirées des données réelles (triées par fréquence). */
export function facets(items: ReadonlyArray<ProspectRow>): { departements: Facet[]; naf: Facet[] } {
  const count = (key: (p: ProspectRow) => string | null) => {
    const m = new Map<string, number>();
    for (const p of items) {
      const k = key(p);
      if (k) m.set(k, (m.get(k) ?? 0) + 1);
    }
    return [...m.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  };
  return {
    departements: count((p) => p.departement).map(([value, n]) => ({
      value,
      label: departementLabel(value),
      count: n,
    })),
    naf: count((p) => p.code_naf).map(([value, n]) => ({
      value,
      label: NAF_LABELS.has(value.replace(".", "")) ? `${value} · ${NAF_LABELS.get(value.replace(".", ""))}` : value,
      count: n,
    })),
  };
}

export function paginate<T>(items: ReadonlyArray<T>, page: number, size: number) {
  const totalPages = Math.max(1, Math.ceil(items.length / size));
  const current = Math.min(Math.max(1, page), totalPages);
  const start = (current - 1) * size;
  return {
    rows: items.slice(start, start + size),
    page: current,
    totalPages,
    from: items.length ? start + 1 : 0,
    to: Math.min(start + size, items.length),
  };
}
