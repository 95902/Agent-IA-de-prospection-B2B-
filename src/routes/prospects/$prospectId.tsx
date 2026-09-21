/* eslint-disable react-refresh/only-export-components */
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, Globe, Mail, MapPin, Phone, User, Users } from "lucide-react";
import type { ReactNode } from "react";
import { ReachBadges } from "@/components/ReachBadges";
import { ErrorState } from "@/components/States";
import { StatusPill } from "@/components/StatusPill";
import { buttonVariants } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { getProspect } from "@/lib/api";
import { displayName, formatScore } from "@/lib/format";
import { isActionable } from "@/lib/reachability";
import { prospectStatut, scoreBand } from "@/lib/statut";

const withProtocol = (url: string) => (/^https?:\/\//i.test(url) ? url : `https://${url}`);

const Info = ({ icon, children }: { icon: ReactNode; children: ReactNode }) => (
  <li className="flex items-start gap-3 text-sm">
    <span className="mt-0.5 text-muted-foreground">{icon}</span>
    <span className="min-w-0 break-words">{children}</span>
  </li>
);

const Layer = ({ label, value, hint }: { label: string; value: number; hint: string }) => (
  <div className="flex flex-col gap-2">
    <div className="flex items-baseline justify-between gap-3">
      <span className="text-sm font-medium">{label}</span>
      <span className="font-mono text-sm tabular-nums">{Math.round(value)} / 100</span>
    </div>
    <div className="h-2 overflow-hidden rounded-full bg-bar-muted">
      <div className="h-2 rounded-full bg-brand-bar" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
    <span className="text-xs text-muted-foreground">{hint}</span>
  </div>
);

const ProspectDetail = () => {
  const { prospectId } = Route.useParams();
  const { data: p, isLoading, isError, refetch } = useQuery({
    queryKey: ["prospect", prospectId],
    queryFn: () => getProspect(prospectId),
  });

  const back = (
    <Link to="/prospects" className="inline-flex items-center gap-1.5 text-[13px] text-muted-foreground hover:text-foreground">
      <ArrowLeft className="size-3.5" aria-hidden="true" /> Prospects
    </Link>
  );

  if (isLoading) {
    return (
      <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-4 pt-2">
        {back}
        <Skeleton className="h-10 w-1/2" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }
  if (isError || !p) {
    return (
      <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-4 pt-2">
        {back}
        <ErrorState message="Prospect introuvable ou indisponible." onRetry={() => refetch()} />
      </div>
    );
  }

  const band = scoreBand(p.score_final);
  const address = [p.adresse, [p.code_postal, p.ville].filter(Boolean).join(" ")].filter(Boolean).join(", ");

  return (
    <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-5 pt-2">
      {back}
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex min-w-0 flex-col gap-2">
          <h1 className="text-[30px] leading-tight font-semibold tracking-tight">{displayName(p.nom_entreprise)}</h1>
          <p className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <span className="font-mono">{p.code_naf}</span>
            {p.libelle_naf && <span>· {p.libelle_naf}</span>}
            <StatusPill value={prospectStatut(p.statut)} />
            {isActionable(p) && <StatusPill value={{ label: "Actionnable", tone: "success" }} />}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {p.telephone && (
            <a href={`tel:${p.telephone}`} className={buttonVariants({ variant: "brand" })}>
              <Phone aria-hidden="true" /> Appeler
            </a>
          )}
          {p.email && (
            <a href={`mailto:${p.email}`} className={buttonVariants({ variant: "outline" })}>
              <Mail aria-hidden="true" /> Email
            </a>
          )}
          {p.site_web && (
            <a
              href={withProtocol(p.site_web)}
              target="_blank"
              rel="noopener noreferrer"
              className={buttonVariants({ variant: "outline" })}
            >
              <Globe aria-hidden="true" /> Site web
            </a>
          )}
        </div>
      </header>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="flex flex-col gap-4">
          <section aria-labelledby="contact-titre" className="flex flex-col gap-4 rounded-[20px] border bg-card p-5 md:p-6">
            <div className="flex items-center justify-between gap-3">
              <h2 id="contact-titre" className="text-base font-semibold">
                Contact
              </h2>
              <ReachBadges prospect={p} />
            </div>
            <ul className="flex flex-col gap-3">
              {p.nom_dirigeant && <Info icon={<User className="size-4" />}>{p.nom_dirigeant}</Info>}
              {p.telephone && (
                <Info icon={<Phone className="size-4" />}>
                  <a href={`tel:${p.telephone}`} className="font-medium hover:underline">
                    {p.telephone}
                  </a>
                  {p.telephone_2 && <span className="text-muted-foreground"> · {p.telephone_2}</span>}
                </Info>
              )}
              {p.email && (
                <Info icon={<Mail className="size-4" />}>
                  <a href={`mailto:${p.email}`} className="font-medium hover:underline">
                    {p.email}
                  </a>
                </Info>
              )}
              {p.site_web && (
                <Info icon={<Globe className="size-4" />}>
                  <a href={withProtocol(p.site_web)} target="_blank" rel="noopener noreferrer" className="hover:underline">
                    {p.site_web}
                  </a>
                </Info>
              )}
              {!p.telephone && !p.email && (
                <li className="text-sm text-muted-foreground">Aucun email ni téléphone trouvé pour l'instant.</li>
              )}
            </ul>
          </section>

          <section aria-labelledby="entreprise-titre" className="flex flex-col gap-4 rounded-[20px] border bg-card p-5 md:p-6">
            <h2 id="entreprise-titre" className="text-base font-semibold">
              Entreprise
            </h2>
            <ul className="flex flex-col gap-3">
              <Info icon={<MapPin className="size-4" />}>{address || "—"}</Info>
              {p.effectif && <Info icon={<Users className="size-4" />}>{p.effectif}</Info>}
              {p.date_creation && (
                <Info icon={<CalendarDays className="size-4" />}>
                  Créée le {new Date(p.date_creation).toLocaleDateString("fr-FR")}
                </Info>
              )}
            </ul>
          </section>
        </div>

        <section aria-labelledby="score-titre" className="glass-card flex flex-col gap-5 rounded-[20px] border p-5 md:p-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div className="flex flex-col gap-1">
              <h2 id="score-titre" className="text-xs font-semibold tracking-[0.08em] text-muted-foreground uppercase">
                Score
              </h2>
              <span className="text-hero-glow text-6xl leading-none font-semibold tracking-tight tabular-nums">
                {formatScore(p.score_final)}
                <span className="text-xl font-medium text-muted-foreground"> /100</span>
              </span>
            </div>
            <StatusPill value={band} />
          </div>
          {p.justification_llm && (
            <blockquote className="rounded-xl border-l-2 border-brand bg-brand-soft/60 px-4 py-3 text-sm">
              {p.justification_llm}
            </blockquote>
          )}
          <div className="flex flex-col gap-4 border-t pt-4">
            <Layer label="Analyse Claude" value={p.score_llm} hint="Adéquation jugée par le modèle à partir de la description ICP." />
            <Layer label="Règles ICP" value={p.score_regles} hint="Secteur, taille, ancienneté, zone et mots-clés." />
            <Layer
              label="Similarité"
              value={p.score_embedding * 100}
              hint="Proximité sémantique avec le profil client idéal."
            />
          </div>
        </section>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/prospects/$prospectId")({
  component: ProspectDetail,
});
