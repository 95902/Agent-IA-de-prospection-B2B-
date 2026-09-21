import type { ProspectRow } from "@/lib/api";

/** Seuil de qualification du pipeline (scoring_agent : qualifie à partir de 60). */
export const QUALIFIED_THRESHOLD = 60;

type Contact = Pick<ProspectRow, "email" | "telephone" | "site_web">;

const present = (value: string | null | undefined): boolean =>
  typeof value === "string" && value.trim() !== "";

/** Canaux de contact disponibles pour un prospect. */
export function reachChannels(p: Contact): {
  email: boolean;
  telephone: boolean;
  site: boolean;
} {
  return {
    email: present(p.email),
    telephone: present(p.telephone),
    site: present(p.site_web),
  };
}

/** Joignable = email OU téléphone (le site seul ne suffit pas pour contacter). */
export function isReachable(p: Contact): boolean {
  const c = reachChannels(p);
  return c.email || c.telephone;
}

export function isQualified(p: Pick<ProspectRow, "score_final">): boolean {
  return (p.score_final ?? 0) >= QUALIFIED_THRESHOLD;
}

/** Actionnable = qualifié (score ≥ 60) ET joignable : le cœur produit. */
export function isActionable(
  p: Contact & Pick<ProspectRow, "score_final">,
): boolean {
  return isQualified(p) && isReachable(p);
}
