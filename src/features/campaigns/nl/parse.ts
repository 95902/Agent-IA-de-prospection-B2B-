/**
 * Parseur DÉTERMINISTE « phrase → critères ICP » (0 crédit, 0 réseau).
 *
 * Principe : la phrase est normalisée caractère par caractère (même longueur que
 * l'original, pour pouvoir relire la casse), puis chaque motif reconnu est extrait
 * et MASQUÉ (remplacé par des espaces) pour ne jamais être compté deux fois.
 * Ordre : codes NAF explicites → exclusions → exigences → ancienneté → effectif →
 * géographie → secteurs → mots restants (non traduits, montrés à l'utilisateur).
 */
import { LEXIQUE, departement, departementLabel } from "./lexicon";
import { EMPTY_CRITERIA, type Criteria, type ParseResult, type SecteurCritere, type ZoneCritere } from "./types";

// ---------------------------------------------------------------------------
// Normalisation alignée
// ---------------------------------------------------------------------------
const BOUNDARY = "|"; // ponctuation forte : virgule, point, parenthèse…

function prepare(input: string): string {
  return input
    .normalize("NFC")
    .replace(/œ/g, "oe")
    .replace(/Œ/g, "Oe")
    .replace(/æ/g, "ae")
    .replace(/Æ/g, "Ae")
    .replace(/[’‘`´]/g, "'");
}

function normChar(c: string): string {
  const base = c.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();
  if (base.length !== 1) return " ";
  if (/[a-z0-9']/.test(base)) return base;
  if ("+<>=≥≤".includes(base)) return base;
  if (",;.:!?()[]/«»\"“”".includes(base)) return BOUNDARY;
  return " ";
}

/** Normalise un terme du lexique de la même façon que le texte. */
export function normTerm(term: string): string {
  return [...prepare(term)].map(normChar).join("").replace(/\s+/g, " ").trim();
}

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const termRe = (term: string) => new RegExp(`(?<![a-z0-9])${escapeRe(term)}(?![a-z0-9])`, "g");

class Buffer {
  readonly original: string;
  private chars: string[];

  constructor(input: string) {
    this.original = prepare(input);
    this.chars = [...this.original].map(normChar);
  }

  get text(): string {
    return this.chars.join("");
  }

  mask(start: number, end: number): void {
    for (let i = start; i < end; i++) this.chars[i] = " ";
  }

  /** Toutes les occurrences (non chevauchantes) de `re` dans le texte courant. */
  matches(re: RegExp): RegExpExecArray[] {
    const flags = re.flags.includes("g") ? re.flags : re.flags + "g";
    return [...this.text.matchAll(new RegExp(re.source, flags))];
  }

  /** Le caractère original à `index` commence-t-il par une majuscule ? */
  capitalAt(index: number): boolean {
    const c = this.original[index] ?? "";
    return c !== c.toLowerCase();
  }
}

// ---------------------------------------------------------------------------
// Tables dérivées du lexique (normalisées une fois)
// ---------------------------------------------------------------------------
const ARTICLES = new Set(["les", "le", "la", "l'", "des", "de", "du", "d'", "un", "une"]);
const STOP_BOUNDARY = new Set(["et", "avec", "dans", "en", "a", "au", "aux", "ou", "qui", "pour", "sur", "de", "du", "des", "entre", "plus", "moins", "sauf", "hors", "sans", "pas"]);

const STOPWORDS = new Set(
  (
    "le la les l de des du d un une et ou a au aux en dans sur pour avec par chez qui que dont je j nous on " +
    "veux voudrais souhaite cherche recherche chercher cibler cible ciblons viser trouver prospecter prospects prospect " +
    "clients client entreprises entreprise societes societe structures structure etablissements etablissement boites boite " +
    "commerces commerce professionnels professionnel type types secteur secteurs zone zones region regions ville villes " +
    "departement departements dept situes situees situe situee bases basees base basee implantes implantees implante " +
    "localises localisees ayant avoir ont sont est etre tous toutes tout toute leur leurs ces cette ce cet mon ma mes " +
    "notre nos votre vos plus moins tres bien aussi uniquement seulement surtout notamment environ france francais " +
    "francaises francaise salaries salarie employes effectif ans an"
  ).split(" "),
);

const AMBIGUOUS_DEP_NAMES = new Set(
  ["ain", "aube", "aude", "cher", "eure", "gard", "gers", "indre", "jura", "landes", "loire", "lot", "manche", "nord", "orne", "somme", "tarn", "var", "vienne"],
);
const GEO_CUE = /(?<![a-z0-9'])(?:dans (?:le|la|les|l')|en|du|de la|de l'|departement(?: du| de la| de l')?|dept)\s*$/;

type GeoTerm = { term: string; zone: ZoneCritere; ambiguous: boolean; assumption?: string };

function buildGeoTerms(): GeoTerm[] {
  const terms: GeoTerm[] = [];
  const depZone = (code: string): ZoneCritere => ({
    id: `dep:${code}`,
    label: departementLabel(code),
    departements: [code],
  });
  for (const z of LEXIQUE.zones) {
    const zone = { id: `zone:${z.id}`, label: `${z.label} (${z.departements.join(", ")})`, departements: z.departements };
    for (const s of z.synonymes) terms.push({ term: normTerm(s), zone, ambiguous: false });
  }
  for (const r of LEXIQUE.regions) {
    // Régions d'un seul département (DROM) : on cible directement le département.
    const zone =
      r.departements.length === 1
        ? depZone(r.departements[0])
        : { id: `reg:${r.code}`, label: `${r.nom} (${r.departements.length} dép.)`, departements: r.departements };
    for (const s of [r.nom, ...r.synonymes]) terms.push({ term: normTerm(s), zone, ambiguous: false });
  }
  for (const d of LEXIQUE.departements) {
    const t = normTerm(d.nom);
    terms.push({ term: t, zone: depZone(d.code), ambiguous: AMBIGUOUS_DEP_NAMES.has(t) });
  }
  for (const v of LEXIQUE.villes) {
    const dep = departement(v.departement);
    terms.push({
      term: normTerm(v.nom),
      zone: depZone(v.departement),
      ambiguous: false,
      assumption:
        v.nom === dep?.nom
          ? undefined
          : `${v.nom} : ciblage sur tout le département ${departementLabel(v.departement)}.`,
    });
  }
  return terms.sort((a, b) => b.term.length - a.term.length);
}

const GEO_TERMS = buildGeoTerms();

const SECTOR_TERMS = LEXIQUE.secteurs
  .flatMap((s) =>
    s.synonymes.map((syn) => ({
      term: normTerm(syn),
      secteur: { id: s.id, label: s.label, naf: s.naf.map((n) => n.code) } as SecteurCritere,
    })),
  )
  .sort((a, b) => b.term.length - a.term.length);

const NAF_TO_SECTEUR = new Map(
  LEXIQUE.secteurs.flatMap((s) => s.naf.map((n) => [n.code, s] as const)),
);

const TAILLE_TERMS = LEXIQUE.tailles
  .flatMap((t) => t.synonymes.map((syn) => ({ term: normTerm(syn), taille: t })))
  .sort((a, b) => b.term.length - a.term.length);

// ---------------------------------------------------------------------------
// Parseur
// ---------------------------------------------------------------------------
const UNIT = "(?:salaries|salarie|employes|employe|personnes|collaborateurs|etp|effectifs|effectif)";
const NUM = "(\\d{1,6})";

export function parseTarget(input: string): ParseResult {
  const buf = new Buffer(input);
  const criteria: Criteria = structuredClone(EMPTY_CRITERIA);
  const assumptions: string[] = [];
  // Position de première apparition : les critères sont rendus dans l'ordre de la phrase.
  const position = new Map<string, number>();
  const addSecteur = (s: SecteurCritere, at: number) => {
    if (!criteria.secteurs.some((x) => x.id === s.id)) criteria.secteurs.push(s);
    position.set(s.id, Math.min(position.get(s.id) ?? at, at));
  };
  const addZone = (z: ZoneCritere, at: number) => {
    if (!criteria.zones.some((x) => x.id === z.id)) criteria.zones.push(z);
    position.set(z.id, Math.min(position.get(z.id) ?? at, at));
  };
  const byPosition = (a: { id: string }, b: { id: string }) =>
    (position.get(a.id) ?? 0) - (position.get(b.id) ?? 0);

  // 0. Codes NAF tapés explicitement (5510Z, 55.10Z, 55.10 Z).
  for (const m of [...buf.original.matchAll(/(?<![0-9A-Za-z])(\d{2})\.?(\d{2}) ?([A-Za-z])(?![A-Za-z0-9])/g)]) {
    const code = `${m[1]}${m[2]}${m[3].toUpperCase()}`;
    const known = NAF_TO_SECTEUR.get(code);
    addSecteur(
      known && known.naf.length === 1
        ? { id: known.id, label: known.label, naf: [code] }
        : { id: `naf:${code}`, label: `NAF ${code}`, naf: [code] },
      m.index!,
    );
    buf.mask(m.index!, m.index! + m[0].length);
  }

  // 1. Exclusions : « sauf les chaînes », « hors franchises », « pas de … ».
  for (const m of buf.matches(/(?<![a-z0-9])(sauf|hors|excepte|exceptes|exceptees|a l'exception (?:des|de|du|d')|pas de|pas d'|sans)(?![a-z0-9])/)) {
    const start = m.index!;
    let end = start + m[0].length;
    const rest = buf.text.slice(end);
    const stop = rest.indexOf(BOUNDARY);
    const segment = stop === -1 ? rest : rest.slice(0, stop);
    // Mots gardés tels que tapés (accents compris) : le backend normalise lui-même
    // avant le matching (agents/nettoyage_agent._matche_exclusion).
    const words: { norm: string; shown: string }[] = [];
    let consumed = 0;
    for (const w of segment.matchAll(/\S+/g)) {
      const norm = w[0];
      if (words.length === 0 && ARTICLES.has(norm)) {
        consumed = w.index! + norm.length;
        continue;
      }
      if (words.length > 0 && STOP_BOUNDARY.has(norm)) break;
      if (words.length === 3) break;
      const at = end + w.index!;
      const elision = words.length === 0 && /^[ld]'/.test(norm) ? 2 : 0;
      words.push({
        norm: norm.slice(elision),
        shown: buf.original.slice(at + elision, at + norm.length).toLowerCase(),
      });
      consumed = w.index! + norm.length;
    }
    end += consumed;
    const normPhrase = words.map((w) => w.norm).join(" ");
    const phrase = words.map((w) => w.shown).join(" ");
    if (/^(site|sites|email|e mail|mail|telephone)/.test(normPhrase)) {
      assumptions.push(`« ${m[1]} ${phrase} » ignoré : on ne peut qu'exiger un canal, pas l'exclure.`);
    } else if (phrase) {
      criteria.motsClesNegatifs.push(phrase);
    }
    buf.mask(start, end);
  }

  // 2. Exigences : « avec site web », « avec un email », « avec site et email ».
  const ITEM = "(site(?: web| internet)?|sites(?: web| internet)?|email|e mail|mail|adresse (?:e mail|email|mail)|courriel|telephone)";
  for (const m of buf.matches(new RegExp(`(?<![a-z0-9])(?:avec|ayant|possedant|dote(?:e|s|es)? d')\\s+(?:(?:un|une|des|leur|son|sa)\\s+)?${ITEM}(?:\\s+(?:et|ou)\\s+(?:(?:un|une)\\s+)?${ITEM})?(?![a-z0-9])`))) {
    for (const item of [m[1], m[2]].filter(Boolean)) {
      if (item.startsWith("site")) criteria.exigerSiteWeb = true;
      else if (item === "telephone") assumptions.push("« avec téléphone » : non filtrable à la création (la joignabilité est mesurée ensuite).");
      else criteria.exigerEmail = true;
    }
    buf.mask(m.index!, m.index! + m[0].length);
  }

  // 3. Ancienneté : « plus de 2 ans », « au moins 5 ans d'existence ».
  for (const m of buf.matches(new RegExp(`(?<![a-z0-9])(?:(?:depuis|de|creees?|existant depuis)\\s+)?(?:plus de|au moins|minimum|min)\\s+(\\d{1,3})\\s+ans?(?:\\s+(?:d'existence|d'anciennete|d'activite))?(?![a-z0-9])`))) {
    criteria.ancienneteMin = Number(m[1]);
    buf.mask(m.index!, m.index! + m[0].length);
  }
  for (const m of buf.matches(/(?<![a-z0-9])(\d{1,3})\s+ans?\s+(?:d'existence|d'anciennete|d'activite)(?![a-z0-9])/)) {
    criteria.ancienneteMin = Number(m[1]);
    buf.mask(m.index!, m.index! + m[0].length);
  }

  // 4. Effectif.
  let min: number | null = null;
  let max: number | null = null;
  const take = (re: RegExp, fn: (m: RegExpExecArray) => void) => {
    for (const m of buf.matches(re)) {
      fn(m);
      buf.mask(m.index!, m.index! + m[0].length);
    }
  };
  take(new RegExp(`(?<![a-z0-9])(?:de|entre)\\s+${NUM}\\s+${UNIT}\\s+(?:a|et)\\s+${NUM}\\s+${UNIT}(?![a-z0-9])`), (m) => {
    min = Math.min(+m[1], +m[2]);
    max = Math.max(+m[1], +m[2]);
  });
  take(new RegExp(`(?<![a-z0-9])(?:(?:de|entre)\\s+)?${NUM}\\s+(?:(?:a|et|au)\\s+)?${NUM}\\s+${UNIT}(?![a-z0-9])`), (m) => {
    min = Math.min(+m[1], +m[2]);
    max = Math.max(+m[1], +m[2]);
  });
  take(new RegExp(`(?:plus de|au moins|minimum|min|>=|≥|>|superieur a|au dela de|a partir de)\\s*${NUM}\\s+${UNIT}(?![a-z0-9])`), (m) => {
    min = +m[1];
  });
  take(new RegExp(`(?<![a-z0-9])${NUM}\\s*(?:\\+|et plus|ou plus)\\s*${UNIT}(?![a-z0-9])`), (m) => {
    min = +m[1];
  });
  take(new RegExp(`(?<![a-z0-9])${NUM}\\s+${UNIT}\\s+(?:et plus|ou plus|minimum|au moins)(?![a-z0-9])`), (m) => {
    min = +m[1];
  });
  take(new RegExp(`(moins de|au plus|maximum|max|<=|≤|<|inferieur a|jusqu'a|jusqu a)\\s*${NUM}\\s+${UNIT}(?![a-z0-9])`), (m) => {
    max = m[1] === "moins de" || m[1] === "<" ? Math.max(0, +m[2] - 1) : +m[2];
  });
  take(new RegExp(`(?<![a-z0-9])${NUM}\\s+${UNIT}(?![a-z0-9])`), (m) => {
    min = +m[1];
    assumptions.push(`« ${m[1]} salariés » compris comme « au moins ${m[1]} ».`);
  });
  for (const { term, taille } of TAILLE_TERMS) {
    for (const m of buf.matches(termRe(term))) {
      min ??= taille.min;
      max ??= taille.max;
      buf.mask(m.index!, m.index! + m[0].length);
    }
  }
  if (min !== null || max !== null) criteria.effectif = { min, max };

  // 5. Géographie (termes les plus longs d'abord).
  for (const g of GEO_TERMS) {
    for (const m of buf.matches(termRe(g.term))) {
      if (g.ambiguous && !buf.capitalAt(m.index!) && !GEO_CUE.test(buf.text.slice(0, m.index!))) continue;
      addZone(g.zone, m.index!);
      if (g.assumption && !assumptions.includes(g.assumption)) assumptions.push(g.assumption);
      buf.mask(m.index!, m.index! + m[0].length);
    }
  }
  // Codes postaux (75011 → 75).
  for (const m of buf.matches(/(?<![0-9])(\d{5})(?![0-9])/)) {
    const code = m[1].startsWith("97") ? m[1].slice(0, 3) : m[1].slice(0, 2);
    if (departement(code)) {
      addZone({ id: `dep:${code}`, label: departementLabel(code), departements: [code] }, m.index!);
      assumptions.push(`Code postal ${m[1]} : ciblage sur tout le département ${departementLabel(code)}.`);
      buf.mask(m.index!, m.index! + m[0].length);
    }
  }
  // Numéros de département, s'ils sont annoncés comme tels (« dans le 92 », « 75, 92 et 93 »).
  for (const m of buf.matches(/(?<![0-9a-z])(2a|2b|97[1-6]|0[1-9]|[1-8]\d|9[0-5])(?![0-9a-z])/)) {
    const before = buf.text.slice(0, m.index!);
    const after = buf.text.slice(m.index! + m[0].length);
    const cued =
      /(?:(?<![a-z0-9'])(?:dans (?:le|les)|le|les|du|departements?|dept|deps?|en|et|ou)|\|)\s*$/.test(before) ||
      /^\s*(?:\||et|ou|$)/.test(after);
    const code = m[1].toUpperCase();
    if (!cued || !departement(code)) continue;
    addZone({ id: `dep:${code}`, label: departementLabel(code), departements: [code] }, m.index!);
    buf.mask(m.index!, m.index! + m[0].length);
  }

  // 6. Secteurs.
  for (const { term, secteur } of SECTOR_TERMS) {
    for (const m of buf.matches(termRe(term))) {
      addSecteur(secteur, m.index!);
      buf.mask(m.index!, m.index! + m[0].length);
    }
  }

  // 7. Mots restants : non traduits → à vérifier (affichés tels que tapés).
  const unmapped: string[] = [];
  for (const m of buf.text.matchAll(/[a-z0-9'+]+/g)) {
    const word = m[0].replace(/^[ld]'/, "");
    if (STOPWORDS.has(word) || (word.length < 3 && !/^\d+$/.test(word))) continue;
    const shown = buf.original.slice(m.index!, m.index! + m[0].length).replace(/^[lLdD]'/, "");
    if (!unmapped.some((u) => normTerm(u) === word)) unmapped.push(shown);
  }

  criteria.secteurs.sort(byPosition);
  criteria.zones.sort(byPosition);
  return { criteria, unmapped, assumptions };
}
