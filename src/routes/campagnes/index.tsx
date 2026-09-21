/* eslint-disable react-refresh/only-export-components */
import { createFileRoute, Link } from "@tanstack/react-router";
import { Info, SlidersHorizontal, Sparkles } from "lucide-react";
import { buttonVariants } from "@/components/ui/Button";
import { CampaignForm } from "@/features/campaigns/components/CampaignForm";
import { CampaignsCard } from "@/features/dashboard/components/CampaignsCard";
import { useCampaignStats } from "@/features/dashboard/queries";
import { readPrefill } from "@/features/campaigns/prefill";

const Campaigns = () => {
  const campaigns = useCampaignStats();
  // Ouvert d'office quand on arrive du lanceur (« Mode avancé ») avec un pré-remplissage.
  const openAdvanced = readPrefill() !== null;

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-6 pt-2">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-[32px] leading-tight font-semibold tracking-tight">Campagnes</h1>
          <p className="text-sm text-muted-foreground">
            Chaque campagne est d'abord un brouillon : ciblage et client, sans collecte ni crédit.
          </p>
        </div>
        <Link
          to="/campagnes/nouvelle"
          className={buttonVariants({ variant: "brand", size: "lg", className: "self-start md:self-auto" })}
        >
          <Sparkles aria-hidden="true" />
          Nouvelle campagne
        </Link>
      </header>

      <CampaignsCard
        showViewAll={false}
        campaigns={campaigns.data}
        isLoading={campaigns.isLoading}
        isError={campaigns.isError}
        onRetry={() => campaigns.refetch()}
      />

      <details
        id="formulaire-avance"
        open={openAdvanced}
        className="group rounded-[20px] border bg-card open:pb-2"
      >
        <summary className="flex cursor-pointer list-none items-center gap-3 rounded-[20px] p-5 md:p-6">
          <SlidersHorizontal className="size-4 text-muted-foreground" aria-hidden="true" />
          <span className="flex flex-col">
            <span className="font-semibold">Formulaire avancé</span>
            <span className="text-[13px] text-muted-foreground">
              Codes NAF, départements, effectif et mots-clés saisis à la main.
            </span>
          </span>
          <span className="ml-auto text-[13px] text-brand group-open:hidden">Ouvrir</span>
        </summary>
        <div className="flex flex-col gap-4 px-5 md:px-6">
          <p className="flex items-start gap-2 rounded-xl bg-muted p-3 text-[13px] text-muted-foreground">
            <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
            Valider crée la campagne en brouillon (client + critères + ICP) : aucun prospect collecté. Le
            lancement du pipeline (INSEE / Tavily / Claude) est une action séparée, pour maîtriser les crédits.
          </p>
          <CampaignForm />
        </div>
      </details>
    </div>
  );
};

export const Route = createFileRoute("/campagnes/")({
  component: Campaigns,
});
