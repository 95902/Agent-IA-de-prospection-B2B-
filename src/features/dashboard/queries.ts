import { useQueries, useQuery } from "@tanstack/react-query";
import { getCampagnes, getKpis, getProspects, type ProspectRow } from "@/lib/api";
import { sinceDaysFor, type KpiWindow } from "@/lib/kpiWindow";
import { aggregateProspects, sortCampaigns, toCampaignStats } from "./stats";

const PAGE = 200; // maximum accepté par /api/prospects
const MAX_ROWS = 5000; // garde-fou

/** Charge toutes les pages de /api/prospects (optionnellement pour une campagne). */
export async function fetchAllProspects(campagneId?: string): Promise<ProspectRow[]> {
  const items: ProspectRow[] = [];
  let total = Infinity;
  while (items.length < total && items.length < MAX_ROWS) {
    const page = await getProspects({ campagneId, limit: PAGE, offset: items.length });
    total = page.total;
    items.push(...page.items);
    if (page.items.length === 0) break;
  }
  return items;
}

export function useKpis(window: KpiWindow) {
  const sinceDays = sinceDaysFor(window);
  return useQuery({
    queryKey: ["kpis", { sinceDays }],
    queryFn: () => getKpis({ sinceDays }),
  });
}

/** Tous les prospects (triés par score décroissant par l'API) + leur agrégat. */
export function useAllProspects() {
  return useQuery({
    queryKey: ["prospects", "all"],
    queryFn: () => fetchAllProspects(),
    select: (items) => ({ items, stats: aggregateProspects(items) }),
  });
}

/**
 * Campagnes enrichies (collectés réels, actionnables). Tant que l'API ne renvoie
 * pas `actionnables` (PR-B1), on agrège les prospects de chaque campagne.
 */
export function useCampaignStats() {
  const campagnes = useQuery({ queryKey: ["campagnes"], queryFn: getCampagnes });
  const list = campagnes.data ?? [];
  const needsFallback = list.some((c) => typeof c.actionnables !== "number");

  const perCampaign = useQueries({
    queries: needsFallback
      ? list.map((c) => ({
          queryKey: ["prospects", "all", { campagneId: c.id }],
          queryFn: () => fetchAllProspects(c.id),
        }))
      : [],
  });

  const stats = sortCampaigns(
    list.map((c, i) => toCampaignStats(c, perCampaign[i]?.data)),
  );

  return {
    data: campagnes.data ? stats : undefined,
    isLoading: campagnes.isLoading,
    isError: campagnes.isError,
    refetch: campagnes.refetch,
  };
}
