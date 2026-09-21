import { Check, History } from "lucide-react";
import { EmptyState, ErrorState } from "@/components/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatInt, formatPct, ratio } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ActionableSummary } from "../stats";
import { Eyebrow, Panel } from "./Panel";

const FunnelRow = ({
  label,
  value,
  pct,
  barClass,
}: {
  label: string;
  value: number;
  pct: number;
  barClass: string;
}) => (
  <div className="flex items-center gap-3.5">
    <span className="w-28 shrink-0 text-[13px] text-muted-foreground">{label}</span>
    <div className="h-2 flex-1 overflow-hidden rounded-full bg-bar-muted">
      <div
        className={cn("h-2 rounded-full", barClass)}
        style={{ width: `${value > 0 ? Math.max(2, pct) : 0}%` }}
      />
    </div>
    <span className="w-14 shrink-0 text-right font-mono text-[13px] tabular-nums">
      {formatInt(value)}
    </span>
  </div>
);

/** Héros du tableau de bord : prospects qualifiés ET joignables. */
export const ActionableHero = ({
  summary,
  isLoading,
  isError,
  onRetry,
  className,
}: {
  summary: ActionableSummary | null;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  className?: string;
}) => {
  let body;
  if (isError && !summary) {
    body = <ErrorState onRetry={onRetry} className="flex-1" />;
  } else if (isLoading || !summary) {
    body = (
      <div className="flex flex-1 flex-col gap-4 pt-2">
        <Skeleton className="h-24 w-48" />
        <Skeleton className="h-2 w-full" />
        <Skeleton className="h-2 w-full" />
        <Skeleton className="h-2 w-full" />
      </div>
    );
  } else if (summary.collected === 0) {
    body = (
      <EmptyState title="Aucun prospect collecté sur cette période" className="flex-1">
        Choisissez « Tout » pour voir l'historique complet.
      </EmptyState>
    );
  } else {
    const { actionable, qualified, collected, allTime } = summary;
    body = (
      <>
        <div className="mt-1 flex flex-wrap items-end gap-x-4 gap-y-1">
          <span className="text-hero-glow text-7xl leading-[0.95] font-semibold tracking-tighter tabular-nums md:text-[104px]">
            {formatInt(actionable)}
          </span>
          <span className="pb-2 text-[15px] text-muted-foreground md:pb-3">
            prospects prêts à contacter
            <br />
            sur {formatInt(collected)} collectés
          </span>
        </div>
        <div className="mt-3 flex flex-col gap-2.5">
          <FunnelRow label="Collectés" value={collected} pct={100} barClass="bg-bar-muted" />
          <FunnelRow
            label="Qualifiés ≥ 60"
            value={qualified}
            pct={ratio(qualified, collected)}
            barClass="bg-brand-bar/60"
          />
          <FunnelRow
            label="Actionnables"
            value={actionable}
            pct={ratio(actionable, collected)}
            barClass="bg-brand-bar"
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {qualified > 0 && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-soft px-2.5 py-1.5 text-[13px] font-medium text-brand">
              <Check className="size-3.5" strokeWidth={2.5} aria-hidden="true" />
              {formatPct(ratio(actionable, qualified))} des qualifiés sont joignables
            </span>
          )}
          <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-1.5 text-[13px] text-muted-foreground">
            {formatPct(ratio(actionable, collected))} du total collecté
          </span>
          {allTime && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-2.5 py-1.5 text-[13px] text-muted-foreground">
              <History className="size-3.5" aria-hidden="true" />
              Calculé sur tout l'historique
            </span>
          )}
        </div>
      </>
    );
  }

  return (
    <Panel glass className={cn("gap-2 p-6 md:p-7", className)} aria-labelledby="kpi-actionnables">
      <div className="flex flex-wrap items-baseline gap-x-2">
        <Eyebrow>
          <span id="kpi-actionnables">Actionnables</span>
        </Eyebrow>
        <span className="text-xs text-muted-foreground">
          · qualifiés ≥ 60 et joignables (email ou tél.)
        </span>
      </div>
      {body}
    </Panel>
  );
};
