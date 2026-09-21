/**
 * Fusion de la proposition « Affiner avec l'IA » dans les critères en cours : l'IA
 * n'ajoute que ce qui manque (jamais d'écrasement d'un choix déjà fait), et chaque
 * interprétation reste visible sous forme d'hypothèse préfixée « IA : ».
 */
import type { IcpParseResult } from "@/lib/api";
import { LEXIQUE, departementLabel } from "./lexicon";
import type { Criteria, SecteurCritere } from "./types";

function secteurPour(code: string): SecteurCritere {
  const secteur = LEXIQUE.secteurs.find((s) => s.naf.some((n) => n.code === code));
  if (!secteur) return { id: `naf:${code}`, label: `NAF ${code}`, naf: [code] };
  if (secteur.naf.length === 1) return { id: secteur.id, label: secteur.label, naf: [code] };
  const libelle = secteur.naf.find((n) => n.code === code)?.libelle ?? secteur.label;
  return { id: `naf:${code}`, label: libelle, naf: [code] };
}

export function mergeAiResult(
  c: Criteria,
  r: IcpParseResult,
): { criteria: Criteria; unmapped: string[]; hypotheses: string[] } {
  const secteurs = [...c.secteurs];
  const nafConnus = new Set(secteurs.flatMap((s) => s.naf));
  for (const code of r.codes_naf) {
    if (nafConnus.has(code)) continue;
    const s = secteurPour(code);
    if (!secteurs.some((x) => x.id === s.id)) secteurs.push(s);
    nafConnus.add(code);
  }

  const zones = [...c.zones];
  const depsConnus = new Set(zones.flatMap((z) => z.departements));
  for (const d of r.departements) {
    if (depsConnus.has(d)) continue;
    zones.push({ id: `dep:${d}`, label: departementLabel(d), departements: [d] });
    depsConnus.add(d);
  }

  const aiEffectif =
    r.effectif_min !== null || r.effectif_max !== null ? { min: r.effectif_min, max: r.effectif_max } : null;
  const union = (a: string[], b: string[]) => [...new Set([...a, ...b])];

  return {
    criteria: {
      secteurs,
      zones,
      effectif: c.effectif ?? aiEffectif,
      ancienneteMin: c.ancienneteMin ?? r.anciennete_min_ans,
      exigerSiteWeb: c.exigerSiteWeb || r.exiger_site_web,
      exigerEmail: c.exigerEmail || r.exiger_email,
      motsClesPositifs: union(c.motsClesPositifs, r.mots_cles_positifs),
      motsClesNegatifs: union(c.motsClesNegatifs, r.mots_cles_negatifs),
    },
    unmapped: r.non_traduits,
    hypotheses: r.hypotheses.map((h) => `IA : ${h}`),
  };
}
