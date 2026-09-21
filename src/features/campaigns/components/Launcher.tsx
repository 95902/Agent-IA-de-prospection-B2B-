import { Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Info, Lightbulb, Sparkles } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Button, buttonVariants } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { getIcpParseStatus, postCampagne, postIcpParse } from "@/lib/api";
import { updateProfile, useProfile } from "@/lib/profile";
import { mergeAiResult } from "../nl/merge";
import { parseTarget } from "../nl/parse";
import { buildPayload, campaignName, toIcpPayload, validate } from "../nl/payload";
import type { Criteria } from "../nl/types";
import { payloadToPrefill, savePrefill } from "../prefill";
import { CriteriaEditor } from "./CriteriaEditor";

const EXAMPLES = [
  "Hôtels indépendants de 10 à 50 salariés à Paris et dans les Hauts-de-Seine, avec site web, sauf les chaînes",
  "Restaurants et bars à Lyon, PME, avec email",
  "Experts-comptables en Île-de-France depuis plus de 3 ans",
];

const Field = ({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) => (
  <label className="flex min-w-0 flex-1 flex-col gap-1.5 text-[13px] text-muted-foreground">
    {label}
    {children}
    {hint && <span className="text-xs text-muted-foreground/80">{hint}</span>}
  </label>
);

/**
 * Lanceur de campagne : une phrase → critères éditables → brouillon.
 * Analyse 100 % locale et déterministe (0 crédit). Aucun prospect n'est collecté :
 * le lancement du pipeline reste une action opérateur (crédits API).
 */
export const Launcher = () => {
  const profile = useProfile();
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const [text, setText] = useState("");
  const [analysed, setAnalysed] = useState<string | null>(null);
  const [criteria, setCriteria] = useState<Criteria | null>(null);
  const [unmapped, setUnmapped] = useState<string[]>([]);
  const [assumptions, setAssumptions] = useState<string[]>([]);
  const [client, setClient] = useState(profile.dernierClient);
  const [produit, setProduit] = useState(profile.dernierProduit);
  const [nom, setNom] = useState("");

  const analyse = (value = text) => {
    const phrase = value.trim();
    if (!phrase) return;
    const r = parseTarget(phrase);
    setText(value);
    setAnalysed(phrase);
    setCriteria(r.criteria);
    setUnmapped(r.unmapped);
    setAssumptions(r.assumptions);
  };

  const meta = { client, produit, description: analysed ?? text, nom };
  const errors = criteria ? validate(criteria, meta) : [];

  // « Affiner avec l'IA » : visible seulement si le serveur l'a activé (sinon 404/false).
  const aiStatus = useQuery({
    queryKey: ["icp-parse-status"],
    queryFn: getIcpParseStatus,
    retry: false,
    staleTime: 5 * 60_000,
  });
  const refine = useMutation({
    mutationFn: () => postIcpParse({ phrase: analysed ?? text, non_traduits: unmapped }),
    onSuccess: (r) => {
      if (!criteria) return;
      const merged = mergeAiResult(criteria, r);
      setCriteria(merged.criteria);
      setUnmapped(merged.unmapped);
      setAssumptions((prev) => [...prev, ...merged.hypotheses]);
    },
  });
  const aiAction =
    aiStatus.data?.enabled && unmapped.length > 0 ? (
      <button
        type="button"
        onClick={() => refine.mutate()}
        disabled={refine.isPending || analysed !== text.trim()}
        title={analysed !== text.trim() ? "Analysez d'abord la phrase modifiée" : `Modèle : ${aiStatus.data.modele}`}
        className="inline-flex h-9 items-center gap-2 rounded-[10px] border bg-glass-card px-3 text-[13px] font-medium transition-colors hover:border-brand/40 disabled:opacity-50"
      >
        <Sparkles className="size-4 text-brand" aria-hidden="true" />
        {refine.isPending ? "Analyse IA…" : "Affiner avec l'IA"}
        <span className="font-mono text-[11px] text-muted-foreground">≈ 0,004 €</span>
      </button>
    ) : undefined;

  const create = useMutation({
    mutationFn: () => postCampagne(toIcpPayload(criteria!, meta)),
    onSuccess: () => {
      updateProfile({ dernierClient: client.trim(), dernierProduit: produit.trim() });
      queryClient.invalidateQueries({ queryKey: ["campagnes"] });
    },
  });

  const openAdvanced = () => {
    if (criteria) savePrefill(payloadToPrefill(buildPayload(criteria, meta)));
    navigate({ to: "/campagnes", hash: "formulaire-avance" });
  };

  if (create.isSuccess) {
    return (
      <div className="mx-auto flex w-full max-w-[920px] flex-col items-start gap-5 pt-10">
        <CheckCircle2 className="size-10 text-brand" aria-hidden="true" />
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">Brouillon créé</h1>
          <p className="text-muted-foreground">
            « {create.data.nom} » est enregistrée en brouillon. Aucun prospect n'a été collecté : le
            lancement du pipeline reste une action opérateur, pour maîtriser les crédits.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link to="/campagnes" className={buttonVariants({ variant: "brand", size: "lg" })}>
            Voir les campagnes <ArrowRight aria-hidden="true" />
          </Link>
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              create.reset();
              refine.reset();
              setText("");
              setAnalysed(null);
              setCriteria(null);
              setNom("");
            }}
          >
            Décrire une autre cible
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-[920px] flex-col gap-6 pt-4 pb-6 md:pt-8">
      <div className="flex flex-col gap-2.5">
        <nav aria-label="Fil d'Ariane" className="text-[13px] text-muted-foreground">
          <Link to="/campagnes" className="hover:text-foreground">
            Campagnes
          </Link>{" "}
          / <span className="text-foreground">Nouvelle campagne</span>
        </nav>
        <h1 className="text-4xl font-semibold tracking-tight md:text-[44px]">Décrivez votre cible</h1>
        <p className="text-muted-foreground md:text-base">
          Une phrase suffit. On la traduit en critères que vous pouvez corriger avant de créer le brouillon.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          analyse();
        }}
        className="glass relative flex flex-col gap-3.5 rounded-[22px] border p-5 pb-3.5 shadow-[0_30px_80px_-30px_rgb(0_0_0/0.45)]"
      >
        <label htmlFor="cible" className="sr-only">
          Description de la cible
        </label>
        <textarea
          id="cible"
          rows={3}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              analyse();
            }
          }}
          placeholder="Ex. : hôtels indépendants de 10 à 50 salariés à Paris et dans le 92, avec site web, sauf les chaînes"
          className="w-full resize-none bg-transparent text-lg leading-relaxed outline-none placeholder:text-muted-foreground/70 md:text-xl"
        />
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
            <CheckCircle2 className="size-3.5" aria-hidden="true" />
            Analyse locale · 0 crédit
          </span>
          <span className="hidden text-xs text-muted-foreground sm:inline">⌘/Ctrl + Entrée</span>
          <span className="flex-1" />
          <Button type="submit" variant="brand" size="lg" disabled={!text.trim()}>
            <Sparkles aria-hidden="true" />
            Analyser
          </Button>
        </div>
      </form>

      {!criteria && (
        <div className="flex flex-col gap-2">
          <span className="text-[13px] text-muted-foreground">Exemples</span>
          <div className="flex flex-col gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => analyse(ex)}
                className="rounded-xl border bg-glass-card px-4 py-3 text-left text-sm text-muted-foreground transition-colors hover:border-brand/40 hover:text-foreground"
              >
                « {ex} »
              </button>
            ))}
          </div>
        </div>
      )}

      {criteria && (
        <>
          {analysed !== text.trim() && (
            <p className="flex items-center gap-2 text-[13px] text-warning" role="status">
              <Info className="size-3.5" aria-hidden="true" />
              La phrase a changé : cliquez sur « Analyser » pour mettre à jour les critères.
            </p>
          )}

          <CriteriaEditor
            criteria={criteria}
            onChange={setCriteria}
            unmapped={unmapped}
            onUnmappedChange={setUnmapped}
            assumptions={assumptions}
            aiAction={aiAction}
          />
          {refine.isError && (
            <p role="alert" className="text-sm text-destructive">
              L'affinage IA a échoué : {(refine.error as Error).message}. Les critères actuels sont conservés.
            </p>
          )}

          {(criteria.effectif?.min ?? 0) < 10 && (
            <div className="flex items-start gap-3 rounded-2xl bg-brand-soft px-4 py-3.5 text-sm">
              <Lightbulb className="mt-0.5 size-4 shrink-0 text-brand" aria-hidden="true" />
              <span>
                Astuce : cibler les entreprises d'<strong>au moins 10 salariés</strong> améliore nettement la
                part de prospects joignables (mesuré sur le pilote hôtels).
              </span>
            </div>
          )}

          <section aria-labelledby="pour-qui" className="flex flex-col gap-4 rounded-[20px] border bg-card p-5 md:p-6">
            <h2 id="pour-qui" className="text-base font-semibold">
              Pour qui ?
            </h2>
            <div className="flex flex-col gap-4 md:flex-row">
              <Field label="Client *">
                <Input value={client} onChange={(e) => setClient(e.target.value)} placeholder="Nom du client" />
              </Field>
              <Field label="Ce que vous vendez *">
                <Input value={produit} onChange={(e) => setProduit(e.target.value)} placeholder="Ex. : logiciel de réservation" />
              </Field>
            </div>
            <Field label="Nom de la campagne" hint="Laissez vide pour utiliser le nom proposé.">
              <Input value={nom} onChange={(e) => setNom(e.target.value)} placeholder={campaignName(criteria)} />
            </Field>
          </section>

          {errors.length > 0 && (
            <ul className="flex flex-col gap-1 text-[13px] text-muted-foreground" aria-label="À compléter">
              {errors.map((err) => (
                <li key={err}>• {err}</li>
              ))}
            </ul>
          )}
          {create.isError && (
            <p role="alert" className="text-sm text-destructive">
              La création a échoué : {(create.error as Error).message}
            </p>
          )}

          <div className="flex flex-col-reverse items-start gap-4 border-t pt-5 md:flex-row md:items-center">
            <button type="button" onClick={openAdvanced} className="text-sm font-medium text-brand hover:underline">
              Mode avancé (formulaire complet)
            </button>
            <span className="flex-1 text-[13px] text-muted-foreground md:text-right">
              Aucun prospect collecté à cette étape. Le lancement reste une action opérateur (crédits API).
            </span>
            <Button
              variant="brand"
              size="lg"
              disabled={errors.length > 0 || create.isPending}
              onClick={() => create.mutate()}
            >
              {create.isPending ? "Création…" : "Créer le brouillon"}
              <ArrowRight aria-hidden="true" />
            </Button>
          </div>
        </>
      )}
    </div>
  );
};
