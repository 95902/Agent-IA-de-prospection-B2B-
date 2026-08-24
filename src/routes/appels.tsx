/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getProspect, getProspects, postNote, postOutcome } from "@/lib/api";
import { Building2, Mail, MapPin, Phone, User } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import { Card } from "@/components/ui/Card";

const Calls = () => {
  const qc = useQueryClient();

  // File d'attente = prospects qualifiés réels (triés par score).
  const { data: page } = useQuery({
    queryKey: ["prospects", { statut: "qualifie", limit: 50 }],
    queryFn: () => getProspects({ statut: "qualifie", limit: 50 }),
  });
  const queue = page?.items ?? [];
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const activeId = selectedId ?? queue[0]?.id ?? null;

  const { data: prospect } = useQuery({
    queryKey: ["prospect", activeId],
    queryFn: () => getProspect(activeId as string),
    enabled: !!activeId,
  });

  const [note, setNote] = useState("");

  // Résultat d'appel → change le statut ; le prospect quitte la file (plus 'qualifie').
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

  const busy = outcome.isPending;

  return (
    <div className="w-full lg:h-full flex flex-col lg:flex-row gap-4">
      {/* File d'attente réelle */}
      <Card className="w-full lg:w-1/3 border rounded-lg h-full flex flex-col">
        <div className="w-full rounded-t flex justify-between items-center bg-muted/40 border-b-2 p-4">
          <p className="text-xl">FILE D'ATTENTE</p>
          <div className="bg-blue-100 rounded-lg px-2 p-1 border border-blue-300 text-blue-700">
            {queue.length} qualifiés
          </div>
        </div>
        <div className="w-full flex flex-col flex-1 p-4 gap-2 overflow-y-scroll">
          {queue.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setSelectedId(p.id)}
              className={`text-left rounded-lg p-3 border transition-colors ${
                p.id === activeId
                  ? "bg-blue-100 border-blue-300"
                  : "hover:bg-muted/50 border-transparent"
              }`}
            >
              <div className="flex justify-between items-center gap-2">
                <p className="font-bold truncate">{p.nom_entreprise}</p>
                <span className="text-sm font-bold text-emerald-600">
                  {p.score_final}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {p.code_naf} · {p.ville ?? "—"} ·{" "}
                {p.telephone || p.email ? "joignable" : "pas de contact"}
              </p>
            </button>
          ))}
          {queue.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Aucun prospect qualifié.
            </p>
          )}
        </div>
      </Card>

      {/* Fiche réelle du prospect sélectionné */}
      <div className="w-full lg:w-1/3 border-2 overflow-y-auto rounded-lg h-full flex flex-col p-6">
        {prospect ? (
          <div className="flex flex-col gap-6">
            <div className="flex items-center gap-3">
              <Building2 size={40} />
              <div>
                <p className="text-lg font-bold">{prospect.nom_entreprise}</p>
                <p className="text-sm text-muted-foreground">
                  {prospect.code_naf} · {prospect.statut}
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-3">
              {prospect.nom_dirigeant && (
                <div className="flex gap-2 items-center">
                  <User />
                  <p>{prospect.nom_dirigeant}</p>
                </div>
              )}
              {prospect.telephone && (
                <div className="flex gap-2 items-center">
                  <Phone />
                  <a
                    className="hover:underline"
                    href={`tel:${prospect.telephone}`}
                  >
                    {prospect.telephone}
                  </a>
                </div>
              )}
              {prospect.email && (
                <div className="flex gap-2 items-center">
                  <Mail />
                  <a
                    className="hover:underline"
                    href={`mailto:${prospect.email}`}
                  >
                    {prospect.email}
                  </a>
                </div>
              )}
              <div className="flex gap-2 items-center">
                <MapPin />
                <p>
                  {[prospect.adresse, prospect.code_postal, prospect.ville]
                    .filter(Boolean)
                    .join(", ") || "—"}
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <div className="flex justify-between">
                <p className="font-bold">Score global</p>
                <p className="font-bold">{prospect.score_final} / 100</p>
              </div>
              {prospect.justification_llm && (
                <p className="text-sm text-muted-foreground">
                  « {prospect.justification_llm} »
                </p>
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            Sélectionnez un prospect dans la file.
          </p>
        )}
      </div>

      {/* Contrôles d'appel — câblés sur l'API d'écriture (#116 A) */}
      <div className="w-full lg:w-1/3 flex flex-col gap-4 h-full overflow-hidden rounded-lg">
        <Card className="w-full shrink-0 border gap-3 border-gray-400 rounded-lg flex flex-col p-4">
          <p className="text-center text-sm text-muted-foreground">
            Résultat d'appel
          </p>
          <div className="flex w-full gap-2">
            <Button
              disabled={!activeId || busy}
              onClick={() => outcome.mutate("rdv")}
              className="flex-1 h-16 rounded-lg bg-emerald-600 hover:bg-emerald-700"
            >
              RDV
            </Button>
            <Button
              disabled={!activeId || busy}
              onClick={() => outcome.mutate("refus")}
              className="flex-1 h-16 rounded-lg bg-rose-600 hover:bg-rose-700"
            >
              Refus
            </Button>
            <Button
              disabled={!activeId || busy}
              onClick={() => outcome.mutate("absent")}
              variant="outline"
              className="flex-1 h-16 rounded-lg"
            >
              Absent
            </Button>
          </div>
          {outcome.isError && (
            <p className="text-xs text-rose-600 text-center">
              Échec : {(outcome.error as Error).message}
            </p>
          )}
        </Card>
        <Card className="w-full flex-1 border rounded-lg flex flex-col">
          <div className="w-full flex items-center justify-between p-4">
            <p>NOTES</p>
          </div>
          <Textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            disabled={!activeId}
            className="flex-1 border-y rounded-none"
            placeholder="Objections, budget, timeline…"
          />
          <div className="w-full flex justify-end p-4">
            <Button
              disabled={!activeId || !note.trim() || saveNote.isPending}
              onClick={() => saveNote.mutate()}
            >
              {saveNote.isPending ? "…" : "Sauvegarder"}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/appels")({
  component: Calls,
});
