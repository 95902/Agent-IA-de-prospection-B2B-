import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { postCampagne } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Field, FieldLabel } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Textarea } from "@/components/ui/Textarea";
import { Checkbox } from "@/components/ui/Checkbox";
import { Card } from "@/components/ui/Card";

const splitList = (s: string) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

const EMPTY = {
  nom_entreprise: "",
  secteur: "",
  produit_vendu: "",
  zone_intervention: "",
  nom: "",
  description_icp: "",
  codes_naf: "",
  departements: "",
  effectif_min: "",
  effectif_max: "",
  anciennete_min_ans: "",
  exiger_site_web: false,
  exiger_email: false,
  mots_cles_positifs: "",
  mots_cles_negatifs: "",
};

export const CampaignForm = () => {
  const [f, setF] = useState({ ...EMPTY });
  const set = (k: keyof typeof f, v: string | boolean) =>
    setF((p) => ({ ...p, [k]: v }));

  const create = useMutation({
    mutationFn: () =>
      postCampagne({
        nom_entreprise: f.nom_entreprise,
        secteur: f.secteur,
        produit_vendu: f.produit_vendu,
        zone_intervention: f.zone_intervention,
        nom: f.nom,
        description_icp: f.description_icp || undefined,
        codes_naf: splitList(f.codes_naf),
        departements: splitList(f.departements),
        effectif_min: f.effectif_min ? Number(f.effectif_min) : undefined,
        effectif_max: f.effectif_max ? Number(f.effectif_max) : undefined,
        anciennete_min_ans: f.anciennete_min_ans
          ? Number(f.anciennete_min_ans)
          : undefined,
        exiger_site_web: f.exiger_site_web,
        exiger_email: f.exiger_email,
        mots_cles_positifs: splitList(f.mots_cles_positifs),
        mots_cles_negatifs: splitList(f.mots_cles_negatifs),
      }),
    onSuccess: () => setF({ ...EMPTY }),
  });

  const canSubmit =
    f.nom_entreprise.trim() &&
    f.secteur.trim() &&
    f.produit_vendu.trim() &&
    f.zone_intervention.trim() &&
    f.nom.trim() &&
    f.codes_naf.trim();

  const text = (k: keyof typeof f, label: string, placeholder = "") => (
    <Field>
      <FieldLabel>{label}</FieldLabel>
      <Input
        type="text"
        className="w-full rounded-lg border"
        placeholder={placeholder}
        value={f[k] as string}
        onChange={(e) => set(k, e.target.value)}
      />
    </Field>
  );

  return (
    <Card className="min-w-full h-fit overflow-hidden border rounded-lg p-4 shrink-0">
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit) create.mutate();
        }}
      >
        {text("nom_entreprise", "Nom du client *", "Client Test — Hôtellerie")}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {text("secteur", "Secteur *", "Hôtellerie indépendante")}
          {text("zone_intervention", "Zone d'intervention *", "Île-de-France")}
        </div>
        {text("produit_vendu", "Produit vendu *", "Solution SaaS de gestion")}

        {text("nom", "Nom de la campagne / ICP *", "Hôtels indépendants 75/92")}
        <Field>
          <FieldLabel>Description de l'ICP</FieldLabel>
          <Textarea
            className="w-full rounded-lg border"
            placeholder="Hôtels indépendants, 2 à 50 salariés, ≥ 2 ans…"
            value={f.description_icp}
            onChange={(e) => set("description_icp", e.target.value)}
          />
        </Field>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {text("codes_naf", "Codes NAF * (séparés par des virgules)", "5510Z, 7311Z")}
          {text("departements", "Départements (virgules)", "75, 92")}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Field>
            <FieldLabel>Effectif min</FieldLabel>
            <Input
              type="number"
              className="w-full rounded-lg border"
              value={f.effectif_min}
              onChange={(e) => set("effectif_min", e.target.value)}
            />
          </Field>
          <Field>
            <FieldLabel>Effectif max</FieldLabel>
            <Input
              type="number"
              className="w-full rounded-lg border"
              value={f.effectif_max}
              onChange={(e) => set("effectif_max", e.target.value)}
            />
          </Field>
          <Field>
            <FieldLabel>Ancienneté min (ans)</FieldLabel>
            <Input
              type="number"
              className="w-full rounded-lg border"
              value={f.anciennete_min_ans}
              onChange={(e) => set("anciennete_min_ans", e.target.value)}
            />
          </Field>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {text("mots_cles_positifs", "Mots-clés positifs (virgules)", "hotel, hebergement")}
          {text("mots_cles_negatifs", "Mots-clés négatifs (virgules)", "groupe, chaine")}
        </div>
        <div className="flex flex-wrap gap-6">
          <label className="flex gap-2 items-center cursor-pointer text-sm">
            <Checkbox
              checked={f.exiger_site_web}
              onCheckedChange={(c) => set("exiger_site_web", !!c)}
            />
            Exiger un site web
          </label>
          <label className="flex gap-2 items-center cursor-pointer text-sm">
            <Checkbox
              checked={f.exiger_email}
              onCheckedChange={(c) => set("exiger_email", !!c)}
            />
            Exiger un email
          </label>
        </div>

        {create.isSuccess && (
          <p className="text-sm text-emerald-600">
            ✓ Campagne créée en <b>brouillon</b> — « {create.data.nom} » (id{" "}
            {create.data.campagne_id.slice(0, 8)}…). Aucun run lancé : lancement à
            déclencher séparément (gate crédits).
          </p>
        )}
        {create.isError && (
          <p className="text-sm text-rose-600">
            Échec : {(create.error as Error).message}
          </p>
        )}

        <Button
          type="submit"
          disabled={!canSubmit || create.isPending}
          className="w-fit self-end"
        >
          {create.isPending ? "Création…" : "Créer la campagne (brouillon)"}
        </Button>
      </form>
    </Card>
  );
};
