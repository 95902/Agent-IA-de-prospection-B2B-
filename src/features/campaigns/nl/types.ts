/**
 * Critères de ciblage issus d'une phrase en langage naturel, éditables avant
 * création du brouillon. Traduits en payload ICP (`utils/icp_payload.py`) par
 * `toIcpPayload`.
 */
export type SecteurCritere = {
  id: string;
  label: string;
  /** Codes NAF au format ICP : 4 chiffres + lettre, sans point (ex. 5510Z). */
  naf: string[];
};

export type ZoneCritere = {
  id: string;
  label: string;
  departements: string[];
};

export type Criteria = {
  secteurs: SecteurCritere[];
  zones: ZoneCritere[];
  effectif: { min: number | null; max: number | null } | null;
  ancienneteMin: number | null;
  exigerSiteWeb: boolean;
  exigerEmail: boolean;
  motsClesPositifs: string[];
  motsClesNegatifs: string[];
};

export type ParseResult = {
  criteria: Criteria;
  /** Mots significatifs non traduits en critère (à vérifier / confier à l'IA). */
  unmapped: string[];
  /** Interprétations faites par le parseur, montrées à l'utilisateur. */
  assumptions: string[];
};

export const EMPTY_CRITERIA: Criteria = {
  secteurs: [],
  zones: [],
  effectif: null,
  ancienneteMin: null,
  exigerSiteWeb: false,
  exigerEmail: false,
  motsClesPositifs: [],
  motsClesNegatifs: [],
};
