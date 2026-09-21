import { describe, expect, it } from "vitest";
import { campagneStatut, prospectStatut, scoreBand } from "@/lib/statut";

describe("statuts en français", () => {
  it("traduit les 8 statuts prospect du schéma SQL", () => {
    const labels = [
      "nouveau",
      "qualifie",
      "en_attente_appel",
      "appele",
      "rdv",
      "refus",
      "absent",
      "invalide",
    ].map((s) => prospectStatut(s).label);
    expect(labels).toEqual([
      "Nouveau",
      "Qualifié",
      "À appeler",
      "Appelé",
      "RDV obtenu",
      "Refus",
      "Absent",
      "Hors cible",
    ]);
  });

  it("traduit les statuts campagne", () => {
    expect(campagneStatut("brouillon")).toEqual({ label: "Brouillon", tone: "muted" });
    expect(campagneStatut("en_cours").label).toBe("En cours");
    expect(campagneStatut("terminee").label).toBe("Terminée");
  });

  it("affiche une valeur inconnue telle quelle, en tonalité neutre", () => {
    expect(prospectStatut("autre")).toEqual({ label: "autre", tone: "muted" });
    expect(campagneStatut(null)).toEqual({ label: "—", tone: "muted" });
  });

  it("bandes de score Chaud / Tiède / Froid aux seuils 60 et 30", () => {
    expect(scoreBand(60).label).toBe("Chaud");
    expect(scoreBand(59).label).toBe("Tiède");
    expect(scoreBand(30).label).toBe("Tiède");
    expect(scoreBand(29).label).toBe("Froid");
    expect(scoreBand(null).label).toBe("Froid");
  });
});
