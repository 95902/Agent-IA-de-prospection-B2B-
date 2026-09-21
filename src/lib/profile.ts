import { useSyncExternalStore } from "react";
import { isKpiWindow, type KpiWindow } from "@/lib/kpiWindow";

/**
 * Profil local de l'utilisateur (Phase 2) : pas de comptes côté backend, donc
 * nom / rôle / préférences vivent dans le navigateur. Toute lecture/écriture du
 * storage est protégée (navigation privée, storage bloqué) et retombe sur les défauts.
 */
export type Profile = {
  name: string;
  role: string;
  kpiWindow: KpiWindow;
  /** Intensité de l'aurore, 0–100. */
  aurora: number;
  /** Derniers client / produit saisis dans le lanceur de campagne (pré-remplissage). */
  dernierClient: string;
  dernierProduit: string;
};

export const PROFILE_STORAGE_KEY = "b2b-profile";

export const DEFAULT_PROFILE: Profile = {
  name: "",
  role: "",
  kpiWindow: "all",
  aurora: 60,
  dernierClient: "",
  dernierProduit: "",
};

const MAX_TEXT = 80;

function clampAurora(value: unknown): number {
  const n = typeof value === "number" ? value : Number.NaN;
  if (!Number.isFinite(n)) return DEFAULT_PROFILE.aurora;
  return Math.min(100, Math.max(0, Math.round(n)));
}

function cleanText(value: unknown): string {
  return typeof value === "string" ? value.trim().slice(0, MAX_TEXT) : "";
}

/** Valide un objet inconnu (JSON du storage) champ par champ. */
export function parseProfile(raw: unknown): Profile {
  if (!raw || typeof raw !== "object") return { ...DEFAULT_PROFILE };
  const r = raw as Record<string, unknown>;
  return {
    name: cleanText(r.name),
    role: cleanText(r.role),
    kpiWindow: isKpiWindow(r.kpiWindow) ? r.kpiWindow : DEFAULT_PROFILE.kpiWindow,
    aurora: r.aurora === undefined ? DEFAULT_PROFILE.aurora : clampAurora(r.aurora),
    dernierClient: cleanText(r.dernierClient),
    dernierProduit: cleanText(r.dernierProduit),
  };
}

export function loadProfile(): Profile {
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
    return raw ? parseProfile(JSON.parse(raw)) : { ...DEFAULT_PROFILE };
  } catch {
    return { ...DEFAULT_PROFILE };
  }
}

/** Initiales pour l'avatar : « Marie Curie » → « MC », vide → "". */
export function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "";
  const first = parts[0][0] ?? "";
  const last = parts.length > 1 ? (parts[parts.length - 1][0] ?? "") : "";
  return (first + last).toUpperCase();
}

// --- store partagé (un seul état pour tous les composants abonnés) ---
let current: Profile | null = null;
const listeners = new Set<() => void>();

function snapshot(): Profile {
  if (current === null) current = loadProfile();
  return current;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function updateProfile(patch: Partial<Profile>): Profile {
  current = parseProfile({ ...snapshot(), ...patch });
  try {
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(current));
  } catch {
    // storage indisponible : le profil reste valable pour la session en cours
  }
  listeners.forEach((l) => l());
  return current;
}

/** Réinitialise le cache mémoire (tests). */
export function resetProfileCache(): void {
  current = null;
}

export function useProfile(): Profile {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}
