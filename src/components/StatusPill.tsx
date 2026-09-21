import { TONE_CLASSES, type Labelled } from "@/lib/statut";
import { cn } from "@/lib/utils";

/** Pastille de statut (prospect, campagne, bande de score). */
export const StatusPill = ({
  value,
  className,
}: {
  value: Labelled;
  className?: string;
}) => (
  <span
    className={cn(
      "inline-flex h-6 items-center rounded-full px-2.5 text-xs font-medium whitespace-nowrap",
      TONE_CLASSES[value.tone],
      className,
    )}
  >
    {value.label}
  </span>
);
