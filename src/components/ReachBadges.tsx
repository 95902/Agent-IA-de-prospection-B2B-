import { Globe, Mail, Phone, type LucideIcon } from "lucide-react";
import type { ProspectRow } from "@/lib/api";
import { reachChannels } from "@/lib/reachability";
import { cn } from "@/lib/utils";

const CHANNELS: ReadonlyArray<{
  key: "email" | "telephone" | "site";
  icon: LucideIcon;
  on: string;
  off: string;
}> = [
  { key: "email", icon: Mail, on: "Email disponible", off: "Pas d'email" },
  { key: "telephone", icon: Phone, on: "Téléphone disponible", off: "Pas de téléphone" },
  { key: "site", icon: Globe, on: "Site web disponible", off: "Pas de site web" },
];

/** Trois pastilles email / téléphone / site : allumées si le canal existe. */
export const ReachBadges = ({
  prospect,
  className,
}: {
  prospect: Pick<ProspectRow, "email" | "telephone" | "site_web">;
  className?: string;
}) => {
  const c = reachChannels(prospect);
  return (
    <span className={cn("inline-flex gap-1.5", className)}>
      {CHANNELS.map(({ key, icon: Icon, on, off }) => {
        const active = c[key];
        return (
          <span
            key={key}
            role="img"
            aria-label={active ? on : off}
            title={active ? on : off}
            className={cn(
              "inline-flex size-7 items-center justify-center rounded-lg",
              active ? "bg-brand-soft text-brand" : "bg-muted text-muted-foreground/50",
            )}
          >
            <Icon className="size-[15px]" aria-hidden="true" />
          </span>
        );
      })}
    </span>
  );
};
