/* eslint-disable react-refresh/only-export-components */
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { EmptyState, ErrorState } from "@/components/States";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { useAllProspects } from "@/features/dashboard/queries";
import { FiltersPanel } from "@/features/prospects/FiltersPanel";
import { ProspectRows } from "@/features/prospects/ProspectRows";
import {
  facets,
  filterProspects,
  hasActiveFilters,
  paginate,
  parseProspectSearch,
  type ProspectFilters,
} from "@/features/prospects/filters";
import type { ProspectRow } from "@/lib/api";
import { formatInt } from "@/lib/format";

const PAGE_SIZE = 25;

/** Liste paginée ; la page revient à 1 quand les filtres changent (clé du parent). */
const ProspectsList = ({ rows, onReset }: { rows: ProspectRow[]; onReset?: () => void }) => {
  const [page, setPage] = useState(1);
  const p = paginate(rows, page, PAGE_SIZE);

  if (rows.length === 0) {
    return (
      <EmptyState title="Aucun prospect ne correspond à ces filtres" className="min-h-60">
        {onReset && (
          <button type="button" onClick={onReset} className="font-medium text-brand hover:underline">
            Réinitialiser les filtres
          </button>
        )}
      </EmptyState>
    );
  }
  return (
    <>
      <ProspectRows rows={p.rows} />
      <div className="flex items-center justify-between gap-3 border-t pt-3">
        <span className="text-[13px] text-muted-foreground">
          {formatInt(p.from)}–{formatInt(p.to)} sur {formatInt(rows.length)}
        </span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon-sm" disabled={p.page <= 1} onClick={() => setPage(p.page - 1)}>
            <ChevronLeft aria-hidden="true" />
            <span className="sr-only">Page précédente</span>
          </Button>
          <span className="min-w-20 text-center text-[13px] tabular-nums" aria-live="polite">
            Page {p.page} / {p.totalPages}
          </span>
          <Button
            variant="outline"
            size="icon-sm"
            disabled={p.page >= p.totalPages}
            onClick={() => setPage(p.page + 1)}
          >
            <ChevronRight aria-hidden="true" />
            <span className="sr-only">Page suivante</span>
          </Button>
        </div>
      </div>
    </>
  );
};

const Prospects = () => {
  const filters = Route.useSearch();
  const navigate = useNavigate({ from: "/prospects/" });
  const setFilters = (patch: Partial<ProspectFilters>) =>
    navigate({ search: (prev) => ({ ...prev, ...patch }), replace: true });
  const reset = () => navigate({ search: {}, replace: true });

  const all = useAllProspects();
  const items = useMemo(() => all.data?.items ?? [], [all.data]);
  const options = useMemo(() => facets(items), [items]);
  const rows = useMemo(() => filterProspects(items, filters), [items, filters]);

  return (
    <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-5 pt-2">
      <header className="flex flex-col gap-1.5">
        <h1 className="text-[32px] leading-tight font-semibold tracking-tight">Prospects</h1>
        <p className="text-sm text-muted-foreground" aria-live="polite">
          {all.data
            ? `${formatInt(rows.length)} sur ${formatInt(items.length)} · triés par score`
            : "Chargement…"}
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)] lg:items-start">
        <FiltersPanel
          filters={filters}
          onChange={setFilters}
          departements={options.departements}
          naf={options.naf}
          className="lg:sticky lg:top-0"
        />
        <section aria-label="Liste des prospects" className="flex min-w-0 flex-col gap-3 rounded-[20px] border bg-card p-5">
          {all.isError ? (
            <ErrorState onRetry={() => all.refetch()} />
          ) : all.isLoading ? (
            <div className="flex flex-col gap-3">
              {Array.from({ length: 8 }, (_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <ProspectsList
              key={JSON.stringify(filters)}
              rows={rows}
              onReset={hasActiveFilters(filters) ? reset : undefined}
            />
          )}
        </section>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/prospects/")({
  validateSearch: (search: Record<string, unknown>): ProspectFilters => parseProspectSearch(search),
  component: Prospects,
});
