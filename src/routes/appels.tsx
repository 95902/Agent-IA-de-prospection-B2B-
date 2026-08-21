/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getProspect, getProspects } from "@/lib/api";
import { Building2, Mail, MapPin, Phone, User } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import { Card } from "@/components/ui/Card";

const Calls = () => {
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
                  <a className="hover:underline" href={`tel:${prospect.telephone}`}>
                    {prospect.telephone}
                  </a>
                </div>
              )}
              {prospect.email && (
                <div className="flex gap-2 items-center">
                  <Mail />
                  <a className="hover:underline" href={`mailto:${prospect.email}`}>
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

      {/* Contrôles d'appel — inactifs tant que l'API d'écriture n'existe pas */}
      <div className="w-full lg:w-1/3 flex flex-col gap-4 h-full overflow-hidden rounded-lg">
        <Card className="w-full shrink-0 border gap-3 border-gray-400 rounded-lg flex flex-col p-4">
          <p className="text-center text-sm text-muted-foreground">
            Résultat d'appel — <span className="font-semibold">à venir</span>{" "}
            (nécessite l'API d'écriture)
          </p>
          <div className="flex w-full gap-2">
            <Button disabled className="flex-1 h-16 rounded-lg">
              RDV
            </Button>
            <Button disabled className="flex-1 h-16 rounded-lg">
              Refus
            </Button>
            <Button disabled className="flex-1 h-16 rounded-lg">
              Absent
            </Button>
          </div>
        </Card>
        <Card className="w-full flex-1 border rounded-lg flex flex-col">
          <div className="w-full flex items-center justify-between p-4">
            <p>NOTES</p>
          </div>
          <Textarea
            disabled
            className="flex-1 border-y rounded-none"
            placeholder="Enregistrement des notes à venir (API d'écriture)."
          />
          <div className="w-full flex justify-end p-4">
            <Button disabled>Sauvegarder</Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/appels")({
  component: Calls,
});
