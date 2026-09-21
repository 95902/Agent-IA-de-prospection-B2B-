import { describe, expect, it } from "vitest";
import {
  ALL_TIME_DAYS,
  KPI_WINDOWS,
  isKpiWindow,
  kpiWindowDescription,
  sinceDaysFor,
} from "@/lib/kpiWindow";

describe("kpiWindow", () => {
  it("convertit 7 et 30 en nombre de jours", () => {
    expect(sinceDaysFor("7")).toBe(7);
    expect(sinceDaysFor("30")).toBe(30);
  });

  it("« Tout » utilise une fenêtre compatible avec since_days >= 1", () => {
    expect(sinceDaysFor("all")).toBe(ALL_TIME_DAYS);
    expect(ALL_TIME_DAYS).toBeGreaterThanOrEqual(1);
  });

  it("valide les valeurs connues seulement", () => {
    expect(isKpiWindow("7")).toBe(true);
    expect(isKpiWindow("all")).toBe(true);
    expect(isKpiWindow("90")).toBe(false);
    expect(isKpiWindow(7)).toBe(false);
    expect(isKpiWindow(undefined)).toBe(false);
  });

  it("expose trois fenêtres dans l'ordre du switch, avec libellés français", () => {
    expect(KPI_WINDOWS.map((w) => w.label)).toEqual(["7 j", "30 j", "Tout"]);
    expect(kpiWindowDescription("all")).toBe("Tout l'historique");
  });
});
