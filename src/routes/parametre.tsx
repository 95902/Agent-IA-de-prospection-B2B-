/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";
import { Monitor, Moon, RotateCcw, Sun, UserRound } from "lucide-react";
import type { ReactNode } from "react";
import { useTheme } from "@/components/ThemeProvider";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SegmentedControl } from "@/components/ui/SegmentedControl";
import { KPI_WINDOWS } from "@/lib/kpiWindow";
import { DEFAULT_PROFILE, initialsOf, updateProfile, useProfile } from "@/lib/profile";

const Section = ({ title, description, children }: { title: string; description?: string; children: ReactNode }) => (
  <section className="grid gap-4 rounded-[20px] border bg-card p-5 md:grid-cols-[240px_minmax(0,1fr)] md:gap-8 md:p-6">
    <div className="flex flex-col gap-1">
      <h2 className="text-base font-semibold">{title}</h2>
      {description && <p className="text-[13px] text-muted-foreground">{description}</p>}
    </div>
    <div className="flex min-w-0 flex-col gap-4">{children}</div>
  </section>
);

const THEMES = [
  { value: "dark", label: "Sombre" },
  { value: "light", label: "Clair" },
  { value: "system", label: "Système" },
] as const;
const THEME_ICON = { dark: Moon, light: Sun, system: Monitor };

const Parametres = () => {
  const profile = useProfile();
  const { theme, setTheme } = useTheme();
  const initials = initialsOf(profile.name);
  const ThemeIcon = THEME_ICON[theme];

  return (
    <div className="mx-auto flex w-full max-w-[960px] flex-col gap-5 pt-2">
      <header className="flex flex-col gap-1.5">
        <h1 className="text-[32px] leading-tight font-semibold tracking-tight">Profil et préférences</h1>
        <p className="text-sm text-muted-foreground">
          Enregistrés automatiquement, dans ce navigateur uniquement (pas encore de compte utilisateur).
        </p>
      </header>

      <Section title="Identité" description="Affichée en bas de la barre latérale.">
        <div className="flex items-center gap-4">
          <span className="flex size-16 shrink-0 rounded-full bg-brand-gradient p-[3px]" aria-hidden="true">
            <span className="flex flex-1 items-center justify-center rounded-full bg-card text-xl font-semibold">
              {initials || <UserRound className="size-6 text-muted-foreground" />}
            </span>
          </span>
          <div className="flex min-w-0 flex-1 flex-col gap-3 sm:flex-row">
            <label className="flex min-w-0 flex-1 flex-col gap-1.5 text-[13px] text-muted-foreground">
              Nom
              <Input
                value={profile.name}
                maxLength={80}
                onChange={(e) => updateProfile({ name: e.target.value })}
                placeholder="Prénom Nom"
              />
            </label>
            <label className="flex min-w-0 flex-1 flex-col gap-1.5 text-[13px] text-muted-foreground">
              Rôle
              <Input
                value={profile.role}
                maxLength={80}
                onChange={(e) => updateProfile({ role: e.target.value })}
                placeholder="Ex. : responsable commercial"
              />
            </label>
          </div>
        </div>
      </Section>

      <Section title="Apparence" description="Thème et intensité de l'aurore en haut de l'écran.">
        <div className="flex flex-wrap items-center gap-3">
          <SegmentedControl label="Thème" options={THEMES} value={theme} onChange={(t) => setTheme(t)} />
          <ThemeIcon className="size-4 text-muted-foreground" aria-hidden="true" />
        </div>
        <label className="flex flex-col gap-2 text-[13px] text-muted-foreground">
          <span className="flex justify-between">
            Intensité de l'aurore
            <span className="font-mono tabular-nums">{profile.aurora} %</span>
          </span>
          <input
            type="range"
            min={0}
            max={100}
            step={5}
            value={profile.aurora}
            onChange={(e) => updateProfile({ aurora: Number(e.target.value) })}
            className="w-full max-w-sm accent-[var(--brand)]"
          />
        </label>
      </Section>

      <Section title="Tableau de bord" description="Période affichée par défaut pour les indicateurs.">
        <SegmentedControl
          label="Période par défaut"
          options={KPI_WINDOWS}
          value={profile.kpiWindow}
          onChange={(w) => updateProfile({ kpiWindow: w })}
          className="self-start"
        />
      </Section>

      <Section title="Lanceur de campagne" description="Pré-remplis à chaque nouvelle campagne.">
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="flex min-w-0 flex-1 flex-col gap-1.5 text-[13px] text-muted-foreground">
            Dernier client
            <Input
              value={profile.dernierClient}
              maxLength={80}
              onChange={(e) => updateProfile({ dernierClient: e.target.value })}
            />
          </label>
          <label className="flex min-w-0 flex-1 flex-col gap-1.5 text-[13px] text-muted-foreground">
            Dernier produit vendu
            <Input
              value={profile.dernierProduit}
              maxLength={80}
              onChange={(e) => updateProfile({ dernierProduit: e.target.value })}
            />
          </label>
        </div>
      </Section>

      <Section title="Données locales" description="Rien n'est envoyé au serveur depuis cette page.">
        <Button
          variant="outline"
          className="self-start"
          onClick={() => {
            updateProfile(DEFAULT_PROFILE);
            setTheme("dark");
          }}
        >
          <RotateCcw aria-hidden="true" />
          Réinitialiser le profil et les préférences
        </Button>
      </Section>
    </div>
  );
};

export const Route = createFileRoute("/parametre")({
  component: Parametres,
});
