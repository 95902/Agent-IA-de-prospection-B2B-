import { lazy, Suspense, type FC } from "react";

// Devtools TanStack chargés uniquement en développement (absents du build prod).
type DevtoolsProps = { initialIsOpen?: boolean };
const NoDevtools: FC<DevtoolsProps> = () => null;

const RouterDevtoolsLazy = import.meta.env.DEV
  ? lazy(() =>
      import("@tanstack/react-router-devtools").then((m) => ({
        default: m.TanStackRouterDevtools,
      })),
    )
  : NoDevtools;

const QueryDevtoolsLazy = import.meta.env.DEV
  ? lazy(() =>
      import("@tanstack/react-query-devtools").then((m) => ({
        default: m.ReactQueryDevtools,
      })),
    )
  : NoDevtools;

export const RouterDevtools = () => (
  <Suspense fallback={null}>
    <RouterDevtoolsLazy initialIsOpen={false} />
  </Suspense>
);

export const QueryDevtools = () => (
  <Suspense fallback={null}>
    <QueryDevtoolsLazy initialIsOpen={false} />
  </Suspense>
);
