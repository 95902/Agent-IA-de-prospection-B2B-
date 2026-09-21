import { Menu, Search } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/Button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/Sheet";
import { Navigation } from "@/components/ui/Navigation";
import { BrandMark } from "@/components/BrandMark";
import { ModeToggle } from "@/components/ModeToggle";

/** Recherche globale : ouvre la liste des prospects filtrée (?q=…). */
const HeaderSearch = () => {
  const navigate = useNavigate();
  const [value, setValue] = useState("");

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    const q = value.trim();
    navigate({ to: "/prospects", search: q ? { q } : {} });
  };

  return (
    <form role="search" onSubmit={onSubmit} className="w-full max-w-[480px]">
      <label className="glass flex h-10 items-center gap-2.5 rounded-xl border px-3 text-muted-foreground focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/30">
        <Search className="size-4 shrink-0" aria-hidden="true" />
        <span className="sr-only">Rechercher un prospect</span>
        <input
          type="search"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Rechercher une entreprise, une ville, un code NAF…"
          className="min-w-0 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
        />
      </label>
    </form>
  );
};

export const Header = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="flex h-16 shrink-0 items-center gap-3 px-4 md:h-[72px] md:px-10">
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger
          render={
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Ouvrir le menu</span>
            </Button>
          }
        />
        <SheetContent side="left" className="glass w-72 p-4">
          <SheetHeader className="p-0 text-left">
            <SheetTitle>
              <BrandMark />
            </SheetTitle>
          </SheetHeader>
          <Navigation showBrand={false} onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>
      <BrandMark className="md:hidden" />
      <div className="hidden flex-1 md:flex">
        <HeaderSearch />
      </div>
      <div className="ml-auto flex items-center gap-2">
        <ModeToggle />
      </div>
    </header>
  );
};
