/* eslint-disable react-refresh/only-export-components */
import { Button } from "@/components/ui/Button";
import { Card, CardTitle } from "@/components/ui/Card";
import { Progress } from "@/components/ui/Progress";
import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { getProspect } from "@/lib/api";
import { Building2, Globe, Mail, MapPin, Phone, Users } from "lucide-react";

const PropspectId = () => {
  const { prospectId } = Route.useParams();
  const {
    data: p,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["prospect", prospectId],
    queryFn: () => getProspect(prospectId),
  });

  if (isLoading) {
    return (
      <div className="p-8 text-sm text-muted-foreground">
        Chargement de la fiche prospect…
      </div>
    );
  }
  if (isError || !p) {
    return (
      <div className="p-8 text-sm text-rose-600">Prospect introuvable.</div>
    );
  }

  const localisation =
    [p.adresse, [p.code_postal, p.ville].filter(Boolean).join(" ")]
      .filter(Boolean)
      .join(", ") || "—";
  const scoreColor =
    p.score_final >= 60
      ? "bg-emerald-500"
      : p.score_final < 30
        ? "bg-rose-500"
        : "bg-amber-500";
  const embeddingPct = Math.round(p.score_embedding * 100);

  return (
    <div className="w-full h-full flex flex-col gap-4">
      {/* En-tête */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2">
        <div className="flex flex-col space-y-1">
          <CardTitle className="font-bold text-2xl">
            {p.nom_entreprise}
          </CardTitle>
          <p className="text-muted-foreground text-sm">
            {p.code_naf}
            {p.libelle_naf ? ` — ${p.libelle_naf}` : ""} · {p.statut}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {p.telephone && (
            <Button
              variant="outline"
              className="rounded-lg"
              onClick={() => {
                window.location.href = `tel:${p.telephone}`;
              }}
            >
              <Phone /> Appeler
            </Button>
          )}
          {p.email && (
            <Button
              variant="outline"
              className="rounded-lg"
              onClick={() => {
                window.location.href = `mailto:${p.email}`;
              }}
            >
              <Mail /> Email
            </Button>
          )}
          {p.site_web && (
            <Button
              className="rounded-lg"
              onClick={() => window.open(p.site_web ?? "", "_blank")}
            >
              <Globe /> Site web
            </Button>
          )}
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row gap-4">
        {/* Colonne gauche : identité + contact + score */}
        <div className="flex-1 lg:w-1/3 flex flex-col gap-4">
          <Card className="w-full border flex flex-col gap-4 border-gray-400 rounded-lg p-8">
            <div className="flex gap-3 items-center">
              <Building2 size={48} />
              <div className="flex flex-col">
                <p className="font-bold text-lg">{p.nom_entreprise}</p>
                {p.nom_dirigeant && (
                  <p className="text-muted-foreground text-xs">
                    {p.nom_dirigeant}
                  </p>
                )}
              </div>
            </div>
            <div className="flex flex-col gap-4">
              {p.email && (
                <div className="flex items-center gap-4">
                  <Mail className="text-blue-700" />
                  <a className="hover:underline" href={`mailto:${p.email}`}>
                    {p.email}
                  </a>
                </div>
              )}
              {p.telephone && (
                <div className="flex items-center gap-4">
                  <Phone className="text-blue-700" />
                  <a className="hover:underline" href={`tel:${p.telephone}`}>
                    {p.telephone}
                  </a>
                </div>
              )}
              <div className="flex items-center gap-4">
                <MapPin className="text-blue-700" />
                <p>{localisation}</p>
              </div>
              {p.effectif && (
                <div className="flex items-center gap-4">
                  <Users className="text-blue-700" />
                  <p>{p.effectif}</p>
                </div>
              )}
            </div>
          </Card>

          {/* Score global + justification Claude */}
          <div className="w-full bg-black flex flex-col gap-4 rounded-lg p-4 dark:border-white dark:border">
            <div className="flex justify-between items-center">
              <p className="text-xl font-bold text-white">Score global</p>
              <div className="bg-blue-500 rounded-lg px-4 py-2">
                <p className="text-white text-nowrap font-bold">score final</p>
              </div>
            </div>
            <div className="flex flex-col items-center gap-4 w-full">
              <p className="text-3xl font-bold w-full text-start text-white">
                {p.score_final} / 100
              </p>
              <Progress
                value={p.score_final}
                className="w-full shrink-0"
                indicatorClassName={scoreColor}
              />
            </div>
            {p.justification_llm && (
              <p className="text-purple-200 flex-1">« {p.justification_llm} »</p>
            )}
          </div>
        </div>

        {/* Colonne droite : détail du scoring hybride (vraies couches) */}
        <div className="lg:w-2/3 h-full flex flex-col gap-4 rounded-lg">
          <Card className="flex-1 border rounded-lg flex flex-col border-gray-400 gap-0">
            <div className="w-full rounded-t-lg flex justify-between items-center border-b-2 p-4 bg-muted/40">
              <p className="text-gray-700 text-lg dark:text-white">
                Détail du scoring hybride
              </p>
            </div>
            <div className="flex-1 flex flex-col p-6 gap-6">
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <p className="font-bold">Analyse Claude (LLM)</p>
                  <p className="text-green-600 text-nowrap">
                    {p.score_llm} / 100
                  </p>
                </div>
                <Progress
                  value={p.score_llm}
                  className="w-full"
                  indicatorClassName="bg-green-500"
                />
                {p.justification_llm && (
                  <p className="text-muted-foreground text-sm">
                    {p.justification_llm}
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <p className="font-bold">Règles (conformité ICP)</p>
                  <p className="text-green-600 text-nowrap">
                    {p.score_regles} / 100
                  </p>
                </div>
                <Progress
                  value={p.score_regles}
                  className="w-full"
                  indicatorClassName="bg-blue-500"
                />
              </div>
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <p className="font-bold">Similarité embedding (Qdrant)</p>
                  <p className="text-green-600 text-nowrap">{embeddingPct} %</p>
                </div>
                <Progress
                  value={embeddingPct}
                  className="w-full"
                  indicatorClassName="bg-purple-500"
                />
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/prospects/$prospectId")({
  component: PropspectId,
});
