/**
 * Passage lanceur → formulaire avancé : le payload est déposé en sessionStorage,
 * lu par le formulaire à l'initialisation puis effacé après le montage (lecture
 * idempotente : StrictMode appelle deux fois les initialiseurs). Storage
 * indisponible → le formulaire s'ouvre simplement vide.
 */
const KEY = "campaign-prefill";

export type FormPrefill = Record<string, string | boolean>;

/** Payload API → valeurs de formulaire (listes en « a, b », nombres en texte). */
export function payloadToPrefill(payload: Record<string, unknown>): FormPrefill {
  const out: FormPrefill = {};
  for (const [k, v] of Object.entries(payload)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) out[k] = v.join(", ");
    else if (typeof v === "boolean") out[k] = v;
    else out[k] = String(v);
  }
  return out;
}

export function savePrefill(prefill: FormPrefill): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(prefill));
  } catch {
    // pas de pré-remplissage possible : sans conséquence
  }
}

export function readPrefill(): FormPrefill | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    return value && typeof value === "object" ? (value as FormPrefill) : null;
  } catch {
    return null;
  }
}

export function clearPrefill(): void {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    // rien à faire
  }
}

/** Applique un pré-remplissage aux valeurs par défaut d'un formulaire (types respectés). */
export function applyPrefill<T extends FormPrefill>(defaults: T, prefill: FormPrefill | null): T {
  const out = { ...defaults };
  if (!prefill) return out;
  for (const key of Object.keys(defaults) as (keyof T & string)[]) {
    const v = prefill[key];
    if (v !== undefined && typeof v === typeof defaults[key]) out[key] = v as T[typeof key];
  }
  return out;
}
