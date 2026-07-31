/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";

function Campaigns() {
  return <div>Hello "/campagnes"!</div>;
}

export const Route = createFileRoute("/campagnes")({
  component: Campaigns,
});
