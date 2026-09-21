import { AlertTriangle, Inbox, RotateCw } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

/** Erreur de chargement avec bouton « Réessayer ». */
export const ErrorState = ({
  message = "Impossible de charger ces données.",
  onRetry,
  className,
}: {
  message?: string;
  onRetry?: () => void;
  className?: string;
}) => (
  <div
    role="alert"
    className={cn(
      "flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed p-6 text-center",
      className,
    )}
  >
    <AlertTriangle className="size-5 text-warning" aria-hidden="true" />
    <p className="text-sm text-muted-foreground">{message}</p>
    {onRetry && (
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RotateCw aria-hidden="true" />
        Réessayer
      </Button>
    )}
  </div>
);

/** État vide explicite (jamais un tableau blanc). */
export const EmptyState = ({
  title,
  children,
  className,
}: {
  title: string;
  children?: ReactNode;
  className?: string;
}) => (
  <div
    className={cn(
      "flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed p-6 text-center",
      className,
    )}
  >
    <Inbox className="size-5 text-muted-foreground" aria-hidden="true" />
    <p className="text-sm font-medium">{title}</p>
    {children && <div className="text-sm text-muted-foreground">{children}</div>}
  </div>
);
