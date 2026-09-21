import { describe, expect, it } from "vitest";
import {
  QUALIFIED_THRESHOLD,
  isActionable,
  isQualified,
  isReachable,
  reachChannels,
} from "@/lib/reachability";

const p = (over: Partial<{ email: string | null; telephone: string | null; site_web: string | null; score_final: number }> = {}) => ({
  email: null,
  telephone: null,
  site_web: null,
  score_final: 0,
  ...over,
});

describe("reachability", () => {
  it("détecte chaque canal, en ignorant les chaînes vides", () => {
    expect(reachChannels(p({ email: "a@b.fr", site_web: "   " }))).toEqual({
      email: true,
      telephone: false,
      site: false,
    });
  });

  it("joignable = email ou téléphone, pas le site seul", () => {
    expect(isReachable(p({ email: "a@b.fr" }))).toBe(true);
    expect(isReachable(p({ telephone: "+33148747824" }))).toBe(true);
    expect(isReachable(p({ site_web: "https://hotel.fr" }))).toBe(false);
    expect(isReachable(p())).toBe(false);
  });

  it("qualifié à partir du seuil 60 inclus", () => {
    expect(QUALIFIED_THRESHOLD).toBe(60);
    expect(isQualified(p({ score_final: 60 }))).toBe(true);
    expect(isQualified(p({ score_final: 59.9 }))).toBe(false);
  });

  it("actionnable = qualifié ET joignable", () => {
    expect(isActionable(p({ score_final: 86, email: "a@b.fr" }))).toBe(true);
    expect(isActionable(p({ score_final: 86 }))).toBe(false);
    expect(isActionable(p({ score_final: 40, telephone: "+33100000000" }))).toBe(false);
  });
});
