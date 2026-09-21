import type { Campagne, Kpis, ProspectRow } from "@/lib/api";
import type { KpiWindow } from "@/lib/kpiWindow";
import { isActionable, isQualified, isReachable, reachChannels } from "@/lib/reachability";

export const SCORE_BUCKETS = [
  { label: "0–19", min: 0 },
  { label: "20–39", min: 20 },
  { label: "40–59", min: 40 },
  { label: "60–79", min: 60 },
  { label: "80–100", min: 80 },
] as const;

/** Index de tranche (0..4) ; 100 tombe dans « 80–100 ». */
export function bucketIndex(score: number | null | undefined): number {
  const s = Math.min(100, Math.max(0, score ?? 0));
  return Math.min(SCORE_BUCKETS.length - 1, Math.floor(s / 20));
}

export type ProspectStats = {
  total: number;
  qualified: number;
  reachable: number;
  actionable: number;
  email: number;
  telephone: number;
  site: number;
  buckets: number[];
};

export function aggregateProspects(items: ReadonlyArray<ProspectRow>): ProspectStats {
  const stats: ProspectStats = {
    total: items.length,
    qualified: 0,
    reachable: 0,
    actionable: 0,
    email: 0,
    telephone: 0,
    site: 0,
    buckets: SCORE_BUCKETS.map(() => 0),
  };
  for (const p of items) {
    const c = reachChannels(p);
    if (isQualified(p)) stats.qualified++;
    if (isReachable(p)) stats.reachable++;
    if (isActionable(p)) stats.actionable++;
    if (c.email) stats.email++;
    if (c.telephone) stats.telephone++;
    if (c.site) stats.site++;
    stats.buckets[bucketIndex(p.score_final)]++;
  }
  return stats;
}

/** Chiffres du héros « Actionnables ». `allTime` = calculé hors fenêtre (repli). */
export type ActionableSummary = {
  actionable: number;
  qualified: number;
  collected: number;
  allTime: boolean;
};

/**
 * Source préférée : `/api/kpis` (fenêtre respectée) quand l'API expose `actionnables`
 * (PR-B1). Sinon, repli sur l'agrégat de tous les prospects — exact pour « Tout »,
 * signalé comme « tout l'historique » pour 7 j / 30 j.
 */
export function resolveActionable(
  window: KpiWindow,
  kpis: Kpis | undefined,
  all: ProspectStats | undefined,
): ActionableSummary | null {
  if (kpis && typeof kpis.actionnables === "number") {
    return {
      actionable: kpis.actionnables,
      qualified: kpis.qualifies_score ?? kpis.qualifies,
      collected: kpis.collectes,
      allTime: false,
    };
  }
  if (all) {
    return {
      actionable: all.actionable,
      qualified: all.qualified,
      collected: all.total,
      allTime: window !== "all",
    };
  }
  return null;
}

/** Qualifiés : par score (≥ 60) si possible, sinon le statut « qualifie » de l'API. */
export function resolveQualified(
  window: KpiWindow,
  kpis: Kpis | undefined,
  all: ProspectStats | undefined,
): { value: number; basis: "score" | "statut" } | null {
  if (kpis && typeof kpis.qualifies_score === "number") {
    return { value: kpis.qualifies_score, basis: "score" };
  }
  if (window === "all" && all) return { value: all.qualified, basis: "score" };
  if (kpis) return { value: kpis.qualifies, basis: "statut" };
  return null;
}

export type CampaignStats = {
  id: string;
  nom: string;
  statut: string;
  collected: number;
  qualified: number;
  /** null tant qu'on ne sait pas le calculer. */
  actionable: number | null;
};

/** Rendement actionnable d'une campagne, en % des collectés (null si inconnu). */
export function campaignYield(c: CampaignStats): number | null {
  if (c.actionable === null || c.collected <= 0) return null;
  return (100 * c.actionable) / c.collected;
}

/** Fusionne la campagne API avec l'agrégat de ses prospects (repli PR-B1). */
export function toCampaignStats(
  c: Campagne,
  prospects?: ReadonlyArray<ProspectRow>,
): CampaignStats {
  if (typeof c.actionnables === "number") {
    return {
      id: c.id,
      nom: c.nom,
      statut: c.statut,
      collected: c.prospects_collectes,
      qualified: c.prospects_qualifies,
      actionable: c.actionnables,
    };
  }
  if (prospects) {
    const s = aggregateProspects(prospects);
    return {
      id: c.id,
      nom: c.nom,
      statut: c.statut,
      collected: s.total,
      qualified: s.qualified,
      actionable: s.actionable,
    };
  }
  return {
    id: c.id,
    nom: c.nom,
    statut: c.statut,
    collected: c.prospects_collectes,
    qualified: c.prospects_qualifies,
    actionable: null,
  };
}

/** Tri : actionnables décroissants (inconnus à la fin), puis qualifiés. */
export function sortCampaigns(list: ReadonlyArray<CampaignStats>): CampaignStats[] {
  return [...list].sort(
    (a, b) =>
      (b.actionable ?? -1) - (a.actionable ?? -1) || b.qualified - a.qualified,
  );
}
