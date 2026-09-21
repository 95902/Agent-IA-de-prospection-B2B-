import { Radar } from "lucide-react";
import { cn } from "@/lib/utils";

/** Logo « B2B Intelligence » : pastille dégradé de marque + nom. */
export const BrandMark = ({ className }: { className?: string }) => (
  <div className={cn("flex items-center gap-2.5", className)}>
    <span className="flex size-8 items-center justify-center rounded-[10px] bg-brand-gradient text-brand-foreground shadow-glow">
      <Radar className="size-[18px]" strokeWidth={2} aria-hidden="true" />
    </span>
    <span className="flex flex-col leading-tight">
      <span className="text-[15px] font-semibold tracking-tight text-foreground">
        B2B Intelligence
      </span>
      <span className="text-xs text-muted-foreground">Prospection</span>
    </span>
  </div>
);
