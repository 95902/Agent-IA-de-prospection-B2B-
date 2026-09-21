import { EmptyState, ErrorState } from "@/components/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { formatInt } from "@/lib/format";
import { cn } from "@/lib/utils";
import { SCORE_BUCKETS } from "../stats";
import { Panel, PanelHeader } from "./Panel";

const QUALIFIED_BUCKET = 3; // première tranche ≥ 60

/** Histogramme des scores (tout l'historique), seuil de qualification à 60. */
export const ScoreDistribution = ({
  buckets,
  total,
  isLoading,
  isError,
  onRetry,
  className,
}: {
  buckets: number[] | undefined;
  total: number;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  className?: string;
}) => {
  const max = Math.max(1, ...(buckets ?? [0]));

  let body;
  if (isError) body = <ErrorState onRetry={onRetry} className="h-56" />;
  else if (isLoading || !buckets) body = <Skeleton className="h-56 w-full" />;
  else if (total === 0) body = <EmptyState title="Aucun prospect scoré pour l'instant" className="h-56" />;
  else
    body = (
      <ol className="mt-4 flex h-56 items-end gap-3" aria-label="Prospects par tranche de score">
        {SCORE_BUCKETS.map((b, i) => {
          const qualified = i >= QUALIFIED_BUCKET;
          const count = buckets[i] ?? 0;
          return (
            <li key={b.label} className="contents">
              {i === QUALIFIED_BUCKET && (
                <div aria-hidden="true" className="relative flex h-full w-px justify-center">
                  <div className="h-[calc(100%-1.5rem)] border-l border-dashed border-brand" />
                  <span className="absolute top-0 left-2 text-[11px] whitespace-nowrap text-brand">
                    seuil · 60
                  </span>
                </div>
              )}
              <div className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                <span
                  className={cn(
                    "font-mono text-xs tabular-nums",
                    qualified ? "text-brand" : "text-muted-foreground",
                  )}
                >
                  {formatInt(count)}
                </span>
                <div
                  className={cn(
                    "w-full rounded-t-lg rounded-b-sm",
                    qualified ? "bg-brand-bar shadow-[0_0_24px_-4px_var(--hero-glow)]" : "bg-bar-muted",
                  )}
                  style={{ height: `${Math.max(count > 0 ? 3 : 0, (count / max) * 72)}%` }}
                />
                <span className="text-xs text-muted-foreground">
                  <span className="sr-only">Score </span>
                  {b.label}
                  <span className="sr-only"> : {formatInt(count)} prospects</span>
                </span>
              </div>
            </li>
          );
        })}
      </ol>
    );

  return (
    <Panel className={className}>
      <PanelHeader
        title="Distribution des scores"
        action={
          !isLoading && buckets ? (
            <span className="text-xs text-muted-foreground">
              {formatInt(total)} prospects
            </span>
          ) : undefined
        }
        description="Tout l'historique · un prospect est qualifié à partir de 60."
      />
      {body}
    </Panel>
  );
};
