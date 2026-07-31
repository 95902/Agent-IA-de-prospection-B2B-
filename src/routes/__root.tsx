/* eslint-disable react-refresh/only-export-components */
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { Menu, Bot } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Navigation } from "@/components/ui/Navigation";

const RootLayout = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur md:px-6">
        <div className="flex items-center gap-3">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger>
              <Button variant="ghost" size="icon" className="md:hidden">
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
          <div className="flex items-center gap-2 font-bold text-lg">
            <Bot className="h-6 w-6 text-primary" />
            <span>Agent IA B2B</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Agent Actif
          </span>
        </div>
      </header>
      <div className="flex flex-1">
        <aside className="hidden w-64 border-r bg-card/50 p-4 md:block ">
          <Navigation />
        </aside>
        <main className="flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>
      <footer className="shrink-0 border-t bg-card/30 py-2.5 px-6 text-center text-xs text-muted-foreground">
        © 2026 Agent IA Prospection B2B
      </footer>
      <TanStackRouterDevtools initialIsOpen={false} />
    </div>
  );
};

export const Route = createRootRoute({
  component: RootLayout,
});
