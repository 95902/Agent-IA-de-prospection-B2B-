/* eslint-disable react-refresh/only-export-components */
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/react-router-devtools";
import { Navigation } from "@/components/ui/Navigation";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Header } from "@/components/Header";

const RootLayout = () => (
  <ThemeProvider defaultTheme="system" storageKey="app-theme">
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header />
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

export const Route = createRootRoute({
  component: RootLayout,
});
