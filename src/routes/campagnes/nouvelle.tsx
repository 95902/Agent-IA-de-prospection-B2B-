import { createFileRoute } from "@tanstack/react-router";
import { Launcher } from "@/features/campaigns/components/Launcher";

export const Route = createFileRoute("/campagnes/nouvelle")({
  component: Launcher,
});
