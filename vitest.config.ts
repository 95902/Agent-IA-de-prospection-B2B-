import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Config de test séparée de vite.config.ts : pas de plugin TanStack Router
// (évite de régénérer routeTree.gen.ts pendant les tests).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": `${import.meta.dirname}/src`,
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
  },
});
