import type { ReactNode } from "react";
import { Skeleton } from "@/components/ui/Skeleton";
import { Eyebrow, Panel } from "./Panel";

/** Petite carte KPI (verre) : libellé, valeur, précision. */
export const StatCard = ({
  label,
  value,
  sub,
  isLoading,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  isLoading?: boolean;
}) => (
  <Panel glass className="gap-2">
    <Eyebrow>{label}</Eyebrow>
    {isLoading ? (
      <>
        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-4 w-36" />
      </>
    ) : (
      <>
        <span className="text-4xl leading-tight font-semibold tracking-tight tabular-nums">
          {value}
        </span>
        {sub && <span className="text-[13px] text-muted-foreground">{sub}</span>}
      </>
    )}
  </Panel>
);
