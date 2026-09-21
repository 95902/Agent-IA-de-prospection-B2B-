import { afterEach, describe, expect, it, vi } from "vitest";
import type { Campagne, Kpis, ProspectRow } from "@/lib/api";
import * as api from "@/lib/api";
import {
  aggregateProspects,
  bucketIndex,
  campaignYield,
  resolveActionable,
  resolveQualified,
  sortCampaigns,
  toCampaignStats,
} from "./stats";
import { fetchAllProspects } from "./queries";

let seq = 0;
const row = (over: Partial<ProspectRow> = {}): ProspectRow => ({
  id: `p${seq++}`,
  nom_entreprise: "HOTEL TEST",
  ville: "PARIS",
  departement: "75",
  code_naf: "55.10Z",
  score_final: 0,
  statut: "nouveau",
  telephone: null,
  email: null,
  site_web: null,
  ...over,
});

const kpis = (over: Partial<Kpis> = {}): Kpis => ({
  portee: "30 derniers jours",
  collectes: 800,
  qualifies: 115,
  taux_tel: 16.6,
  taux_email: 15.5,
  pct_qualifies: 14.4,
  score_moy_qualifies: 71.2,
  cout_estime_eur: 1.6,
  ...over,
});

afterEach(() => vi.restoreAllMocks());

describe("bucketIndex", () => {
  it("range les scores par tranches de 20, 100 inclus dans la dernière", () => {
    expect(bucketIndex(0)).toBe(0);
    expect(bucketIndex(19.9)).toBe(0);
    expect(bucketIndex(20)).toBe(1);
    expect(bucketIndex(59)).toBe(2);
    expect(bucketIndex(60)).toBe(3);
    expect(bucketIndex(100)).toBe(4);
    expect(bucketIndex(null)).toBe(0);
  });
});

describe("aggregateProspects", () => {
  it("compte qualifiés, joignables, actionnables et canaux", () => {
    const s = aggregateProspects([
      row({ score_final: 86, email: "a@h.fr", telephone: "+331", site_web: "h.fr" }),
      row({ score_final: 85, telephone: "+332" }),
      row({ score_final: 70 }), // qualifié, pas joignable
      row({ score_final: 40, email: "b@h.fr" }), // joignable, pas qualifié
      row({ score_final: 10 }),
    ]);
    expect(s).toMatchObject({
      total: 5,
      qualified: 3,
      reachable: 3,
      actionable: 2,
      email: 2,
      telephone: 2,
      site: 1,
    });
    expect(s.buckets).toEqual([1, 0, 1, 1, 2]);
  });
});

describe("resolveActionable", () => {
  const all = aggregateProspects([row({ score_final: 90, email: "x@y.fr" }), row()]);

  it("préfère l'API quand elle expose actionnables (fenêtre respectée)", () => {
    const r = resolveActionable("7", kpis({ actionnables: 12, qualifies_score: 20, collectes: 100 }), all);
    expect(r).toEqual({ actionable: 12, qualified: 20, collected: 100, allTime: false });
  });

  it("se replie sur l'agrégat et le signale hors fenêtre « Tout »", () => {
    expect(resolveActionable("all", kpis(), all)).toEqual({
      actionable: 1,
      qualified: 1,
      collected: 2,
      allTime: false,
    });
    expect(resolveActionable("30", kpis(), all)?.allTime).toBe(true);
  });

  it("renvoie null sans aucune donnée", () => {
    expect(resolveActionable("all", undefined, undefined)).toBeNull();
  });
});

describe("resolveQualified", () => {
  const all = aggregateProspects([row({ score_final: 90 }), row({ score_final: 65 })]);

  it("score de l'API > agrégat (Tout) > statut API", () => {
    expect(resolveQualified("7", kpis({ qualifies_score: 9 }), all)).toEqual({ value: 9, basis: "score" });
    expect(resolveQualified("all", kpis(), all)).toEqual({ value: 2, basis: "score" });
    expect(resolveQualified("30", kpis(), all)).toEqual({ value: 115, basis: "statut" });
    expect(resolveQualified("30", undefined, all)).toBeNull();
  });
});

describe("campagnes", () => {
  const c = (over: Partial<Campagne> = {}): Campagne => ({
    id: "c1",
    nom: "Pilote",
    statut: "brouillon",
    prospects_collectes: 0,
    prospects_qualifies: 72,
    ...over,
  });

  it("utilise les champs API quand actionnables est présent", () => {
    expect(toCampaignStats(c({ prospects_collectes: 500, actionnables: 55 }))).toMatchObject({
      collected: 500,
      actionable: 55,
    });
  });

  it("recalcule collectés/actionnables depuis les prospects (compteur API à 0)", () => {
    const s = toCampaignStats(c(), [
      row({ score_final: 80, email: "a@b.fr" }),
      row({ score_final: 70 }),
      row({ score_final: 20 }),
    ]);
    expect(s).toMatchObject({ collected: 3, qualified: 2, actionable: 1 });
  });

  it("laisse actionnable inconnu sans données", () => {
    expect(toCampaignStats(c()).actionable).toBeNull();
  });

  it("calcule le rendement et trie par actionnables", () => {
    const a = { id: "a", nom: "A", statut: "brouillon", collected: 150, qualified: 37, actionable: 29 };
    const b = { id: "b", nom: "B", statut: "brouillon", collected: 500, qualified: 72, actionable: 55 };
    const u = { id: "u", nom: "U", statut: "brouillon", collected: 0, qualified: 99, actionable: null };
    expect(campaignYield(a)).toBeCloseTo(19.33, 2);
    expect(campaignYield(u)).toBeNull();
    expect(sortCampaigns([a, u, b]).map((x) => x.id)).toEqual(["b", "a", "u"]);
  });
});

describe("fetchAllProspects", () => {
  it("parcourt toutes les pages jusqu'au total", async () => {
    const spy = vi.spyOn(api, "getProspects").mockImplementation(async ({ offset = 0 } = {}) => {
      const total = 450;
      const n = Math.min(200, total - offset);
      return { total, limit: 200, offset, items: Array.from({ length: n }, () => row()) };
    });
    const items = await fetchAllProspects("camp-1");
    expect(items).toHaveLength(450);
    expect(spy).toHaveBeenCalledTimes(3);
    expect(spy.mock.calls.map((c) => c[0]?.offset)).toEqual([0, 200, 400]);
    expect(spy.mock.calls[0][0]?.campagneId).toBe("camp-1");
  });

  it("s'arrête sur une page vide (total incohérent)", async () => {
    vi.spyOn(api, "getProspects").mockResolvedValue({ total: 999, limit: 200, offset: 0, items: [] });
    expect(await fetchAllProspects()).toEqual([]);
  });
});
