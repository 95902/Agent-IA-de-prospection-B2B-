/** Fenêtre temporelle des KPI du tableau de bord (switch 7 j / 30 j / Tout). */
export type KpiWindow = "7" | "30" | "all";

export const KPI_WINDOWS: ReadonlyArray<{
  value: KpiWindow;
  label: string;
  description: string;
}> = [
  { value: "7", label: "7 j", description: "7 derniers jours" },
  { value: "30", label: "30 j", description: "30 derniers jours" },
  { value: "all", label: "Tout", description: "Tout l'historique" },
];

/**
 * « Tout » = une fenêtre de 100 ans : `/api/kpis` exige `since_days >= 1`, et une
 * très grande fenêtre équivaut à « depuis toujours » sans changer l'API.
 */
export const ALL_TIME_DAYS = 36500;

export function sinceDaysFor(window: KpiWindow): number {
  return window === "all" ? ALL_TIME_DAYS : Number(window);
}

export function isKpiWindow(value: unknown): value is KpiWindow {
  return value === "7" || value === "30" || value === "all";
}

export function kpiWindowDescription(window: KpiWindow): string {
  return KPI_WINDOWS.find((w) => w.value === window)?.description ?? "";
}
