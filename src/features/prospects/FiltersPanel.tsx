import { RotateCcw, Zap } from "lucide-react";
import { useState } from "react";
import { Checkbox } from "@/components/ui/Checkbox";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import { depList, hasActiveFilters, type Facet, type ProspectFilters } from "./filters";

const MAX_DEPS = 8;

const Check = ({
  checked,
  onChange,
  children,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  children: React.ReactNode;
}) => (
  <label className="flex cursor-pointer items-center gap-2.5 text-sm">
    <Checkbox checked={checked} onCheckedChange={(c) => onChange(!!c)} />
    <span className="flex flex-1 items-center justify-between gap-2">{children}</span>
  </label>
);

/** Filtres de la liste des prospects ; chaque changement met à jour l'URL. */
export const FiltersPanel = ({
  filters,
  onChange,
  departements,
  naf,
  className,
}: {
  filters: ProspectFilters;
  onChange: (patch: Partial<ProspectFilters>) => void;
  departements: Facet[];
  naf: Facet[];
  className?: string;
}) => {
  const [showAllDeps, setShowAllDeps] = useState(false);
  const selected = depList(filters.dep);
  const toggleDep = (code: string, on: boolean) => {
    const next = on ? [...selected, code] : selected.filter((d) => d !== code);
    onChange({ dep: next.length ? next.join(",") : undefined });
  };
  const visibleDeps = showAllDeps ? departements : departements.slice(0, MAX_DEPS);
  const actionnables = !!filters.qualifies && !!filters.joignables;

  return (
    <aside aria-label="Filtres" className={cn("flex flex-col gap-5 rounded-[20px] border bg-card p-5", className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">Filtres</h2>
        {hasActiveFilters(filters) && (
          <button
            type="button"
            onClick={() => onChange({ q: undefined, dep: undefined, naf: undefined, joignables: undefined, qualifies: undefined })}
            className="inline-flex items-center gap-1.5 text-[13px] font-medium text-brand hover:underline"
          >
            <RotateCcw className="size-3.5" aria-hidden="true" />
            Réinitialiser
          </button>
        )}
      </div>

      <label className="flex flex-col gap-1.5 text-[13px] text-muted-foreground">
        Recherche
        <Input
          type="search"
          value={filters.q ?? ""}
          onChange={(e) => onChange({ q: e.target.value || undefined })}
          placeholder="Nom, ville ou code NAF"
        />
      </label>

      <div className="flex flex-col gap-2.5">
        <button
          type="button"
          aria-pressed={actionnables}
          onClick={() =>
            onChange(actionnables ? { qualifies: undefined, joignables: undefined } : { qualifies: true, joignables: true })
          }
          className={cn(
            "inline-flex h-9 items-center justify-center gap-2 rounded-xl text-sm font-medium transition",
            actionnables ? "bg-brand-gradient text-brand-foreground shadow-glow" : "border hover:bg-accent",
          )}
        >
          <Zap className="size-4" aria-hidden="true" />
          Actionnables uniquement
        </button>
        <Check checked={!!filters.qualifies} onChange={(v) => onChange({ qualifies: v || undefined })}>
          Qualifiés (score ≥ 60)
        </Check>
        <Check checked={!!filters.joignables} onChange={(v) => onChange({ joignables: v || undefined })}>
          Joignables (email ou tél.)
        </Check>
      </div>

      {departements.length > 0 && (
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-[13px] text-muted-foreground">Départements</legend>
          {visibleDeps.map((d) => (
            <Check key={d.value} checked={selected.includes(d.value)} onChange={(v) => toggleDep(d.value, v)}>
              <span>{d.label}</span>
              <span className="font-mono text-xs text-muted-foreground">{d.count}</span>
            </Check>
          ))}
          {departements.length > MAX_DEPS && (
            <button
              type="button"
              onClick={() => setShowAllDeps((v) => !v)}
              className="self-start text-[13px] font-medium text-brand hover:underline"
            >
              {showAllDeps ? "Moins" : `+ ${departements.length - MAX_DEPS} autres`}
            </button>
          )}
        </fieldset>
      )}

      {naf.length > 0 && (
        <label className="flex flex-col gap-1.5 text-[13px] text-muted-foreground">
          Activité (NAF)
          <select
            value={filters.naf ?? ""}
            onChange={(e) => onChange({ naf: e.target.value || undefined })}
            className="h-9 w-full rounded-lg border bg-transparent px-2.5 text-sm text-foreground outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 dark:bg-input/30"
          >
            <option value="">Toutes les activités</option>
            {naf.map((n) => (
              <option key={n.value} value={n.value}>
                {n.label} ({n.count})
              </option>
            ))}
          </select>
        </label>
      )}
    </aside>
  );
};
