/* eslint-disable react-refresh/only-export-components */
import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Check, Mail, MapPin, Phone, User } from "lucide-react";
import { ReachBadges } from "@/components/ReachBadges";
import { EmptyState, ErrorState } from "@/components/States";
import { StatusPill } from "@/components/StatusPill";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { Textarea } from "@/components/ui/Textarea";
import { getProspect, getProspects, postNote, postOutcome } from "@/lib/api";
import { displayName, formatScore } from "@/lib/format";
import { isReachable } from "@/lib/reachability";
import { prospectStatut } from "@/lib/statut";
import { cn } from "@/lib/utils";

const OUTCOMES = [
  { statut: "rdv", label: "RDV obtenu", className: "bg-success-soft text-success hover:bg-success/20" },
  { statut: "refus", label: "Refus", className: "bg-danger-soft text-destructive hover:bg-destructive/20" },
  { statut: "absent", label: "Absent", className: "bg-warning-soft text-warning hover:bg-warning/20" },
] as const;

const Calls = () => {
  const qc = useQueryClient();

  // File d'appel = prospects au statut « qualifié » (triés par score) ; joignables en tête.
  const queueQuery = useQuery({
    queryKey: ["prospects", { statut: "qualifie", limit: 50 }],
    queryFn: () => getProspects({ statut: "qualifie", limit: 50 }),
  });
  const queue = useMemo(() => {
    const items = queueQuery.data?.items ?? [];
    return [...items.filter(isReachable), ...items.filter((p) => !isReachable(p))];
  }, [queueQuery.data]);
  const reachableCount = queue.filter(isReachable).length;

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const activeId = selectedId ?? queue[0]?.id ?? null;

  const { data: prospect, isLoading: prospectLoading } = useQuery({
    queryKey: ["prospect", activeId],
    queryFn: () => getProspect(activeId as string),
    enabled: !!activeId,
  });

  const [note, setNote] = useState("");

  // Résultat d'appel → change le statut ; le prospect quitte la file (plus « qualifié »).
  const outcome = useMutation({
    mutationFn: (statut: string) => postOutcome(activeId as string, statut),
    onSuccess: () => {
      setSelectedId(null);
      setNote("");
      qc.invalidateQueries({ queryKey: ["prospects"] });
    },
  });
  const saveNote = useMutation({
    mutationFn: () => postNote(activeId as string, note),
    onSuccess: () => setNote(""),
  });

  return (
    <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-5 pt-2">
      <header className="flex flex-col gap-1.5">
        <h1 className="text-[32px] leading-tight font-semibold tracking-tight">Appels</h1>
        <p className="text-sm text-muted-foreground">
          Prospects qualifiés à contacter, les joignables en premier. Chaque résultat est enregistré.
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_minmax(0,1fr)] lg:items-start">
        {/* File d'appel */}
        <section aria-labelledby="file-titre" className="flex flex-col gap-3 rounded-[20px] border bg-card p-4">
          <div className="flex items-center justify-between gap-2 px-1">
            <h2 id="file-titre" className="text-base font-semibold">
              File d'appel
            </h2>
            {queueQuery.data && (
              <span className="rounded-full bg-brand-soft px-2.5 py-1 text-xs font-medium text-brand">
                {reachableCount} joignables / {queue.length}
              </span>
            )}
          </div>
          {queueQuery.isError ? (
            <ErrorState onRetry={() => queueQuery.refetch()} />
          ) : queueQuery.isLoading ? (
            Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-16 w-full" />)
          ) : queue.length === 0 ? (
            <EmptyState title="Aucun prospect qualifié à appeler">
              Les prospects apparaissent ici après le lancement d'une campagne.
            </EmptyState>
          ) : (
            <ul className="flex max-h-[70vh] flex-col gap-1.5 overflow-y-auto pr-1">
              {queue.map((p) => {
                const active = p.id === activeId;
                const reachable = isReachable(p);
                return (
                  <li key={p.id}>
                    <button
                      type="button"
                      aria-current={active}
                      onClick={() => setSelectedId(p.id)}
                      className={cn(
                        "flex w-full flex-col gap-1.5 rounded-xl border p-3 text-left transition-colors",
                        active ? "border-brand/40 bg-brand-soft" : "border-transparent hover:bg-accent/60",
                        !reachable && "opacity-60",
                      )}
                    >
                      <span className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm font-medium">{displayName(p.nom_entreprise)}</span>
                        <span className="font-mono text-sm font-medium text-brand tabular-nums">
                          {formatScore(p.score_final)}
                        </span>
                      </span>
                      <span className="flex items-center justify-between gap-2">
                        <span className="truncate text-xs text-muted-foreground">
                          {[p.ville && displayName(p.ville), p.code_naf].filter(Boolean).join(" · ")}
                        </span>
                        <ReachBadges prospect={p} className="scale-90" />
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>

        {/* Fiche du prospect sélectionné */}
        <section aria-label="Fiche du prospect" className="glass-card flex flex-col gap-5 rounded-[20px] border p-5 md:p-6">
          {!activeId ? (
            <p className="text-sm text-muted-foreground">Sélectionnez un prospect dans la file.</p>
          ) : prospectLoading || !prospect ? (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-8 w-2/3" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : (
            <>
              <div className="flex items-start gap-3">
                <span className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-brand-soft text-brand">
                  <Building2 className="size-5" aria-hidden="true" />
                </span>
                <div className="flex min-w-0 flex-col gap-1">
                  <Link
                    to="/prospects/$prospectId"
                    params={{ prospectId: prospect.id }}
                    className="text-lg leading-tight font-semibold hover:underline"
                  >
                    {displayName(prospect.nom_entreprise)}
                  </Link>
                  <span className="flex flex-wrap items-center gap-2 text-[13px] text-muted-foreground">
                    {prospect.code_naf}
                    <StatusPill value={prospectStatut(prospect.statut)} />
                  </span>
                </div>
              </div>
              <ul className="flex flex-col gap-3 text-sm">
                {prospect.nom_dirigeant && (
                  <li className="flex items-center gap-3">
                    <User className="size-4 text-muted-foreground" aria-hidden="true" />
                    {prospect.nom_dirigeant}
                  </li>
                )}
                {prospect.telephone && (
                  <li className="flex items-center gap-3">
                    <Phone className="size-4 text-brand" aria-hidden="true" />
                    <a className="font-medium hover:underline" href={`tel:${prospect.telephone}`}>
                      {prospect.telephone}
                    </a>
                  </li>
                )}
                {prospect.email && (
                  <li className="flex items-center gap-3">
                    <Mail className="size-4 text-brand" aria-hidden="true" />
                    <a className="font-medium break-all hover:underline" href={`mailto:${prospect.email}`}>
                      {prospect.email}
                    </a>
                  </li>
                )}
                <li className="flex items-center gap-3 text-muted-foreground">
                  <MapPin className="size-4" aria-hidden="true" />
                  {[prospect.adresse, prospect.code_postal, prospect.ville].filter(Boolean).join(", ") || "—"}
                </li>
              </ul>
              <div className="flex flex-col gap-2 border-t pt-4">
                <div className="flex items-baseline justify-between">
                  <span className="text-[13px] text-muted-foreground">Score</span>
                  <span className="text-2xl font-semibold tabular-nums">
                    {formatScore(prospect.score_final)}
                    <span className="text-sm font-medium text-muted-foreground"> /100</span>
                  </span>
                </div>
                {prospect.justification_llm && (
                  <p className="text-sm text-muted-foreground">« {prospect.justification_llm} »</p>
                )}
              </div>
            </>
          )}
        </section>

        {/* Résultat d'appel + notes (écrit en base via l'API) */}
        <div className="flex flex-col gap-4">
          <section aria-labelledby="resultat-titre" className="flex flex-col gap-3 rounded-[20px] border bg-card p-4">
            <h2 id="resultat-titre" className="px-1 text-base font-semibold">
              Résultat d'appel
            </h2>
            <div className="grid grid-cols-3 gap-2">
              {OUTCOMES.map((o) => (
                <button
                  key={o.statut}
                  type="button"
                  disabled={!activeId || outcome.isPending}
                  onClick={() => outcome.mutate(o.statut)}
                  className={cn(
                    "h-14 rounded-xl text-sm font-semibold transition-colors disabled:pointer-events-none disabled:opacity-50",
                    o.className,
                  )}
                >
                  {o.label}
                </button>
              ))}
            </div>
            {outcome.isError && (
              <p role="alert" className="text-center text-xs text-destructive">
                Échec : {(outcome.error as Error).message}
              </p>
            )}
          </section>
          <section aria-labelledby="notes-titre" className="flex flex-col gap-3 rounded-[20px] border bg-card p-4">
            <label id="notes-titre" htmlFor="note" className="px-1 text-base font-semibold">
              Notes
            </label>
            <Textarea
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              disabled={!activeId}
              className="min-h-32"
              placeholder="Objections, budget, calendrier…"
            />
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs text-muted-foreground" role="status">
                {saveNote.isSuccess ? (
                  <span className="inline-flex items-center gap-1 text-success">
                    <Check className="size-3.5" aria-hidden="true" /> Note enregistrée
                  </span>
                ) : saveNote.isError ? (
                  <span className="text-destructive">Échec de l'enregistrement</span>
                ) : (
                  "Remplace la note précédente."
                )}
              </span>
              <Button
                disabled={!activeId || !note.trim() || saveNote.isPending}
                onClick={() => saveNote.mutate()}
              >
                {saveNote.isPending ? "Enregistrement…" : "Enregistrer"}
              </Button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/appels")({
  component: Calls,
});
