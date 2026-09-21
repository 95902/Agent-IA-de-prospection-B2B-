/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { ActionableHero } from "@/features/dashboard/components/ActionableHero";
import { CampaignsCard } from "@/features/dashboard/components/CampaignsCard";
import { ScoreDistribution } from "@/features/dashboard/components/ScoreDistribution";
import { StatCard } from "@/features/dashboard/components/StatCard";
import { TopProspects } from "@/features/dashboard/components/TopProspects";
import {
  useAllProspects,
  useCampaignStats,
  useKpis,
} from "@/features/dashboard/queries";
import { resolveActionable, resolveQualified } from "@/features/dashboard/stats";
import { formatInt, formatPct, formatScore, ratio } from "@/lib/format";
import { KPI_WINDOWS, kpiWindowDescription } from "@/lib/kpiWindow";
import { updateProfile, useProfile } from "@/lib/profile";

const Dashboard = () => {
  const { kpiWindow } = useProfile();
  const kpis = useKpis(kpiWindow);
  const all = useAllProspects();
  const campaigns = useCampaignStats();

  const allStats = all.data?.stats;
  const actionable = resolveActionable(kpiWindow, kpis.data, allStats);
  const qualified = resolveQualified(kpiWindow, kpis.data, allStats);
  const k = kpis.data;
  // Joignables = email OU tél. : champ API (PR-B1), sinon agrégat exact pour « Tout ».
  const reachablePct =
    k && typeof k.joignables === "number"
      ? ratio(k.joignables, k.collectes)
      : kpiWindow === "all" && allStats
        ? ratio(allStats.reachable, allStats.total)
        : null;

  const subtitle = [
    kpiWindowDescription(kpiWindow),
    campaigns.data && `${campaigns.data.length} campagnes`,
    k && `${formatInt(k.collectes)} entreprises analysées`,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-5">
      <header className="flex flex-col gap-4 pt-2 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[32px] leading-tight font-semibold tracking-tight">
            Tableau de bord
          </h1>
          <p className="text-sm text-muted-foreground">{subtitle || "Chargement…"}</p>
        </div>
        <SegmentedControl
          label="Période des indicateurs"
          options={KPI_WINDOWS}
          value={kpiWindow}
          onChange={(w) => updateProfile({ kpiWindow: w })}
          className="self-start md:self-auto"
        />
      </header>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ActionableHero
          summary={actionable}
          isLoading={kpis.isLoading && all.isLoading}
          isError={kpis.isError && all.isError}
          onRetry={() => {
            kpis.refetch();
            all.refetch();
          }}
          className="md:col-span-2 xl:row-span-2"
        />
        <StatCard
          label="Collectés"
          isLoading={kpis.isLoading}
          value={k ? formatInt(k.collectes) : "—"}
          sub="entreprises Sirene analysées"
        />
        <StatCard
          label={qualified?.basis === "statut" ? "Qualifiés" : "Qualifiés ≥ 60"}
          isLoading={kpis.isLoading && !qualified}
          value={qualified ? formatInt(qualified.value) : "—"}
          sub={
            qualified && k
              ? qualified.basis === "score"
                ? `${formatPct(ratio(qualified.value, k.collectes))} des collectés`
                : "statut « qualifié » (hors appels traités)"
              : undefined
          }
        />
        <StatCard
          label="Joignabilité"
          isLoading={kpis.isLoading}
          value={reachablePct === null ? "—" : formatPct(reachablePct)}
          sub={
            k
              ? `email ${formatPct(k.taux_email)} · tél. ${formatPct(k.taux_tel)}`
              : undefined
          }
        />
        <StatCard
          label="Score moyen"
          isLoading={kpis.isLoading}
          value={
            k?.score_moy_qualifies != null ? (
              <>
                {formatScore(k.score_moy_qualifies)}
                <span className="text-lg font-medium text-muted-foreground"> /100</span>
              </>
            ) : (
              "—"
            )
          }
          sub="des prospects qualifiés"
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-12">
        <ScoreDistribution
          className="xl:col-span-5"
          buckets={allStats?.buckets}
          total={allStats?.total ?? 0}
          isLoading={all.isLoading}
          isError={all.isError}
          onRetry={() => all.refetch()}
        />
        <CampaignsCard
          className="xl:col-span-7"
          campaigns={campaigns.data}
          isLoading={campaigns.isLoading}
          isError={campaigns.isError}
          onRetry={() => campaigns.refetch()}
        />
      </div>

      <TopProspects
        items={all.data?.items}
        isLoading={all.isLoading}
        isError={all.isError}
        onRetry={() => all.refetch()}
      />
    </div>
  );
};

export const Route = createFileRoute("/")({
  component: Dashboard,
});
