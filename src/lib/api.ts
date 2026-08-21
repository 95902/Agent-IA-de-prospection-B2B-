/**
 * Client de l'API de lecture du pipeline (#116, Slice 2).
 *
 * Le front consomme l'API FastAPI (api/main.py) plutôt que des données mock.
 * L'URL de base vient de VITE_API_URL (voir .env.example) ; défaut localhost:8000.
 */

const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

// --- Types miroir des DTO de l'API (api/models.py) -------------------------
export interface Campagne {
  id: string;
  nom: string;
  statut: string;
  prospects_collectes: number;
  prospects_qualifies: number;
}

export interface ProspectRow {
  id: string;
  nom_entreprise: string;
  ville: string | null;
  departement: string | null;
  code_naf: string | null;
  score_final: number;
  statut: string;
  telephone: string | null;
  email: string | null;
  site_web: string | null;
}

export interface ProspectPage {
  total: number;
  limit: number;
  offset: number;
  items: ProspectRow[];
}

export interface Kpis {
  portee: string;
  collectes: number;
  qualifies: number;
  taux_tel: number;
  taux_email: number;
  pct_qualifies: number;
  score_moy_qualifies: number | null;
  cout_estime_eur: number;
}

// --- Fetch helper ----------------------------------------------------------
async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) {
    throw new Error(`API ${res.status} ${res.statusText} — ${path}`);
  }
  return (await res.json()) as T;
}

function qs(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

// --- Endpoints -------------------------------------------------------------
export const getCampagnes = () => apiGet<Campagne[]>("/api/campagnes");

export const getCampagne = (id: string) => apiGet<Campagne>(`/api/campagnes/${id}`);

export const getProspects = (params: {
  campagneId?: string;
  statut?: string;
  limit?: number;
  offset?: number;
} = {}) =>
  apiGet<ProspectPage>(
    `/api/prospects${qs({
      campagne_id: params.campagneId,
      statut: params.statut,
      limit: params.limit,
      offset: params.offset,
    })}`,
  );

export const getKpis = (params: { campagneId?: string; sinceDays?: number } = {}) =>
  apiGet<Kpis>(
    `/api/kpis${qs({ campagne_id: params.campagneId, since_days: params.sinceDays })}`,
  );
