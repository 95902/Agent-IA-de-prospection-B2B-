/* eslint-disable react-refresh/only-export-components */
import { useEffect } from "react";
import { createRootRoute, Outlet } from "@tanstack/react-router";
import { Navigation } from "@/components/ui/Navigation";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Header } from "@/components/Header";
import { useProfile } from "@/lib/profile";
import { RouterDevtools } from "@/components/Devtools";

/** Aurore + grain derrière le haut du shell ; intensité réglée dans le profil. */
const AuroraBackdrop = () => {
  const { aurora } = useProfile();
  useEffect(() => {
    document.documentElement.style.setProperty(
      "--aurora-opacity",
      String(aurora / 100),
    );
  }, [aurora]);
  return (
    <>
      <div className="aurora" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div className="grain" aria-hidden="true" />
    </>
  );
};

const RootLayout = () => (
  <ThemeProvider defaultTheme="dark" storageKey="app-theme">
    <div className="relative isolate flex h-dvh overflow-hidden bg-background text-foreground">
      <AuroraBackdrop />
      <aside className="glass relative z-10 hidden w-64 shrink-0 border-r border-sidebar-border px-4 py-5 md:block">
        <Navigation />
      </aside>
      <div className="relative z-10 flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto px-4 pb-12 md:px-10">
          <Outlet />
        </main>
      </div>
      <RouterDevtools />
    </div>
  </ThemeProvider>
);

export const Route = createRootRoute({
  component: RootLayout,
});
