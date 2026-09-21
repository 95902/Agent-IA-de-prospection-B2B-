import { Link } from "@tanstack/react-router";
import { ReachBadges } from "@/components/ReachBadges";
import { StatusPill } from "@/components/StatusPill";
import type { ProspectRow } from "@/lib/api";
import { displayName, formatScore } from "@/lib/format";
import { prospectStatut, scoreBand } from "@/lib/statut";
import { cn } from "@/lib/utils";

const COLS =
  "grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 md:grid-cols-[minmax(0,2.2fr)_90px_minmax(0,1.2fr)_120px_110px]";

const BAR: Record<string, string> = {
  brand: "bg-brand-bar",
  warning: "bg-warning/70",
  muted: "bg-muted-foreground/40",
};

/** En-tête + lignes cliquables d'une liste de prospects (score, joignabilité, statut). */
export const ProspectRows = ({ rows }: { rows: ReadonlyArray<ProspectRow> }) => (
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
      {rows.map((p) => {
        const band = scoreBand(p.score_final);
        return (
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
              <span className="hidden items-center gap-3 md:flex" title={`${band.label} (${formatScore(p.score_final)}/100)`}>
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-bar-muted">
                  <span
                    className={cn("block h-1.5 rounded-full", BAR[band.tone] ?? BAR.muted)}
                    style={{ width: `${Math.min(100, p.score_final ?? 0)}%` }}
                  />
                </span>
                <span className="font-mono text-sm font-medium tabular-nums">{formatScore(p.score_final)}</span>
              </span>
              <ReachBadges prospect={p} className="hidden md:inline-flex" />
              <span className="text-right md:text-left">
                <StatusPill value={prospectStatut(p.statut)} />
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  </div>
);
