import { describe, expect, it } from "vitest";
import type { ProspectRow } from "@/lib/api";
import {
  facets,
  filterProspects,
  hasActiveFilters,
  paginate,
  parseProspectSearch,
} from "./filters";

let n = 0;
const row = (over: Partial<ProspectRow> = {}): ProspectRow => ({
  id: `p${n++}`,
  nom_entreprise: "HOTEL TEST",
  ville: "PARIS",
  departement: "75",
  code_naf: "55.10Z",
  score_final: 50,
  statut: "nouveau",
  telephone: null,
  email: null,
  site_web: null,
  ...over,
});

const items = [
  row({ nom_entreprise: "HOTEL CASTELBRAC", score_final: 86, email: "a@b.fr" }),
  row({ nom_entreprise: "HOTEL LANCASTER", score_final: 85, telephone: "+331" }),
  row({ nom_entreprise: "AGENCE PUB", code_naf: "73.11Z", departement: "92", ville: "BOULOGNE", score_final: 70 }),
  row({ nom_entreprise: "HOTEL DU PARC", departement: "92", score_final: 40, email: "c@d.fr" }),
];

describe("parseProspectSearch", () => {
  it("garde les paramètres valides et ignore le reste", () => {
    expect(parseProspectSearch({ q: " hôtel ", dep: "75, 92,", joignables: "1", qualifies: true, x: 1 })).toEqual({
      q: "hôtel",
      dep: "75,92",
      joignables: true,
      qualifies: true,
    });
    expect(parseProspectSearch({ q: "", joignables: "0", naf: 5 })).toEqual({});
  });
});

describe("filterProspects", () => {
  it("combine recherche, qualification, joignabilité, départements et NAF", () => {
    expect(filterProspects(items, { q: "hotel" })).toHaveLength(3);
    expect(filterProspects(items, { qualifies: true, joignables: true }).map((p) => p.nom_entreprise)).toEqual([
      "HOTEL CASTELBRAC",
      "HOTEL LANCASTER",
    ]);
    expect(filterProspects(items, { dep: "92" })).toHaveLength(2);
    expect(filterProspects(items, { naf: "73.11Z" })[0].nom_entreprise).toBe("AGENCE PUB");
    expect(filterProspects(items, {})).toHaveLength(4);
  });

  it("signale les filtres actifs", () => {
    expect(hasActiveFilters({})).toBe(false);
    expect(hasActiveFilters({ joignables: true })).toBe(true);
  });
});

describe("facets", () => {
  it("tire les options des données, triées par fréquence, avec libellés", () => {
    const f = facets(items);
    expect(f.departements).toEqual([
      { value: "75", label: "75 · Paris", count: 2 },
      { value: "92", label: "92 · Hauts-de-Seine", count: 2 },
    ]);
    expect(f.naf[0]).toEqual({ value: "55.10Z", label: "55.10Z · Hôtels et hébergement similaire", count: 3 });
    expect(f.naf[1].label).toBe("73.11Z · Activités des agences de publicité");
  });
});

describe("paginate", () => {
  const list = Array.from({ length: 23 }, (_, i) => i);

  it("découpe et borne la page demandée", () => {
    expect(paginate(list, 1, 10)).toMatchObject({ rows: list.slice(0, 10), page: 1, totalPages: 3, from: 1, to: 10 });
    expect(paginate(list, 3, 10)).toMatchObject({ page: 3, from: 21, to: 23 });
    expect(paginate(list, 99, 10).page).toBe(3);
    expect(paginate([], 1, 10)).toMatchObject({ rows: [], page: 1, totalPages: 1, from: 0, to: 0 });
  });
});

describe("facets — NAF hors lexique", () => {
  it("affiche le code seul plutôt qu'un libellé inventé", () => {
    expect(facets([row({ code_naf: "70.10Z" })]).naf[0].label).toBe("70.10Z");
  });
});
