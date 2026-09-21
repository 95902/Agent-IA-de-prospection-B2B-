import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  DEFAULT_PROFILE,
  PROFILE_STORAGE_KEY,
  initialsOf,
  loadProfile,
  parseProfile,
  resetProfileCache,
  updateProfile,
  useProfile,
} from "@/lib/profile";

beforeEach(() => {
  localStorage.clear();
  resetProfileCache();
  vi.restoreAllMocks();
});

describe("parseProfile", () => {
  it("retombe sur les défauts pour une entrée invalide", () => {
    expect(parseProfile(null)).toEqual(DEFAULT_PROFILE);
    expect(parseProfile("texte")).toEqual(DEFAULT_PROFILE);
  });

  it("nettoie chaque champ indépendamment", () => {
    const p = parseProfile({
      name: "  Marie Curie  ",
      role: 42,
      kpiWindow: "90",
      density: "compact",
      aurora: 250,
    });
    expect(p).toEqual({
      name: "Marie Curie",
      role: "",
      kpiWindow: DEFAULT_PROFILE.kpiWindow,
      density: "compact",
      aurora: 100,
      dernierClient: "",
      dernierProduit: "",
    });
  });

  it("tronque les textes trop longs", () => {
    expect(parseProfile({ name: "x".repeat(200) }).name).toHaveLength(80);
  });
});

describe("loadProfile", () => {
  it("résiste à un JSON corrompu", () => {
    localStorage.setItem(PROFILE_STORAGE_KEY, "{pas du json");
    expect(loadProfile()).toEqual(DEFAULT_PROFILE);
  });

  it("résiste à un storage qui lève une exception", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("SecurityError");
    });
    expect(loadProfile()).toEqual(DEFAULT_PROFILE);
  });
});

describe("initialsOf", () => {
  it("prend la première lettre du premier et du dernier mot", () => {
    expect(initialsOf("Marie Curie")).toBe("MC");
    expect(initialsOf("jean de la fontaine")).toBe("JF");
    expect(initialsOf("Ada")).toBe("A");
    expect(initialsOf("   ")).toBe("");
  });
});

describe("updateProfile / useProfile", () => {
  it("persiste et notifie les composants abonnés", () => {
    const { result } = renderHook(() => useProfile());
    expect(result.current.name).toBe("");

    act(() => {
      updateProfile({ name: "Marie Curie", kpiWindow: "7" });
    });

    expect(result.current.name).toBe("Marie Curie");
    expect(result.current.kpiWindow).toBe("7");
    expect(JSON.parse(localStorage.getItem(PROFILE_STORAGE_KEY)!)).toMatchObject({
      name: "Marie Curie",
      kpiWindow: "7",
    });
  });

  it("reste utilisable si l'écriture échoue", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });
    expect(updateProfile({ role: "Commercial" }).role).toBe("Commercial");
  });
});
