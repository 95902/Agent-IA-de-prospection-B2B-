import { Link } from "@tanstack/react-router";
import { UserRound } from "lucide-react";
import { initialsOf, useProfile } from "@/lib/profile";

/** Pastille profil en bas de la sidebar → page Paramètres (profil local). */
export const ProfileChip = ({ onNavigate }: { onNavigate?: () => void }) => {
  const { name, role } = useProfile();
  const initials = initialsOf(name);

  return (
    <Link
      to="/parametre"
      onClick={onNavigate}
      className="flex items-center gap-3 rounded-xl border bg-glass-card p-2.5 transition-colors hover:bg-sidebar-accent"
    >
      <span className="flex size-9 shrink-0 rounded-full bg-brand-gradient p-[2px]">
        <span className="flex flex-1 items-center justify-center rounded-full bg-card text-[13px] font-semibold text-foreground">
          {initials || <UserRound className="size-4 text-muted-foreground" aria-hidden="true" />}
        </span>
      </span>
      <span className="flex min-w-0 flex-col">
        <span className="truncate text-[13px] font-semibold text-foreground">
          {name || "Mon profil"}
        </span>
        <span className="truncate text-xs text-muted-foreground">
          {name ? role || "Profil et préférences" : "Nom, rôle, préférences"}
        </span>
      </span>
    </Link>
  );
};
