"""« Affiner avec l'IA » du lanceur de campagne (POST /api/icp/parse).

Le front traduit la phrase du commercial avec un parseur DÉTERMINISTE ; les mots qu'il
n'a pas su mapper (« indépendants », « fintech »…) peuvent être confiés ici à Claude.

- API Claude uniquement (règle #6), AsyncAnthropic (règle #8), modèle configurable
  (`settings.claude_icp_parse_model`), jamais codé en dur.
- Sortie STRUCTURÉE (`output_config.format`) : codes NAF et départements restreints par
  `enum` aux listes vérifiées de `config/lexique_ciblage.fr.json` (règle #3 : aucune
  valeur métier dans le code). La réponse est re-validée ici (défense en profondeur).
- Même demande → même réponse : cache mémoire par phrase normalisée, sans nouvel appel.
- Code agnostique du modèle, comme le scoring : ni effort, ni temperature, ni thinking.
"""
from __future__ import annotations

import hashlib
import json
import logging
import unicodedata
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path

import anthropic
from jinja2 import Environment, FileSystemLoader

from config.settings import get_settings

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
_LEXIQUE_PATH = _ROOT / "config" / "lexique_ciblage.fr.json"
_JINJA_ENV = Environment(loader=FileSystemLoader(str(_ROOT / "prompts")), autoescape=False)

MAX_MOTS = 20          # mots « à vérifier » acceptés par requête
MAX_LEN_MOT = 60
_MAX_TOKENS = 1024     # sortie JSON courte ; une troncature est traitée comme une erreur
_CACHE_TAILLE = 256
_MAX_ITEMS = 20
_MAX_LEN_HYPOTHESE = 200


class IcpParseError(Exception):
    """Réponse de l'IA inexploitable (refus, troncature, JSON invalide)."""


@lru_cache
def lexique() -> dict:
    return json.loads(_LEXIQUE_PATH.read_text(encoding="utf-8"))


def codes_naf_autorises() -> list[str]:
    return sorted({n["code"] for s in lexique()["secteurs"] for n in s["naf"]})


def departements_autorises() -> list[str]:
    return [d["code"] for d in lexique()["departements"]]


def _liste(items: dict) -> dict:
    return {"type": "array", "items": items}


_ENTIER_OU_NULL = {"anyOf": [{"type": "integer"}, {"type": "null"}]}


def schema() -> dict:
    """Schéma JSON de la sortie (reconstruit à chaque appel : jamais muté partagé)."""
    proprietes = {
        "codes_naf": _liste({"type": "string", "enum": codes_naf_autorises()}),
        "departements": _liste({"type": "string", "enum": departements_autorises()}),
        "effectif_min": dict(_ENTIER_OU_NULL),
        "effectif_max": dict(_ENTIER_OU_NULL),
        "anciennete_min_ans": dict(_ENTIER_OU_NULL),
        "exiger_site_web": {"type": "boolean"},
        "exiger_email": {"type": "boolean"},
        "mots_cles_positifs": _liste({"type": "string"}),
        "mots_cles_negatifs": _liste({"type": "string"}),
        "non_traduits": _liste({"type": "string"}),
        "hypotheses": _liste({"type": "string"}),
    }
    return {
        "type": "object",
        "properties": proprietes,
        "required": list(proprietes),
        "additionalProperties": False,
    }


def _norm(texte: str) -> str:
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return " ".join(sans_accents.lower().split())


def nettoyer_mots(mots: list[str]) -> list[str]:
    """Mots d'entrée : sans vides ni doublons (à la casse/aux accents près), bornés."""
    vus: set[str] = set()
    propres: list[str] = []
    for mot in mots:
        m = " ".join(str(mot).split())[:MAX_LEN_MOT]
        if m and _norm(m) not in vus:
            vus.add(_norm(m))
            propres.append(m)
    return propres[:MAX_MOTS]


def cle_cache(phrase: str, mots: list[str]) -> str:
    brut = _norm(phrase) + "\x1f" + "\x1f".join(sorted(_norm(m) for m in mots))
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()


def _entier(valeur: object) -> int | None:
    return valeur if isinstance(valeur, int) and not isinstance(valeur, bool) and valeur >= 0 else None


def _textes(valeurs: object, *, minuscules: bool, max_len: int) -> list[str]:
    if not isinstance(valeurs, list):
        return []
    sortie: list[str] = []
    for v in valeurs:
        if not isinstance(v, str):
            continue
        t = " ".join(v.split())[:max_len]
        t = t.lower() if minuscules else t
        if t and t not in sortie:
            sortie.append(t)
    return sortie[:_MAX_ITEMS]


def valider(data: dict, mots: list[str]) -> dict:
    """Re-valide la sortie de l'IA : codes hors lexique écartés, effectif incohérent
    ignoré, « non_traduits » limité aux mots réellement transmis."""
    naf_ok = set(codes_naf_autorises())
    dep_ok = set(departements_autorises())
    emin, emax = _entier(data.get("effectif_min")), _entier(data.get("effectif_max"))
    if emin is not None and emax is not None and emax < emin:
        emin = emax = None
    mots_norm = {_norm(m): m for m in mots}
    return {
        "codes_naf": [c for c in dict.fromkeys(data.get("codes_naf") or []) if c in naf_ok],
        "departements": [d for d in dict.fromkeys(data.get("departements") or []) if d in dep_ok],
        "effectif_min": emin,
        "effectif_max": emax,
        "anciennete_min_ans": _entier(data.get("anciennete_min_ans")),
        "exiger_site_web": data.get("exiger_site_web") is True,
        "exiger_email": data.get("exiger_email") is True,
        "mots_cles_positifs": _textes(data.get("mots_cles_positifs"), minuscules=True, max_len=MAX_LEN_MOT),
        "mots_cles_negatifs": _textes(data.get("mots_cles_negatifs"), minuscules=True, max_len=MAX_LEN_MOT),
        "non_traduits": [
            mots_norm[_norm(m)]
            for m in _textes(data.get("non_traduits"), minuscules=False, max_len=MAX_LEN_MOT)
            if _norm(m) in mots_norm
        ],
        "hypotheses": _textes(data.get("hypotheses"), minuscules=False, max_len=_MAX_LEN_HYPOTHESE)[:10],
    }


def make_client() -> anthropic.AsyncAnthropic:
    """Client Claude (point d'injection des tests)."""
    return anthropic.AsyncAnthropic(api_key=get_settings().anthropic_api_key)


_cache: OrderedDict[str, dict] = OrderedDict()


async def affiner(phrase: str, mots: list[str]) -> tuple[dict, bool]:
    """Traduit les mots non mappés en critères. Renvoie (critères, depuis_cache).

    Lève `IcpParseError` si la réponse est inexploitable, `anthropic.APIError` si l'API
    est indisponible (l'appelant choisit le code HTTP).
    """
    mots = nettoyer_mots(mots)
    cle = cle_cache(phrase, mots)
    if cle in _cache:
        _cache.move_to_end(cle)
        return _cache[cle], True

    settings = get_settings()
    system = _JINJA_ENV.get_template("icp_parse_system.txt.j2").render(secteurs=lexique()["secteurs"])
    user = _JINJA_ENV.get_template("icp_parse_user.txt.j2").render(phrase=phrase.strip(), non_traduits=mots)

    async with make_client() as client:
        resp = await client.messages.create(
            model=settings.claude_icp_parse_model,       # jamais codé en dur (règle #6)
            max_tokens=_MAX_TOKENS,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema()}},
            # ⚠️ NI effort, NI temperature, NI thinking (agnostique du modèle, cf. scoring).
        )

    # Sortie garantie conforme au schéma SAUF refus ou troncature.
    if resp.stop_reason in ("refusal", "max_tokens"):
        raise IcpParseError(f"réponse de l'IA inexploitable ({resp.stop_reason})")
    try:
        texte = next(b.text for b in resp.content if getattr(b, "type", None) == "text")
        data = json.loads(texte)
    except (StopIteration, ValueError, TypeError) as exc:
        raise IcpParseError("réponse de l'IA inexploitable (JSON)") from exc
    if not isinstance(data, dict):
        raise IcpParseError("réponse de l'IA inexploitable (format)")

    resultat = valider(data, mots)
    _cache[cle] = resultat
    if len(_cache) > _CACHE_TAILLE:
        _cache.popitem(last=False)
    usage = getattr(resp, "usage", None)
    logger.info(
        "Affinage IA (%s) : %d mot(s) → %d NAF, %d dép. — tokens in=%s out=%s",
        settings.claude_icp_parse_model, len(mots), len(resultat["codes_naf"]),
        len(resultat["departements"]), getattr(usage, "input_tokens", "?"), getattr(usage, "output_tokens", "?"),
    )
    return resultat, False
