/** Formatage des nombres à la française (espaces fines, virgule décimale). */
const INT = new Intl.NumberFormat("fr-FR");
const DEC1 = new Intl.NumberFormat("fr-FR", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

export function formatInt(value: number): string {
  return INT.format(Math.round(value));
}

/** 13.24 → « 13,2 % » (espace insécable avant %). */
export function formatPct(value: number): string {
  return `${DEC1.format(value)}\u00a0%`;
}

/** Pourcentage de `part` dans `whole` ; 0 si `whole` est nul. */
export function ratio(part: number, whole: number): number {
  return whole > 0 ? (100 * part) / whole : 0;
}

/** Score 0–100 affiché avec une décimale au plus : 70.4 → « 70,4 », 86 → « 86 ». */
export function formatScore(value: number): string {
  return Number.isInteger(value) ? String(value) : DEC1.format(value);
}

const PARTICLES = new Set(["de", "du", "des", "la", "le", "les", "et", "en", "sur", "au", "aux", "a", "à"]);

/**
 * Noms Sirene en capitales → casse lisible : « SOC DE L'HOTEL DE LA BOURSE »
 * → « Soc de l'Hotel de la Bourse ». Les sigles courts (≤ 3 lettres, sans voyelle
 * ou connus) restent en capitales : SAS, SARL, SCI, EURL.
 */
const ACRONYMS = new Set(["sas", "sarl", "sci", "eurl", "sa", "snc", "sasu", "gie"]);

export function displayName(raw: string | null | undefined): string {
  if (!raw) return "—";
  return raw
    .toLowerCase()
    .split(/(\s+)/)
    .map((token, index) => {
      if (/^\s+$/.test(token)) return token;
      if (ACRONYMS.has(token)) return token.toUpperCase();
      if (index > 0 && PARTICLES.has(token)) return token;
      // « l'hotel » / « d'or » : particule élidée en minuscule, mot suivant capitalisé
      const elided = token.match(/^([ld])['’](.+)$/u);
      if (elided) {
        const [, p, rest] = elided;
        const head = index > 0 ? p : p.toUpperCase();
        return `${head}'${rest.charAt(0).toUpperCase()}${rest.slice(1)}`;
      }
      return token.replace(/(^|-)(\p{L})/gu, (_, sep: string, ch: string) => sep + ch.toUpperCase());
    })
    .join("");
}
