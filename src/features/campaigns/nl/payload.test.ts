import { describe, expect, it } from "vitest";
import { parseTarget } from "./parse";
import {
  EFFECTIF_SANS_LIMITE,
  campaignName,
  effectifLabel,
  toIcpPayload,
  validate,
  type LaunchMeta,
} from "./payload";
import { EMPTY_CRITERIA } from "./types";

const PHRASE =
  "Hôtels indépendants de 10 à 50 salariés à Paris et dans les Hauts-de-Seine, avec site web, sauf les chaînes";
const META: LaunchMeta = { client: "Client Test", produit: "Logiciel de réservation", description: PHRASE };

describe("toIcpPayload", () => {
  it("produit un payload conforme à utils/icp_payload.py", () => {
    const p = toIcpPayload(parseTarget(PHRASE).criteria, META);
    expect(p).toEqual({
      nom_entreprise: "Client Test",
      secteur: "Hôtels",
      produit_vendu: "Logiciel de réservation",
      zone_intervention: "Paris, Hauts-de-Seine",
      nom: "Hôtels — Paris, Hauts-de-Seine",
      description_icp: PHRASE,
      codes_naf: ["5510Z"],
      departements: ["75", "92"],
      effectif_min: 10,
      effectif_max: 50,
      exiger_site_web: true,
      exiger_email: false,
      mots_cles_positifs: [],
      mots_cles_negatifs: ["chaînes"],
    });
  });

  it("borne haute ouverte → max explicite élevé (le défaut serveur 500 casserait « 1000+ »)", () => {
    const p = toIcpPayload(parseTarget("hôtels, plus de 1000 salariés, à Paris").criteria, META);
    expect(p.effectif_min).toBe(1000);
    expect(p.effectif_max).toBe(EFFECTIF_SANS_LIMITE);
  });

  it("n'envoie ni effectif ni ancienneté quand ils ne sont pas précisés", () => {
    const p = toIcpPayload(parseTarget("hôtels à Paris").criteria, META);
    expect(p).not.toHaveProperty("effectif_min");
    expect(p).not.toHaveProperty("effectif_max");
    expect(p).not.toHaveProperty("anciennete_min_ans");
  });

  it("respecte un nom de campagne saisi", () => {
    const p = toIcpPayload(parseTarget("hôtels à Paris").criteria, { ...META, nom: "  Mon pilote  " });
    expect(p.nom).toBe("Mon pilote");
  });

  it("refuse un payload invalide", () => {
    expect(() => toIcpPayload(EMPTY_CRITERIA, META)).toThrow(/au moins un secteur ou une zone/);
  });
});

describe("validate", () => {
  it("exige client, produit et un ciblage", () => {
    expect(validate(EMPTY_CRITERIA, { client: " ", produit: "", description: "" })).toEqual([
      "Indiquez le client pour qui vous prospectez.",
      "Indiquez ce que vous vendez.",
      "Ajoutez au moins un secteur ou une zone : sans cela, aucun ciblage n'est possible.",
    ]);
  });

  it("vérifie la cohérence de l'effectif et les codes", () => {
    const c = {
      ...EMPTY_CRITERIA,
      secteurs: [{ id: "x", label: "X", naf: ["55.10Z"] }],
      zones: [{ id: "dep:20", label: "20", departements: ["20"] }],
      effectif: { min: 50, max: 10 },
    };
    const errors = validate(c, META);
    expect(errors).toContain("Un code NAF est invalide (format attendu : 5510Z).");
    expect(errors).toContain("Un département est invalide.");
    expect(errors).toContain("L'effectif maximum doit être supérieur ou égal au minimum.");
  });
});

describe("libellés", () => {
  it("nomme la campagne par secteurs et zones", () => {
    expect(campaignName(parseTarget("restaurants et bars à Lyon").criteria)).toBe(
      "Restaurants + Bars et cafés — Rhône",
    );
    expect(campaignName(EMPTY_CRITERIA)).toBe("Tous secteurs — France entière");
  });

  it("décrit l'effectif", () => {
    expect(effectifLabel({ min: 10, max: 50 })).toBe("10 – 50 salariés");
    expect(effectifLabel({ min: 10, max: null })).toBe("10+ salariés");
    expect(effectifLabel({ min: null, max: 49 })).toBe("jusqu'à 49 salariés");
    expect(effectifLabel(null)).toBeNull();
  });
});
