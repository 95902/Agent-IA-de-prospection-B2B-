/* eslint-disable react-refresh/only-export-components */
import { createFileRoute, Link } from "@tanstack/react-router";
import { FileText, Phone, Radar, Sparkles } from "lucide-react";

const STEPS = [
  {
    icon: Sparkles,
    title: "Décrire la cible",
    text: "Une phrase dans « Nouvelle campagne » : secteur, zone, taille. Les critères sont modifiables avant création.",
  },
  {
    icon: FileText,
    title: "Créer le brouillon",
    text: "La campagne est enregistrée sans collecte ni appel payant : aucun crédit n'est consommé à cette étape.",
  },
  {
    icon: Radar,
    title: "Lancement par l'équipe",
    text: "Collecte INSEE Sirene, recherche des coordonnées puis score de 0 à 100 (règles, similarité et analyse Claude).",
  },
  {
    icon: Phone,
    title: "Contacter les actionnables",
    text: "Les prospects qualifiés et joignables arrivent dans « Appels » ; chaque résultat d'appel est enregistré.",
  },
];

const GLOSSARY = [
  ["Collecté", "Entreprise trouvée dans la base Sirene de l'INSEE pour les critères de la campagne."],
  ["Qualifié", "Prospect dont le score atteint au moins 60 sur 100."],
  ["Joignable", "Prospect pour lequel on dispose d'un email ou d'un numéro de téléphone."],
  ["Actionnable", "Prospect à la fois qualifié et joignable : celui qu'on peut vraiment contacter."],
  ["Rendement", "Part des prospects collectés qui sont actionnables, par campagne."],
  ["Brouillon", "Campagne configurée mais pas encore lancée : aucune donnée collectée."],
] as const;

const Support = () => (
  <div className="mx-auto flex w-full max-w-[960px] flex-col gap-6 pt-2">
    <header className="flex flex-col gap-1.5">
      <h1 className="text-[32px] leading-tight font-semibold tracking-tight">Aide</h1>
      <p className="text-sm text-muted-foreground">
        Comment fonctionne B2B Intelligence, et ce que signifient les indicateurs.
      </p>
    </header>

    <section aria-labelledby="etapes" className="flex flex-col gap-3">
      <h2 id="etapes" className="text-base font-semibold">
        Le parcours en 4 étapes
      </h2>
      <ol className="grid gap-3 sm:grid-cols-2">
        {STEPS.map(({ icon: Icon, title, text }, i) => (
          <li key={title} className="glass-card flex gap-4 rounded-[20px] border p-5">
            <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-soft text-brand">
              <Icon className="size-5" aria-hidden="true" />
            </span>
            <span className="flex flex-col gap-1">
              <span className="text-sm font-semibold">
                {i + 1}. {title}
              </span>
              <span className="text-[13px] text-muted-foreground">{text}</span>
            </span>
          </li>
        ))}
      </ol>
    </section>

    <section aria-labelledby="glossaire" className="flex flex-col gap-3 rounded-[20px] border bg-card p-5 md:p-6">
      <h2 id="glossaire" className="text-base font-semibold">
        Glossaire
      </h2>
      <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-[160px_minmax(0,1fr)]">
        {GLOSSARY.map(([term, def]) => (
          <div key={term} className="contents">
            <dt className="text-sm font-medium">{term}</dt>
            <dd className="text-sm text-muted-foreground">{def}</dd>
          </div>
        ))}
      </dl>
    </section>

    <p className="text-sm text-muted-foreground">
      Prêt ?{" "}
      <Link to="/campagnes/nouvelle" className="font-medium text-brand hover:underline">
        Décrivez votre première cible
      </Link>
      .
    </p>
  </div>
);

export const Route = createFileRoute("/support")({
  component: Support,
});
