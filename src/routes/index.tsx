/* eslint-disable react-refresh/only-export-components */
import { createFileRoute } from "@tanstack/react-router";

const Index = () => {
  return <div>Hello "/"!</div>;
};

export const Route = createFileRoute("/")({
  component: Index,
});
