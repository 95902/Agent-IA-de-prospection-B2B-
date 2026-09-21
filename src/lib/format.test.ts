import { describe, expect, it } from "vitest";
import { displayName, formatInt, formatPct, formatScore, ratio } from "@/lib/format";

describe("format fr-FR", () => {
  it("sépare les milliers avec une espace", () => {
    expect(formatInt(1200)).toMatch(/^1\s200$/u);
    expect(formatInt(122)).toBe("122");
  });

  it("affiche les pourcentages avec une décimale et une virgule", () => {
    expect(formatPct(13.24)).toBe("13,2\u00a0%");
    expect(formatPct(10)).toBe("10,0\u00a0%");
  });

  it("calcule un ratio sans diviser par zéro", () => {
    expect(ratio(122, 1200)).toBeCloseTo(10.1667, 3);
    expect(ratio(5, 0)).toBe(0);
  });

  it("formate les scores entiers sans décimale", () => {
    expect(formatScore(86)).toBe("86");
    expect(formatScore(70.4)).toBe("70,4");
  });
});

describe("displayName", () => {
  it("met en casse lisible les noms Sirene en capitales", () => {
    expect(displayName("HOTEL CASTELBRAC")).toBe("Hotel Castelbrac");
    expect(displayName("SOC DE L'HOTEL DE LA BOURSE")).toBe("Soc de l'Hotel de la Bourse");
    expect(displayName("HOTEL DES ARTS CAVAIGNAC")).toBe("Hotel des Arts Cavaignac");
  });

  it("garde les formes juridiques en capitales et gère les tirets", () => {
    expect(displayName("SAS SAINT-GERMAIN")).toBe("SAS Saint-Germain");
    expect(displayName("L'ORANGERIE")).toBe("L'Orangerie");
  });

  it("gère les valeurs vides", () => {
    expect(displayName(null)).toBe("—");
    expect(displayName("")).toBe("—");
  });
});
