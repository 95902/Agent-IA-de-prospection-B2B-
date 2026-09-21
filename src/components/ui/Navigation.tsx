import {
  Users,
  LayoutDashboard,
  Settings,
  HelpCircle,
  Phone,
  Target,
  Sparkles,
} from "lucide-react";
import { Link } from "@tanstack/react-router";
import { BrandMark } from "@/components/BrandMark";
import { ProfileChip } from "@/components/ProfileChip";

const navItems = [
  { to: "/", label: "Tableau de bord", icon: LayoutDashboard, exact: true },
  { to: "/prospects", label: "Prospects", icon: Users, exact: false },
  { to: "/appels", label: "Appels", icon: Phone, exact: false },
  { to: "/campagnes", label: "Campagnes", icon: Target, exact: false },
] as const;

const navItemsSettings = [
  { to: "/parametre", label: "Paramètres", icon: Settings },
  { to: "/support", label: "Support", icon: HelpCircle },
] as const;

const itemClass =
  "group flex h-10 items-center gap-3 rounded-[10px] px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground [&.active]:bg-sidebar-accent [&.active]:font-semibold [&.active]:text-foreground [&.active]:shadow-[inset_0_0_0_1px_var(--border)]";
const iconClass =
  "size-[18px] text-muted-foreground transition-colors group-[.active]:text-brand";

/**
 * Contenu de la sidebar (desktop) et du menu mobile (Sheet).
 * `onNavigate` ferme le menu mobile après un clic.
 */
export const Navigation = ({
  showBrand = true,
  onNavigate,
}: {
  showBrand?: boolean;
  onNavigate?: () => void;
}) => {
  return (
    <div className="flex h-full flex-col gap-6">
      {showBrand && <BrandMark className="px-2 pt-1" />}
      <Link
        to="/campagnes"
        onClick={onNavigate}
        className="flex h-11 items-center justify-center gap-2 rounded-xl bg-brand-gradient text-sm font-semibold text-brand-foreground shadow-glow transition hover:brightness-110"
      >
        <Sparkles className="size-[18px]" aria-hidden="true" />
        Nouvelle campagne
      </Link>
      <nav aria-label="Navigation principale" className="flex flex-col gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              activeOptions={{ exact: item.exact }}
              onClick={onNavigate}
              className={itemClass}
            >
              <Icon className={iconClass} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="flex-1" />
      <nav aria-label="Réglages et aide" className="flex flex-col gap-1">
        {navItemsSettings.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={itemClass}
            >
              <Icon className={iconClass} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <ProfileChip onNavigate={onNavigate} />
    </div>
  );
};
