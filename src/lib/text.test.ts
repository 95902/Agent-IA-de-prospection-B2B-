import { describe, expect, it } from "vitest";
import { matchesQuery, normalizeText } from "@/lib/text";

describe("normalizeText", () => {
  it("retire casse, accents et espaces superflus", () => {
    expect(normalizeText("  Hôtel   Élysée ")).toBe("hotel elysee");
    expect(normalizeText("ÇA")).toBe("ca");
  });
});

describe("matchesQuery", () => {
  const fields = ["HOTEL CASTELBRAC", "PARIS", "55.10Z"];

  it("accepte une requête vide", () => {
    expect(matchesQuery("", fields)).toBe(true);
    expect(matchesQuery("   ", fields)).toBe(true);
  });

  it("matche sans accents ni casse, sur n'importe quel champ", () => {
    expect(matchesQuery("hôtel castel", fields)).toBe(true);
    expect(matchesQuery("paris", fields)).toBe(true);
    expect(matchesQuery("55.10", fields)).toBe(true);
  });

  it("exige que chaque mot soit présent", () => {
    expect(matchesQuery("castelbrac lyon", fields)).toBe(false);
  });

  it("ignore les champs vides", () => {
    expect(matchesQuery("paris", [null, undefined, "Paris"])).toBe(true);
  });
});
