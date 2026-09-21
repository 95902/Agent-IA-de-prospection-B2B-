import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { ReachBadges } from "@/components/ReachBadges";
import { StatusPill } from "@/components/StatusPill";
import { EmptyState, ErrorState } from "@/components/States";
import { Skeleton } from "@/components/ui/Skeleton";
import type { ProspectRow } from "@/lib/api";
import { displayName, formatScore } from "@/lib/format";
import { prospectStatut } from "@/lib/statut";
import { Panel, PanelHeader } from "./Panel";

const COLS =
  "grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 md:grid-cols-[minmax(0,2.2fr)_90px_minmax(0,1.2fr)_120px_110px]";


/** Meilleurs prospects (score décroissant) avec leur joignabilité. */
export const TopProspects = ({
  items,
  isLoading,
  isError,
  onRetry,
  limit = 8,
}: {
  items: ProspectRow[] | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  limit?: number;
}) => {
  const top = [...(items ?? [])]
    .sort((a, b) => (b.score_final ?? 0) - (a.score_final ?? 0))
    .slice(0, limit);

  let body;
  if (isError) body = <ErrorState onRetry={onRetry} />;
  else if (isLoading || !items)
    body = (
      <div className="flex flex-col gap-3 pt-2">
        {Array.from({ length: 5 }, (_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  else if (top.length === 0) body = <EmptyState title="Aucun prospect pour l'instant" />;
  else
    body = (
      <div>
        <div
          className={`${COLS} px-2 pb-2 text-[11px] font-semibold tracking-[0.08em] text-muted-foreground uppercase`}
        >
          <span>Entreprise</span>
          <span className="hidden md:block">NAF</span>
          <span className="hidden md:block">Score</span>
          <span className="hidden md:block">Joignabilité</span>
          <span className="text-right md:text-left">Statut</span>
        </div>
        <ul>
          {top.map((p) => (
            <li key={p.id} className="border-t">
              <Link
                to="/prospects/$prospectId"
                params={{ prospectId: p.id }}
                className={`${COLS} items-center rounded-lg px-2 py-3 transition-colors hover:bg-accent/60`}
              >
                <span className="flex min-w-0 flex-col">
                  <span className="truncate text-sm font-medium">{displayName(p.nom_entreprise)}</span>
                  <span className="text-xs text-muted-foreground">
                    {[p.ville && displayName(p.ville), p.departement].filter(Boolean).join(" · ") || "—"}
                    <span className="md:hidden"> · score {formatScore(p.score_final)}</span>
                  </span>
                </span>
                <span className="hidden font-mono text-[13px] text-muted-foreground md:block">
                  {p.code_naf ?? "—"}
                </span>
                <span className="hidden items-center gap-3 md:flex">
                  <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-bar-muted">
                    <span
                      className="block h-1.5 rounded-full bg-brand-bar"
                      style={{ width: `${Math.min(100, p.score_final ?? 0)}%` }}
                    />
                  </span>
                  <span className="font-mono text-sm font-medium tabular-nums">
                    {formatScore(p.score_final)}
                  </span>
                </span>
                <ReachBadges prospect={p} className="hidden md:inline-flex" />
                <span className="text-right md:text-left">
                  <StatusPill value={prospectStatut(p.statut)} />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    );

  return (
    <Panel>
      <PanelHeader
        title="Meilleurs prospects"
        action={
          <Link
            to="/prospects"
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-brand hover:underline"
          >
            Tous les prospects <ArrowRight className="size-3.5" aria-hidden="true" />
          </Link>
        }
      />
      {body}
    </Panel>
  );
};
