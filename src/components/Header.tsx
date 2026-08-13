import { Menu, Bot, RotateCcwClock, BellDot } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/Sheet";
import { Navigation } from "@/components/ui/Navigation";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/Avatar";
import { Input } from "@/components/ui/Input";
import { ModeToggle } from "@/components/ModeToggle";

export const Header = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 flex min-h-16 items-center justify-between border-b bg-background/95 backdrop-blur">
      <div className="flex items-center">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger>
            <Button variant="ghost" size="icon" className="md:hidden pl-4">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle Navigation</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <SheetHeader className="p-4 text-left border-b">
              <SheetTitle className="flex items-center gap-2">
                <Bot className="h-6 w-6 text-primary" />
                Agent Prospection
              </SheetTitle>
            </SheetHeader>
            <Navigation />
          </SheetContent>
        </Sheet>
        <div className="hidden pl-4 md:flex items-center gap-2 w-60 font-bold text-lg">
          <Bot className="h-6 w-6 text-primary" />
          <span className="text-nowrap">B2B Intelligence</span>
        </div>
      </div>
      <div className="hidden md:flex flex-1 px-4">
        <Input placeholder="Rechercher..." />
      </div>
      <div className="flex items-center">
        <div className="flex gap-2 items-center px-2">
          <Button variant="ghost" size="icon">
            <BellDot className="h-5 w-5" />
            <span className="sr-only">Notifications</span>
          </Button>
          <Button variant="ghost" size="icon">
            <RotateCcwClock className="h-5 w-5" />
          </Button>
          <ModeToggle />
        </div>
        <div className="h-full flex items-center gap-2 border-l px-4">
          <div className="flex flex-col">
            <span className="font-semibold text-nowrap">Taupin Fabien</span>
            <p className="text-sm text-muted-foreground text-nowrap">
              Directeur du monde
            </p>
          </div>
          <Avatar size="lg">
            <AvatarImage
              src="https://github.com/shadcn.png"
              alt="@shadcn"
              className="grayscale"
            />
            <AvatarFallback>CN</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  );
};
