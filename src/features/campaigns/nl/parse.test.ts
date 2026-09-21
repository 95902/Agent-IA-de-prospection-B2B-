import { describe, expect, it } from "vitest";
import pilote from "../../../../config/icp_hotels_pilote.json";
import agencesCom from "../../../../config/icp_agences_com.json";
import { LEXIQUE } from "./lexicon";
import { parseTarget } from "./parse";
import { allDepartements, allNaf } from "./payload";

const parse = (s: string) => {
  const r = parseTarget(s);
  return {
    ...r,
    naf: allNaf(r.criteria),
    deps: allDepartements(r.criteria),
    secteurs: r.criteria.secteurs.map((x) => x.id),
  };
};

describe("parseTarget — phrase de référence du lanceur", () => {
  const r = parse(
    "Hôtels indépendants de 10 à 50 salariés à Paris et dans les Hauts-de-Seine, avec site web, sauf les chaînes",
  );

  it("traduit secteur, zones, effectif, exigence et exclusion", () => {
    expect(r.naf).toEqual(["5510Z"]);
    expect(r.deps).toEqual(["75", "92"]);
    expect(r.criteria.effectif).toEqual({ min: 10, max: 50 });
    expect(r.criteria.exigerSiteWeb).toBe(true);
    expect(r.criteria.exigerEmail).toBe(false);
    expect(r.criteria.motsClesNegatifs).toEqual(["chaînes"]);
  });

  it("signale ce qu'il n'a pas su traduire, tel que tapé", () => {
    expect(r.unmapped).toEqual(["indépendants"]);
  });
});

describe("parseTarget — ICP réels du projet (golden)", () => {
  it("retrouve le ciblage du pilote hôtels #35 depuis sa description", () => {
    const r = parse(pilote.description_icp);
    expect(r.naf).toEqual(expect.arrayContaining(pilote.codes_naf));
    expect(r.deps).toEqual(pilote.departements);
    expect(r.criteria.effectif).toEqual({ min: pilote.effectif_min, max: pilote.effectif_max });
    expect(r.criteria.ancienneteMin).toBe(2);
  });

  it("retrouve le ciblage agences de communication depuis sa description", () => {
    const r = parse(agencesCom.description_icp);
    expect(r.naf).toEqual(agencesCom.codes_naf);
    expect(r.deps).toEqual(expect.arrayContaining(agencesCom.departements));
    expect(r.criteria.effectif).toEqual({ min: 2, max: 50 });
    expect(r.criteria.ancienneteMin).toBe(2);
    expect(r.unmapped).toEqual(expect.arrayContaining(["holding"]));
  });
});

describe("parseTarget — secteurs", () => {
  it("plusieurs secteurs, casse et accents indifférents", () => {
    expect(parse("RESTAURANTS ET BARS").secteurs).toEqual(["restaurants", "bars"]);
    expect(parse("plombiers, électriciens et maçons").naf).toEqual(["4322A", "4322B", "4321A", "4399C"]);
  });

  it("traite les tirets et apostrophes (expert-comptable, cabinets d'avocats)", () => {
    expect(parse("experts-comptables et cabinets d’avocats").secteurs).toEqual(["experts-comptables", "juridique"]);
    expect(parse("auto-écoles").naf).toEqual(["8553Z"]);
  });

  it("préfère l'expression la plus longue (restauration rapide ≠ restaurant)", () => {
    expect(parse("restauration rapide").secteurs).toEqual(["restauration-rapide"]);
  });

  it("accepte des codes NAF tapés directement", () => {
    expect(parse("5510Z").naf).toEqual(["5510Z"]);
    expect(parse("55.10Z et 68.31 Z").naf).toEqual(["5510Z", "6831Z"]);
    expect(parse("code 9999Z").criteria.secteurs[0]).toEqual({ id: "naf:9999Z", label: "NAF 9999Z", naf: ["9999Z"] });
  });

  it("un secteur exclu n'est pas ajouté comme cible", () => {
    const r = parse("restaurants sauf fast-food");
    expect(r.secteurs).toEqual(["restaurants"]);
    expect(r.criteria.motsClesNegatifs).toEqual(["fast food"]);
  });

  it("laisse les secteurs inconnus en « à vérifier »", () => {
    const r = parse("startups fintech à Nantes");
    expect(r.naf).toEqual([]);
    expect(r.deps).toEqual(["44"]);
    expect(r.unmapped).toEqual(["startups", "fintech"]);
  });
});

describe("parseTarget — géographie", () => {
  it("numéros de département annoncés (« dans le 92 », listes)", () => {
    expect(parse("hôtels dans le 92").deps).toEqual(["92"]);
    expect(parse("garages 75, 92 et 93").deps).toEqual(["75", "92", "93"]);
    expect(parse("hôtels en Corse-du-Sud et 2B").deps).toEqual(["2A", "2B"]);
  });

  it("n'invente pas de département pour un nombre isolé", () => {
    const r = parse("10 hôtels");
    expect(r.deps).toEqual([]);
    expect(r.unmapped).toEqual(["10"]);
  });

  it("régions et couronnes", () => {
    expect(parse("agences immobilières en Île-de-France").deps).toEqual(["75", "77", "78", "91", "92", "93", "94", "95"]);
    expect(parse("dentistes en petite couronne").deps).toEqual(["92", "93", "94"]);
    expect(parse("dentistes en proche couronne").deps).toEqual(["92", "93", "94"]);
    const corse = LEXIQUE.regions.find((x) => x.nom === "Corse")!;
    expect(parse("campings en Corse").deps).toEqual(corse.departements);
  });

  it("DROM : la région d'un seul département cible ce département", () => {
    expect(parse("hôtels à La Réunion").deps).toEqual(["974"]);
  });

  it("villes → département entier, avec une hypothèse explicite", () => {
    const r = parse("restaurants à Lyon et Saint-Étienne");
    expect(r.deps).toEqual(["42", "69"]);
    expect(r.assumptions.some((a) => a.startsWith("Lyon"))).toBe(true);
  });

  it("codes postaux → département", () => {
    const r = parse("garages 75011");
    expect(r.deps).toEqual(["75"]);
    expect(r.assumptions[0]).toMatch(/75011/);
  });

  it("noms de départements ambigus : seulement avec majuscule ou indice géographique", () => {
    expect(parse("hôtels dans le Nord").deps).toEqual(["59"]);
    expect(parse("hôtels dans le cher").deps).toEqual(["18"]);
    expect(parse("hôtels au nord de Paris").deps).toEqual(["75"]);
    expect(parse("hôtels pas chers dans le Var").deps).toEqual(["83"]);
    expect(parse("restaurants avec un menu pas cher").deps).toEqual([]);
  });
});

describe("parseTarget — effectif et ancienneté", () => {
  it("fourchettes sous toutes leurs formes", () => {
    expect(parse("entre 10 et 50 salariés").criteria.effectif).toEqual({ min: 10, max: 50 });
    expect(parse("10-50 salariés").criteria.effectif).toEqual({ min: 10, max: 50 });
    expect(parse("de 5 salariés à 20 salariés").criteria.effectif).toEqual({ min: 5, max: 20 });
  });

  it("bornes ouvertes", () => {
    expect(parse("plus de 10 salariés").criteria.effectif).toEqual({ min: 10, max: null });
    expect(parse("20 salariés et plus").criteria.effectif).toEqual({ min: 20, max: null });
    expect(parse("moins de 50 salariés").criteria.effectif).toEqual({ min: null, max: 49 });
    expect(parse("jusqu'à 50 salariés").criteria.effectif).toEqual({ min: null, max: 50 });
  });

  it("nombre seul : minimum, avec hypothèse", () => {
    const r = parse("hôtels de 20 salariés");
    expect(r.criteria.effectif).toEqual({ min: 20, max: null });
    expect(r.assumptions[0]).toMatch(/au moins 20/);
  });

  it("mots de taille (TPE, PME) sans écraser une fourchette explicite", () => {
    expect(parse("TPE du bâtiment").criteria.effectif).toEqual({ min: 1, max: 9 });
    expect(parse("PME").criteria.effectif).toEqual({ min: 10, max: 249 });
    expect(parse("PME de 20 à 100 salariés").criteria.effectif).toEqual({ min: 20, max: 100 });
  });

  it("ancienneté minimale", () => {
    expect(parse("créées depuis plus de 3 ans").criteria.ancienneteMin).toBe(3);
    expect(parse("5 ans d'existence").criteria.ancienneteMin).toBe(5);
  });

  it("ne confond pas effectif, ancienneté et département", () => {
    const r = parse("hôtels dans le 92 de plus de 10 salariés depuis au moins 2 ans");
    expect(r.deps).toEqual(["92"]);
    expect(r.criteria.effectif).toEqual({ min: 10, max: null });
    expect(r.criteria.ancienneteMin).toBe(2);
  });
});

describe("parseTarget — exigences et exclusions", () => {
  it("exige site et email, ensemble ou séparément", () => {
    const r = parse("avec un email et un site web");
    expect(r.criteria.exigerEmail).toBe(true);
    expect(r.criteria.exigerSiteWeb).toBe(true);
    expect(parse("ayant un site internet").criteria.exigerSiteWeb).toBe(true);
  });

  it("« sans site web » est expliqué, pas transformé en mot-clé", () => {
    const r = parse("hôtels sans site web");
    expect(r.criteria.exigerSiteWeb).toBe(false);
    expect(r.criteria.motsClesNegatifs).toEqual([]);
    expect(r.assumptions[0]).toMatch(/ignoré/);
  });

  it("plusieurs exclusions", () => {
    const r = parse("hôtels sauf les chaînes, hors franchises");
    expect(r.criteria.motsClesNegatifs).toEqual(["chaînes", "franchises"]);
  });
});

describe("parseTarget — robustesse", () => {
  it("phrase vide", () => {
    const r = parse("   ");
    expect(r.naf).toEqual([]);
    expect(r.deps).toEqual([]);
    expect(r.unmapped).toEqual([]);
  });

  it("déterministe : même entrée, même sortie", () => {
    const s = "Boulangeries et pâtisseries à Bordeaux, PME, avec email";
    expect(parseTarget(s)).toEqual(parseTarget(s));
  });
});
