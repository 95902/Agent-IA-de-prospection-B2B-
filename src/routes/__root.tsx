/* eslint-disable react-refresh/only-export-components */
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
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
import { ThemeProvider } from "@/components/ThemeProvider";
import { ModeToggle } from "@/components/ModeToggle";

const RootLayout = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <ThemeProvider defaultTheme="system" storageKey="app-theme">
      <div className="flex h-screen flex-col bg-background text-foreground">
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
            <div className="h-full flex items-center gap-4 border-l px-2">
              <div className="flex flex-col ">
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
        <div className="flex h-screen flex-1 overflow-hidden">
          <aside className="hidden w-64 border-r bg-card/50 p-4 md:block ">
            <Navigation />
          </aside>
          <main className="flex-1 p-6 overflow-y-scroll">
            <Outlet />
          </main>
        </div>
        <footer className="shrink-0 border-t bg-card/30 py-2.5 px-6 text-center text-xs text-muted-foreground">
          © 2026 Agent IA Prospection B2B
        </footer>
        <TanStackRouterDevtools initialIsOpen={false} />
      </div>
    </ThemeProvider>
  );
};

export const Route = createRootRoute({
  component: RootLayout,
});
