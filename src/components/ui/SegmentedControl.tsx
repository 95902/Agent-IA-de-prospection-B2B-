import { cn } from "@/lib/utils";

type Option<T extends string> = { value: T; label: string; description?: string };

/** Groupe de boutons exclusifs (ex. 7 j / 30 j / Tout), accessible au clavier. */
function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  label,
  className,
}: {
  options: ReadonlyArray<Option<T>>;
  value: T;
  onChange: (value: T) => void;
  label: string;
  className?: string;
}) {
  return (
    <div
      role="group"
      aria-label={label}
      className={cn("glass inline-flex gap-0.5 rounded-xl border p-[3px]", className)}
    >
      {options.map((o) => {
        const active = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={active}
            title={o.description}
            onClick={() => onChange(o.value)}
            className={cn(
              "h-8 rounded-[9px] px-3.5 text-[13px] font-medium transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/30",
              active
                ? "bg-sidebar-accent font-semibold text-foreground shadow-[inset_0_0_0_1px_var(--border)]"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}

export { SegmentedControl };
