import { describe, expect, it } from "vitest";
import type { IcpParseResult } from "@/lib/api";
import { mergeAiResult } from "./merge";
import { parseTarget } from "./parse";

const ia = (over: Partial<IcpParseResult> = {}): IcpParseResult => ({
  codes_naf: [],
  departements: [],
  effectif_min: null,
  effectif_max: null,
  anciennete_min_ans: null,
  exiger_site_web: false,
  exiger_email: false,
  mots_cles_positifs: [],
  mots_cles_negatifs: [],
  non_traduits: [],
  hypotheses: [],
  modele: "claude-haiku-4-5",
  depuis_cache: false,
  ...over,
});

describe("mergeAiResult", () => {
  const base = parseTarget(
    "Hôtels indépendants de 10 à 50 salariés à Paris, avec site web, sauf les chaînes",
  ).criteria;

  it("ajoute les mots-clés proposés et garde les hypothèses visibles", () => {
    const m = mergeAiResult(
      base,
      ia({ mots_cles_negatifs: ["groupe", "chaînes"], hypotheses: ["indépendants : exclusion des réseaux"] }),
    );
    expect(m.criteria.motsClesNegatifs).toEqual(["chaînes", "groupe"]);
    expect(m.hypotheses).toEqual(["IA : indépendants : exclusion des réseaux"]);
    expect(m.unmapped).toEqual([]);
  });

  it("n'écrase jamais un choix déjà fait (effectif, ancienneté)", () => {
    const m = mergeAiResult(base, ia({ effectif_min: 1, effectif_max: 9, anciennete_min_ans: 3 }));
    expect(m.criteria.effectif).toEqual({ min: 10, max: 50 });
    expect(m.criteria.ancienneteMin).toBe(3);
  });

  it("ajoute secteurs et zones sans doublon, avec libellés du lexique", () => {
    const m = mergeAiResult(base, ia({ codes_naf: ["5510Z", "5520Z", "4322B"], departements: ["75", "92"] }));
    expect(m.criteria.secteurs.map((s) => s.id)).toEqual(["hotels", "hebergement-touristique", "naf:4322B"]);
    expect(m.criteria.secteurs[2].label).toBe(
      "Travaux d'installation d'équipements thermiques et de climatisation",
    );
    expect(m.criteria.zones.map((z) => z.label)).toEqual(["75 · Paris", "92 · Hauts-de-Seine"]);
  });

  it("reprend l'effectif proposé quand il n'y en avait pas", () => {
    const m = mergeAiResult(parseTarget("hôtels à Paris").criteria, ia({ effectif_min: 10, effectif_max: null }));
    expect(m.criteria.effectif).toEqual({ min: 10, max: null });
  });
});
