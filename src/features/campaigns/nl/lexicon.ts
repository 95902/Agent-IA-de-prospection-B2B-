/**
 * Lexique de ciblage (secteurs → NAF, géographie, tailles). Données vérifiées dans
 * `config/lexique_ciblage.fr.json` (INSEE + geo.api.gouv.fr) — partagées avec le
 * backend, jamais codées en dur ici.
 */
import raw from "../../../../config/lexique_ciblage.fr.json";

export type LexSecteur = {
  id: string;
  label: string;
  naf: { code: string; libelle: string }[];
  synonymes: string[];
};
export type LexDepartement = { code: string; nom: string; region: string };
export type LexRegion = { code: string; nom: string; departements: string[]; synonymes: string[] };
export type LexZone = { id: string; label: string; departements: string[]; synonymes: string[] };
export type LexVille = { nom: string; departement: string };
export type LexTaille = { id: string; label: string; min: number; max: number; synonymes: string[] };

export type Lexique = {
  version: number;
  sources: Record<string, string>;
  secteurs: LexSecteur[];
  departements: LexDepartement[];
  regions: LexRegion[];
  zones: LexZone[];
  villes: LexVille[];
  tailles: LexTaille[];
};

export const LEXIQUE = raw as Lexique;

const DEP_BY_CODE = new Map(LEXIQUE.departements.map((d) => [d.code, d]));

export function departement(code: string): LexDepartement | undefined {
  return DEP_BY_CODE.get(code.toUpperCase());
}

/** « 92 · Hauts-de-Seine » (ou le code seul s'il est inconnu). */
export function departementLabel(code: string): string {
  const d = departement(code);
  return d ? `${d.code} · ${d.nom}` : code;
}
