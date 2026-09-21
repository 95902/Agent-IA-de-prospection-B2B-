/**
 * Critères → payload `POST /api/campagnes` (validé côté serveur par
 * `utils/icp_payload.py`). On reproduit ici les règles bloquantes pour afficher
 * les erreurs AVANT l'envoi.
 */
import { departement } from "./lexicon";
import type { Criteria } from "./types";

/** Borne haute « sans limite » : l'ICP exige un max (défaut 500) ; Sirene traite un max élevé comme ouvert. */
export const EFFECTIF_SANS_LIMITE = 100_000;

const NAF_RE = /^\d{4}[A-Z]$/;
const DEP_RE = /^(\d{2}|2[AB]|\d{3})$/;

export type LaunchMeta = {
  /** Client pour qui la campagne est menée (clients.nom_entreprise). */
  client: string;
  /** Ce que le client vend (clients.produit_vendu). */
  produit: string;
  /** La phrase d'origine : alimente description_icp (prompts Claude + embedding). */
  description: string;
  /** Nom de campagne ; proposé automatiquement s'il est vide. */
  nom?: string;
};

const uniq = <T,>(xs: T[]) => [...new Set(xs)];

export function allNaf(c: Criteria): string[] {
  return uniq(c.secteurs.flatMap((s) => s.naf));
}

export function allDepartements(c: Criteria): string[] {
  return uniq(c.zones.flatMap((z) => z.departements)).sort();
}

/** Libellé court d'une zone pour les textes : « Hauts-de-Seine », « Île-de-France ». */
function zoneName(label: string): string {
  return label.replace(/^\S+ · /, "").replace(/ \(.*\)$/, "");
}

export function effectifLabel(e: Criteria["effectif"]): string | null {
  if (!e || (e.min === null && e.max === null)) return null;
  if (e.min !== null && e.max !== null) return e.min === e.max ? `${e.min} salariés` : `${e.min} – ${e.max} salariés`;
  if (e.min !== null) return `${e.min}+ salariés`;
  return `jusqu'à ${e.max} salariés`;
}

/** Nom proposé : « Hôtels — Paris, Hauts-de-Seine ». */
export function campaignName(c: Criteria): string {
  const who = c.secteurs.map((s) => s.label).join(" + ") || "Tous secteurs";
  const where = c.zones.map((z) => zoneName(z.label)).join(", ") || "France entière";
  const name = `${who} — ${where}`;
  return name.length > 120 ? `${name.slice(0, 119)}…` : name;
}

export function validate(c: Criteria, meta: LaunchMeta): string[] {
  const errors: string[] = [];
  if (!meta.client.trim()) errors.push("Indiquez le client pour qui vous prospectez.");
  if (!meta.produit.trim()) errors.push("Indiquez ce que vous vendez.");
  const naf = allNaf(c);
  const deps = allDepartements(c);
  if (naf.length === 0 && deps.length === 0)
    errors.push("Ajoutez au moins un secteur ou une zone : sans cela, aucun ciblage n'est possible.");
  if (naf.some((n) => !NAF_RE.test(n))) errors.push("Un code NAF est invalide (format attendu : 5510Z).");
  if (deps.some((d) => !DEP_RE.test(d) || !departement(d))) errors.push("Un département est invalide.");
  const e = c.effectif;
  if (e) {
    if ((e.min ?? 0) < 0 || (e.max ?? 0) < 0) errors.push("L'effectif ne peut pas être négatif.");
    if (e.min !== null && e.max !== null && e.max < e.min)
      errors.push("L'effectif maximum doit être supérieur ou égal au minimum.");
  }
  if (c.ancienneteMin !== null && c.ancienneteMin < 0) errors.push("L'ancienneté ne peut pas être négative.");
  return errors;
}

/** Construit le payload ICP ; lève si `validate` renvoie des erreurs. */
export function toIcpPayload(c: Criteria, meta: LaunchMeta): Record<string, unknown> {
  const errors = validate(c, meta);
  if (errors.length) throw new Error(errors.join(" "));
  return buildPayload(c, meta);
}

/**
 * Payload sans validation (pré-remplissage du formulaire avancé, qui affichera
 * lui-même ce qui manque). Pour l'envoi à l'API, passer par `toIcpPayload`.
 */
export function buildPayload(c: Criteria, meta: LaunchMeta): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    nom_entreprise: meta.client.trim(),
    secteur: c.secteurs.map((s) => s.label).join(", ") || "Tous secteurs",
    produit_vendu: meta.produit.trim(),
    zone_intervention: c.zones.map((z) => zoneName(z.label)).join(", ") || "France entière",
    nom: meta.nom?.trim() || campaignName(c),
    description_icp: meta.description.trim() || undefined,
    codes_naf: allNaf(c),
    departements: allDepartements(c),
    exiger_site_web: c.exigerSiteWeb,
    exiger_email: c.exigerEmail,
    mots_cles_positifs: uniq(c.motsClesPositifs),
    mots_cles_negatifs: uniq(c.motsClesNegatifs),
  };
  if (c.effectif) {
    if (c.effectif.min !== null) payload.effectif_min = c.effectif.min;
    payload.effectif_max = c.effectif.max ?? EFFECTIF_SANS_LIMITE;
  }
  if (c.ancienneteMin !== null) payload.anciennete_min_ans = c.ancienneteMin;
  return payload;
}
