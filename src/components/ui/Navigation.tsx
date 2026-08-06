import {
  Users,
  LayoutDashboard,
  Settings,
  HelpCircle,
  Plus,
  Phone,
  Megaphone,
} from "lucide-react";
import { Button } from "./Button";
import { Link } from "@tanstack/react-router";

const navItems = [
  { to: "/", label: "Tableau de bord", icon: LayoutDashboard },
  { to: "/prospects", label: "Prospects", icon: Users },
  { to: "/appels", label: "Appels", icon: Phone },
  { to: "/campagnes", label: "Campagnes", icon: Megaphone },
];

const navItemsSettings = [
  { to: "/parametre", label: "Paramètres", icon: Settings },
  { to: "/support", label: "Support", icon: HelpCircle },
];

export const Navigation = () => {
  return (
    <nav className="flex flex-col gap-1 h-full justify-between">
      <div className="">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground [&.active]:bg-primary [&.active]:text-primary-foreground transition-colors"
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </div>
      <div className="flex flex-col gap-4">
        <Button className="rounded-md py-2">
          <Plus className="h-4 w-4 " />
          Importer des prospects
        </Button>
        <div>
          {navItemsSettings.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground [&.active]:bg-primary [&.active]:text-primary-foreground transition-colors"
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
