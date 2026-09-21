import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { EmptyState, ErrorState } from "@/components/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatInt, formatPct } from "@/lib/format";
import { campagneStatut } from "@/lib/statut";
import { campaignYield, type CampaignStats } from "../stats";
import { Panel, PanelHeader } from "./Panel";

const COLS = "grid grid-cols-[minmax(0,1fr)_64px] gap-x-4 sm:grid-cols-[minmax(0,1fr)_72px_150px]";

/** Campagnes triées par prospects actionnables, avec leur rendement. */
export const CampaignsCard = ({
  campaigns,
  isLoading,
  isError,
  onRetry,
  className,
  showViewAll = true,
}: {
  showViewAll?: boolean;
  campaigns: CampaignStats[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  className?: string;
}) => {
  const yields = (campaigns ?? []).map(campaignYield);
  const maxYield = Math.max(1, ...yields.map((y) => y ?? 0));

  let body;
  if (isError) body = <ErrorState onRetry={onRetry} />;
  else if (isLoading || !campaigns)
    body = (
      <div className="flex flex-col gap-3 pt-2">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-11 w-full" />
        ))}
      </div>
    );
  else if (campaigns.length === 0)
    body = (
      <EmptyState title="Aucune campagne">
        <Link to="/campagnes/nouvelle" className="font-medium text-brand hover:underline">
          Créer une première campagne
        </Link>
      </EmptyState>
    );
  else
    body = (
      <div>
        <div
          className={`${COLS} px-1 pb-2 text-[11px] font-semibold tracking-[0.08em] text-muted-foreground uppercase`}
        >
          <span>Campagne</span>
          <span className="text-right">Actionn.</span>
          <span className="hidden sm:block">Rendement</span>
        </div>
        <ul>
          {campaigns.map((c, i) => {
            const y = yields[i];
            return (
              <li key={c.id} className={`${COLS} items-center border-t px-1 py-3`}>
                <span className="flex min-w-0 flex-col">
                  <span className="truncate text-sm font-medium" title={c.nom}>
                    {c.nom}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {campagneStatut(c.statut).label} · {formatInt(c.collected)} collectés
                  </span>
                </span>
                <span className="text-right font-mono text-[15px] font-medium tabular-nums">
                  {c.actionable === null ? "—" : formatInt(c.actionable)}
                </span>
                <span className="hidden items-center gap-2.5 sm:flex">
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-bar-muted">
                    <span
                      className="block h-1.5 rounded-full bg-brand-bar"
                      style={{ width: `${y === null ? 0 : (y / maxYield) * 100}%` }}
                    />
                  </span>
                  <span className="w-14 text-right font-mono text-xs text-muted-foreground tabular-nums">
                    {y === null ? "—" : formatPct(y)}
                  </span>
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    );

  return (
    <Panel className={className}>
      <PanelHeader
        title="Campagnes"
        description="Rendement = actionnables / collectés."
        action={
          showViewAll && (
          <Link
            to="/campagnes"
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-brand hover:underline"
          >
            Voir tout <ArrowRight className="size-3.5" aria-hidden="true" />
          </Link>
          )
        }
      />
      {body}
    </Panel>
  );
};
