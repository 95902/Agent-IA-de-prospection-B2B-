import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { EmptyState, ErrorState } from "@/components/States";
import { Skeleton } from "@/components/ui/Skeleton";
import { ProspectRows } from "@/features/prospects/ProspectRows";
import type { ProspectRow } from "@/lib/api";
import { Panel, PanelHeader } from "./Panel";

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
  else body = <ProspectRows rows={top} />;

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
