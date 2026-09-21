import { AlertTriangle, Check, Info, Minus, Plus, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Input } from "@/components/ui/Input";
import { cn } from "@/lib/utils";
import type { Criteria } from "../nl/types";

// --- Pastille de critère ------------------------------------------------------
const Chip = ({
  children,
  detail,
  tone = "ok",
  onRemove,
  removeLabel,
  actions,
}: {
  children: ReactNode;
  detail?: string;
  tone?: "ok" | "warn";
  onRemove?: () => void;
  removeLabel?: string;
  actions?: ReactNode;
}) => (
  <span
    className={cn(
      "inline-flex min-h-9 items-center gap-2 rounded-[10px] py-1 pr-1 pl-3 text-sm",
      tone === "ok"
        ? "border border-brand/35 bg-brand-soft"
        : "border border-dashed border-warning bg-warning-soft",
    )}
  >
    {tone === "ok" ? (
      <Check className="size-3.5 shrink-0 text-brand" strokeWidth={2.5} aria-hidden="true" />
    ) : (
      <AlertTriangle className="size-3.5 shrink-0 text-warning" aria-hidden="true" />
    )}
    <span className="font-medium">{children}</span>
    {detail && <span className="font-mono text-xs text-muted-foreground">{detail}</span>}
    {actions}
    {onRemove && (
      <button
        type="button"
        aria-label={removeLabel}
        onClick={onRemove}
        className="flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
      >
        <X className="size-3.5" aria-hidden="true" />
      </button>
    )}
  </span>
);

const Row = ({ label, children }: { label: string; children: ReactNode }) => (
  <div className="grid gap-2 sm:grid-cols-[130px_minmax(0,1fr)] sm:items-center sm:gap-4">
    <span className="text-[13px] text-muted-foreground">{label}</span>
    <div className="flex flex-wrap items-center gap-2">{children}</div>
  </div>
);

const Empty = ({ children }: { children: ReactNode }) => (
  <span className="text-[13px] text-muted-foreground/80 italic">{children}</span>
);

/** Champ « ajouter un mot » (Entrée pour valider). */
const AddWord = ({ label, onAdd }: { label: string; onAdd: (w: string) => void }) => {
  const [value, setValue] = useState("");
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const w = value.trim();
        if (w) onAdd(w);
        setValue("");
      }}
      className="flex items-center gap-1"
    >
      <Input
        aria-label={label}
        placeholder="Ajouter…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="h-9 w-36"
      />
      <button
        type="submit"
        aria-label={label}
        className="flex size-9 items-center justify-center rounded-lg border text-muted-foreground hover:bg-accent hover:text-foreground"
      >
        <Plus className="size-4" aria-hidden="true" />
      </button>
    </form>
  );
};

const NumberField = ({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  placeholder?: string;
}) => (
  <label className="flex items-center gap-2 text-[13px] text-muted-foreground">
    {label}
    <Input
      type="number"
      min={0}
      inputMode="numeric"
      value={value ?? ""}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value === "" ? null : Math.max(0, Math.round(Number(e.target.value))))}
      className="h-9 w-24 font-mono"
    />
  </label>
);

const Toggle = ({ on, onClick, children }: { on: boolean; onClick: () => void; children: ReactNode }) => (
  <button
    type="button"
    aria-pressed={on}
    onClick={onClick}
    className={cn(
      "inline-flex h-9 items-center gap-2 rounded-[10px] px-3 text-sm font-medium transition-colors",
      on ? "border border-brand/35 bg-brand-soft text-foreground" : "border border-dashed text-muted-foreground hover:text-foreground",
    )}
  >
    {on ? <Check className="size-3.5 text-brand" strokeWidth={2.5} aria-hidden="true" /> : <Plus className="size-3.5" aria-hidden="true" />}
    {children}
  </button>
);

// --- Éditeur ------------------------------------------------------------------
export const CriteriaEditor = ({
  criteria,
  onChange,
  unmapped,
  onUnmappedChange,
  assumptions,
  aiAction,
}: {
  criteria: Criteria;
  onChange: (c: Criteria) => void;
  unmapped: string[];
  onUnmappedChange: (words: string[]) => void;
  assumptions: string[];
  /** Bouton « Affiner avec l'IA » (affiché seulement si le service est disponible). */
  aiAction?: ReactNode;
}) => {
  const set = (patch: Partial<Criteria>) => onChange({ ...criteria, ...patch });
  const without = (list: string[], w: string) => list.filter((x) => x !== w);
  const addTo = (key: "motsClesPositifs" | "motsClesNegatifs", w: string) =>
    set({ [key]: [...new Set([...criteria[key], w])] });
  const moveUnmapped = (w: string, key: "motsClesPositifs" | "motsClesNegatifs") => {
    addTo(key, w.toLowerCase());
    onUnmappedChange(without(unmapped, w));
  };
  const recognized =
    criteria.secteurs.length +
    criteria.zones.length +
    (criteria.effectif ? 1 : 0) +
    (criteria.ancienneteMin !== null ? 1 : 0) +
    (criteria.exigerSiteWeb ? 1 : 0) +
    (criteria.exigerEmail ? 1 : 0) +
    criteria.motsClesNegatifs.length +
    criteria.motsClesPositifs.length;
  const e = criteria.effectif ?? { min: null, max: null };
  const setEffectif = (patch: Partial<typeof e>) => {
    const next = { ...e, ...patch };
    set({ effectif: next.min === null && next.max === null ? null : next });
  };

  return (
    <section aria-labelledby="criteres-titre" className="flex flex-col gap-4 rounded-[20px] border bg-card p-5 md:p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="criteres-titre" className="text-base font-semibold">
          Critères détectés
        </h2>
        <span className="text-[13px] text-muted-foreground" aria-live="polite">
          {recognized} reconnu{recognized > 1 ? "s" : ""}
          {unmapped.length > 0 && ` · ${unmapped.length} à vérifier`}
        </span>
      </div>

      <Row label="Secteur">
        {criteria.secteurs.length === 0 && <Empty>Aucun secteur — tous secteurs</Empty>}
        {criteria.secteurs.map((s) => (
          <Chip
            key={s.id}
            detail={s.naf.join(" · ")}
            onRemove={() => set({ secteurs: criteria.secteurs.filter((x) => x.id !== s.id) })}
            removeLabel={`Retirer le secteur ${s.label}`}
          >
            {s.label}
          </Chip>
        ))}
      </Row>

      <Row label="Zone">
        {criteria.zones.length === 0 && <Empty>Aucune zone — France entière</Empty>}
        {criteria.zones.map((z) => (
          <Chip
            key={z.id}
            onRemove={() => set({ zones: criteria.zones.filter((x) => x.id !== z.id) })}
            removeLabel={`Retirer la zone ${z.label}`}
          >
            {z.label}
          </Chip>
        ))}
      </Row>

      <Row label="Effectif">
        <NumberField label="de" value={e.min} onChange={(min) => setEffectif({ min })} placeholder="1" />
        <NumberField label="à" value={e.max} onChange={(max) => setEffectif({ max })} placeholder="sans limite" />
        <span className="text-[13px] text-muted-foreground">salariés</span>
      </Row>

      <Row label="Ancienneté">
        <NumberField
          label="au moins"
          value={criteria.ancienneteMin}
          onChange={(ancienneteMin) => set({ ancienneteMin })}
          placeholder="0"
        />
        <span className="text-[13px] text-muted-foreground">ans</span>
      </Row>

      <Row label="Exigences">
        <Toggle on={criteria.exigerSiteWeb} onClick={() => set({ exigerSiteWeb: !criteria.exigerSiteWeb })}>
          Site web requis
        </Toggle>
        <Toggle on={criteria.exigerEmail} onClick={() => set({ exigerEmail: !criteria.exigerEmail })}>
          Email requis
        </Toggle>
      </Row>

      <Row label="Exclusions">
        {criteria.motsClesNegatifs.map((w) => (
          <Chip
            key={w}
            detail="mot-clé exclu"
            onRemove={() => set({ motsClesNegatifs: without(criteria.motsClesNegatifs, w) })}
            removeLabel={`Retirer l'exclusion ${w}`}
          >
            « {w} »
          </Chip>
        ))}
        <AddWord label="Ajouter un mot-clé exclu" onAdd={(w) => addTo("motsClesNegatifs", w)} />
      </Row>

      <Row label="Mots-clés">
        {criteria.motsClesPositifs.map((w) => (
          <Chip
            key={w}
            detail="bonus de score"
            onRemove={() => set({ motsClesPositifs: without(criteria.motsClesPositifs, w) })}
            removeLabel={`Retirer le mot-clé ${w}`}
          >
            « {w} »
          </Chip>
        ))}
        <AddWord label="Ajouter un mot-clé positif" onAdd={(w) => addTo("motsClesPositifs", w)} />
      </Row>

      {(unmapped.length > 0 || aiAction) && (
        <Row label="À vérifier">
          {unmapped.map((w) => (
            <Chip
              key={w}
              tone="warn"
              detail="non traduit"
              onRemove={() => onUnmappedChange(without(unmapped, w))}
              removeLabel={`Ignorer ${w}`}
              actions={
                <span className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => moveUnmapped(w, "motsClesPositifs")}
                    className="inline-flex h-7 items-center gap-1 rounded-md px-2 text-xs font-medium text-brand hover:bg-brand-soft"
                    aria-label={`Utiliser ${w} comme mot-clé positif`}
                  >
                    <Plus className="size-3" aria-hidden="true" /> mot-clé
                  </button>
                  <button
                    type="button"
                    onClick={() => moveUnmapped(w, "motsClesNegatifs")}
                    className="inline-flex h-7 items-center gap-1 rounded-md px-2 text-xs font-medium text-muted-foreground hover:bg-accent"
                    aria-label={`Exclure ${w}`}
                  >
                    <Minus className="size-3" aria-hidden="true" /> exclure
                  </button>
                </span>
              }
            >
              « {w} »
            </Chip>
          ))}
          {aiAction}
        </Row>
      )}

      {assumptions.length > 0 && (
        <ul className="flex flex-col gap-1.5 border-t pt-4">
          {assumptions.map((a) => (
            <li key={a} className="flex items-start gap-2 text-[13px] text-muted-foreground">
              <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
              {a}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
};
