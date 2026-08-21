/**
 * Adaptateurs API → shape d'affichage du front (#116, Slice 2).
 *
 * L'API expose des champs domaine (nom_entreprise, score_final, statut) ; les
 * composants affichent un shape présentation (CompanyData : Hot/Warm/Cold…).
 * La traduction vit ici, pas dans l'API.
 */
import type { ProspectRow } from "@/lib/api";
import type { CompanyData } from "@/components/ProspectsTable";

/** statut pipeline (qualifie/nouveau/invalide) → libellé de notation du front. */
export function scoringStatus(
  statut: string,
  score: number,
): CompanyData["scoringStatus"] {
  if (statut === "qualifie") return "Hot";
  if (statut === "invalide") return "Cold";
  // Repli par score si le statut n'est pas tranché (seuils pipeline 60 / 30).
  if (score >= 60) return "Hot";
  if (score < 30) return "Cold";
  return "Warm";
}

export function prospectToCompanyData(p: ProspectRow): CompanyData {
  const nom = p.nom_entreprise || "—";
  const location = [p.ville, p.departement].filter(Boolean).join(", ") || "—";
  return {
    id: p.id,
    companyName: nom,
    contactName: p.telephone ?? p.email ?? "—",
    location,
    logoLetter: (nom[0] ?? "?").toUpperCase(),
    logoBgColor: "bg-indigo-100 dark:bg-indigo-950",
    logoTextColor: "text-indigo-600 dark:text-indigo-400",
    nafCode: p.code_naf ?? "—",
    scoringStatus: scoringStatus(p.statut, p.score_final),
    scoringPercentage: p.score_final,
    lastContactDate: "—",
    lastContactType: p.email ? "Email" : p.telephone ? "Téléphone" : "—",
    contactable: Boolean(p.telephone || p.email),
  };
}
