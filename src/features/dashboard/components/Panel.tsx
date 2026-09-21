import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Conteneur de section du tableau de bord.
 * `glass` : au-dessus de l'aurore (KPI). Sinon surface pleine (graphiques, tables).
 */
export const Panel = ({
  glass = false,
  className,
  children,
  ...rest
}: React.ComponentProps<"section"> & { glass?: boolean }) => (
  <section
    className={cn(
      "flex min-w-0 flex-col gap-3 rounded-[20px] border p-5 md:p-6",
      glass ? "glass-card" : "bg-card",
      className,
    )}
    {...rest}
  >
    {children}
  </section>
);

export const PanelHeader = ({
  title,
  description,
  action,
}: {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
}) => (
  <div className="flex flex-col gap-1">
    <div className="flex items-baseline justify-between gap-3">
      <h2 className="text-base font-semibold tracking-tight">{title}</h2>
      {action}
    </div>
    {description && <p className="text-[13px] text-muted-foreground">{description}</p>}
  </div>
);

/** Petit libellé en capitales espacées (en-têtes de KPI, colonnes). */
export const Eyebrow = ({ children, className }: { children: ReactNode; className?: string }) => (
  <span
    className={cn(
      "text-xs font-semibold tracking-[0.08em] text-muted-foreground uppercase",
      className,
    )}
  >
    {children}
  </span>
);
