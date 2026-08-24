export const BREADCRUMBS = ["INFORMATIONS", "CIBLE", "MOTS CLEF"];

// NB : pas de "Profil LinkedIn" — le scraping LinkedIn est un NO-GO légal
// (sources publiques uniquement : SIRENE, sites d'entreprise). Cf. agents.md / LEGAL.md.
export const VERIFICATIONS = [
  "Email vérifié",
  "Téléphone valide",
  "Site web actif",
];

export const LEVEL_VALUES = ["Standard", "Elevé", "Urgent"] as const;

export const OBJECTIVE_VALUES = [
  "Génération de prospects",
  "Études de marché",
  "Recherche de partenariats",
] as const;