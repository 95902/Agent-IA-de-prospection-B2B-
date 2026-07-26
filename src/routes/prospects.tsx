/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";

const Prospects = () => {
  return <div>Hello "/Prospects"!</div>;
};

export const Route = createFileRoute("/prospects")({
  component: Prospects,
});
