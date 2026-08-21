"""Rapport hebdo — KPIs de campagne (#38).

Synthétise les métriques de la semaine (ou d'une campagne) depuis PostgreSQL et,
optionnellement, envoie le rapport par email via Brevo. **Sans clé Brevo NI
destinataire configurés, le rapport est seulement imprimé/écrit — jamais envoyé.**

KPIs suivis (docs/PRD.md §6), avec leur cible :
    - taux enrichissement téléphone     ≥ 40 %
    - taux enrichissement email         ≥ 20 %
    - % prospects qualifiés (score≥60)  ≥ 30 %   (seuil pipeline `_SEUIL_QUALIFIE`)
    - score moyen des qualifiés         ≥ 65/100
    - coût / prospect qualifié          ≤ 0,15 €   (estimation, cf. settings)
    - taux appels → RDV                 ≥ 2 %

Aucune valeur métier codée en dur : les seuils KPI viennent du PRD (constantes de
reporting, pas un ICP), les coûts unitaires viennent de `settings` (règle #3).

Usage :
    python scripts/rapport_hebdo.py                      # 7 derniers jours → stdout (texte)
    python scripts/rapport_hebdo.py --since-days 14
    python scripts/rapport_hebdo.py --campagne-id <uuid> # une campagne précise
    python scripts/rapport_hebdo.py --format html --out rapport.html
    python scripts/rapport_hebdo.py --send               # via Brevo (exige clé + destinataire)
"""
from __future__ import annotations

import argparse
import asyncio
import codecs
import io
import sys
import uuid
from datetime import date
from pathlib import Path

from pydantic import BaseModel

# Permet `python scripts/rapport_hebdo.py` depuis la racine du repo sans install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Cibles KPI — docs/PRD.md §6 (constantes de reporting, pas un ICP).
CIBLE_TEL = 40.0
CIBLE_EMAIL = 20.0
CIBLE_PCT_QUALIFIES = 30.0
CIBLE_SCORE_QUALIFIES = 65.0
CIBLE_COUT_PAR_QUALIFIE = 0.15
CIBLE_TAUX_RDV = 2.0

_APPEL_STATUTS = ("appele", "rdv", "refus", "absent")


def _force_utf8_stdio() -> None:
    """stdout/stderr en UTF-8 — sinon les accents crashent sur console cp1252 Windows."""
    for stream in (sys.stdout, sys.stderr):
        enc = getattr(stream, "encoding", "") or ""
        try:
            if codecs.lookup(enc).name != "utf-8":
                reconfigure = getattr(stream, "reconfigure", None)
                if callable(reconfigure):
                    reconfigure(encoding="utf-8", errors="replace")
        except (LookupError, TypeError, ValueError, OSError, io.UnsupportedOperation):
            pass


def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total else 0.0


class CampagneKPI(BaseModel):
    nom: str
    collectes: int
    qualifies: int
    avec_tel: int
    avec_email: int
    score_moy_qualifies: float | None

    @property
    def pct_qualifies(self) -> float:
        return _pct(self.qualifies, self.collectes)


class Prospect(BaseModel):
    nom_entreprise: str
    code_naf: str | None
    score_final: int
    telephone: str | None
    email: str | None


class Rapport(BaseModel):
    """Vue agrégée d'une fenêtre (semaine) ou d'une campagne."""
    portee: str                 # ex. "7 derniers jours" / "campagne <nom>"
    collectes: int
    qualifies: int
    avec_tel: int
    avec_email: int
    score_moy_qualifies: float | None
    appels: int
    rdv: int
    cout_estime_eur: float
    campagnes: list[CampagneKPI]
    top_file: list[Prospect]

    # --- KPIs dérivés (docs/PRD.md §6) ---
    @property
    def taux_tel(self) -> float: return _pct(self.avec_tel, self.collectes)
    @property
    def taux_email(self) -> float: return _pct(self.avec_email, self.collectes)
    @property
    def pct_qualifies(self) -> float: return _pct(self.qualifies, self.collectes)
    @property
    def taux_rdv(self) -> float | None:
        return _pct(self.rdv, self.appels) if self.appels else None
    @property
    def cout_par_qualifie(self) -> float | None:
        return round(self.cout_estime_eur / self.qualifies, 4) if self.qualifies else None


# --------------------------------------------------------------------------- #
#  Collecte des KPIs
# --------------------------------------------------------------------------- #
async def collecter(conn, *, since_days: int, campagne_id: str | None) -> Rapport:
    """Agrège les KPIs sur une fenêtre glissante OU une campagne précise."""
    from config.settings import get_settings
    settings = get_settings()

    if campagne_id is not None:
        where, params = "p.campagne_id = $1", [uuid.UUID(campagne_id)]
        nom = await conn.fetchval("SELECT nom FROM campagnes WHERE id = $1", uuid.UUID(campagne_id))
        if nom is None:
            raise SystemExit(f"Campagne introuvable : {campagne_id}")
        portee = f"campagne « {nom} »"
    else:
        where, params = "p.created_at >= NOW() - make_interval(days => $1::int)", [since_days]
        portee = f"{since_days} derniers jours"

    glob = await conn.fetchrow(
        f"""
        SELECT
          count(*)                                                    AS collectes,
          count(*) FILTER (WHERE p.statut = 'qualifie')               AS qualifies,
          count(*) FILTER (WHERE p.telephone IS NOT NULL AND p.telephone <> '') AS avec_tel,
          count(*) FILTER (WHERE p.email     IS NOT NULL AND p.email     <> '') AS avec_email,
          avg(p.score_final) FILTER (WHERE p.statut = 'qualifie')     AS score_moy_q,
          count(*) FILTER (WHERE p.statut = ANY($2))                  AS appels,
          count(*) FILTER (WHERE p.statut = 'rdv')                    AS rdv
        FROM prospects p
        WHERE {where}
        """,
        *params, list(_APPEL_STATUTS),
    )

    par_camp = await conn.fetch(
        f"""
        SELECT cmp.nom AS nom,
          count(*)                                                    AS collectes,
          count(*) FILTER (WHERE p.statut = 'qualifie')               AS qualifies,
          count(*) FILTER (WHERE p.telephone IS NOT NULL AND p.telephone <> '') AS avec_tel,
          count(*) FILTER (WHERE p.email     IS NOT NULL AND p.email     <> '') AS avec_email,
          avg(p.score_final) FILTER (WHERE p.statut = 'qualifie')     AS score_moy_q
        FROM prospects p
        JOIN campagnes cmp ON cmp.id = p.campagne_id
        WHERE {where}
        GROUP BY cmp.nom
        HAVING count(*) > 0
        ORDER BY qualifies DESC, collectes DESC
        """,
        *params,
    )

    top = await conn.fetch(
        f"""
        SELECT p.nom_entreprise, p.code_naf, p.score_final, p.telephone, p.email
        FROM prospects p
        WHERE {where} AND p.statut = 'qualifie'
        ORDER BY p.score_final DESC, p.created_at ASC
        LIMIT 10
        """,
        *params,
    )

    collectes = glob["collectes"] or 0
    cout = round(
        collectes * (settings.cout_claude_par_prospect_eur + settings.cout_tavily_par_prospect_eur), 3
    )
    return Rapport(
        portee=portee,
        collectes=collectes,
        qualifies=glob["qualifies"] or 0,
        avec_tel=glob["avec_tel"] or 0,
        avec_email=glob["avec_email"] or 0,
        score_moy_qualifies=(round(glob["score_moy_q"], 1) if glob["score_moy_q"] is not None else None),
        appels=glob["appels"] or 0,
        rdv=glob["rdv"] or 0,
        cout_estime_eur=cout,
        campagnes=[CampagneKPI(
            nom=r["nom"], collectes=r["collectes"], qualifies=r["qualifies"],
            avec_tel=r["avec_tel"], avec_email=r["avec_email"],
            score_moy_qualifies=(round(r["score_moy_q"], 1) if r["score_moy_q"] is not None else None),
        ) for r in par_camp],
        top_file=[Prospect(
            nom_entreprise=r["nom_entreprise"], code_naf=r["code_naf"],
            score_final=r["score_final"], telephone=r["telephone"], email=r["email"],
        ) for r in top],
    )


# --------------------------------------------------------------------------- #
#  Rendu
# --------------------------------------------------------------------------- #
def _flag(valeur: float | None, cible: float, *, sens: str = "min") -> str:
    """✅/⚠️ selon que la valeur atteint la cible (`min` = ≥ cible, `max` = ≤ cible)."""
    if valeur is None:
        return "  n/a"
    ok = valeur >= cible if sens == "min" else valeur <= cible
    return "  ✅" if ok else "  ⚠️"


def rendre_texte(r: Rapport) -> str:
    L: list[str] = []
    L.append("=" * 60)
    L.append(f"  RAPPORT DE PROSPECTION — {r.portee}")
    L.append(f"  généré le {date.today().isoformat()}")
    L.append("=" * 60)
    L.append("")
    L.append(f"  Prospects collectés .......... {r.collectes}")
    L.append(f"  Prospects qualifiés (≥60) .... {r.qualifies}")
    L.append("")
    L.append("  KPIs (cible PRD §6)")
    L.append("  " + "-" * 46)
    L.append(f"  Taux téléphone ....... {r.taux_tel:5.1f} %   (≥{CIBLE_TEL:.0f}%){_flag(r.taux_tel, CIBLE_TEL)}")
    L.append(f"  Taux email ........... {r.taux_email:5.1f} %   (≥{CIBLE_EMAIL:.0f}%){_flag(r.taux_email, CIBLE_EMAIL)}")
    L.append(f"  % qualifiés .......... {r.pct_qualifies:5.1f} %   (≥{CIBLE_PCT_QUALIFIES:.0f}%){_flag(r.pct_qualifies, CIBLE_PCT_QUALIFIES)}")
    smq = f"{r.score_moy_qualifies:5.1f}  " if r.score_moy_qualifies is not None else "  n/a  "
    L.append(f"  Score moy qualifiés .. {smq}    (≥{CIBLE_SCORE_QUALIFIES:.0f}){_flag(r.score_moy_qualifies, CIBLE_SCORE_QUALIFIES)}")
    cpq = f"{r.cout_par_qualifie:.3f} €" if r.cout_par_qualifie is not None else " n/a  "
    L.append(f"  Coût / qualifié ...... {cpq:>8}  (≤{CIBLE_COUT_PAR_QUALIFIE:.2f}€){_flag(r.cout_par_qualifie, CIBLE_COUT_PAR_QUALIFIE, sens='max')}")
    if r.taux_rdv is not None:
        L.append(f"  Appels → RDV ......... {r.taux_rdv:5.1f} %   (≥{CIBLE_TAUX_RDV:.0f}%){_flag(r.taux_rdv, CIBLE_TAUX_RDV)}")
    else:
        L.append(f"  Appels → RDV ......... n/a  (aucun appel journalisé)")
    L.append(f"  Coût API estimé ...... {r.cout_estime_eur:.2f} €")
    L.append("")

    if r.campagnes:
        L.append("  Par campagne")
        L.append("  " + "-" * 46)
        L.append(f"  {'campagne':<28}{'coll.':>6}{'qual.':>6}{'tél%':>6}")
        for c in r.campagnes:
            nom = (c.nom[:26] + "…") if len(c.nom) > 27 else c.nom
            L.append(f"  {nom:<28}{c.collectes:>6}{c.qualifies:>6}{_pct(c.avec_tel, c.collectes):>6.1f}")
        L.append("")

    if r.top_file:
        L.append("  File d'appel — top qualifiés")
        L.append("  " + "-" * 46)
        for i, p in enumerate(r.top_file, 1):
            canal = "☎" if p.telephone else ("@" if p.email else "·")
            L.append(f"  {i:>2}. [{p.score_final:>3}] {canal} {p.nom_entreprise[:40]}")
        L.append("")
    L.append("=" * 60)
    return "\n".join(L)


def _kpi_html_row(label: str, valeur: str, ok: bool | None) -> str:
    badge = {True: ("#15803d", "✓"), False: ("#b45309", "⚠"), None: ("#8496a5", "–")}[ok]
    return (
        f'<tr><td style="padding:6px 10px;color:#586a7a">{label}</td>'
        f'<td style="padding:6px 10px;font-weight:600;text-align:right;font-variant-numeric:tabular-nums">{valeur}</td>'
        f'<td style="padding:6px 10px;text-align:center;color:{badge[0]}">{badge[1]}</td></tr>'
    )


def rendre_html(r: Rapport) -> str:
    """HTML email-friendly (styles inline — les clients mail ignorent <style>)."""
    def ok(v, c, sens="min"):
        return None if v is None else (v >= c if sens == "min" else v <= c)
    rows = [
        _kpi_html_row("Taux téléphone", f"{r.taux_tel:.1f} % (≥{CIBLE_TEL:.0f})", ok(r.taux_tel, CIBLE_TEL)),
        _kpi_html_row("Taux email", f"{r.taux_email:.1f} % (≥{CIBLE_EMAIL:.0f})", ok(r.taux_email, CIBLE_EMAIL)),
        _kpi_html_row("% qualifiés (≥60)", f"{r.pct_qualifies:.1f} % (≥{CIBLE_PCT_QUALIFIES:.0f})", ok(r.pct_qualifies, CIBLE_PCT_QUALIFIES)),
        _kpi_html_row("Score moyen qualifiés",
                      (f"{r.score_moy_qualifies:.1f} (≥{CIBLE_SCORE_QUALIFIES:.0f})" if r.score_moy_qualifies is not None else "n/a"),
                      ok(r.score_moy_qualifies, CIBLE_SCORE_QUALIFIES)),
        _kpi_html_row("Coût / qualifié",
                      (f"{r.cout_par_qualifie:.3f} € (≤{CIBLE_COUT_PAR_QUALIFIE:.2f})" if r.cout_par_qualifie is not None else "n/a"),
                      ok(r.cout_par_qualifie, CIBLE_COUT_PAR_QUALIFIE, "max")),
    ]
    top = "".join(
        f'<li style="margin:3px 0"><b>{p.score_final}</b> — {p.nom_entreprise}'
        f'{" ☎" if p.telephone else (" @" if p.email else "")}</li>'
        for p in r.top_file
    )
    return f"""<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;color:#17212b">
  <h2 style="font-size:19px;margin:0 0 2px">Rapport de prospection</h2>
  <p style="color:#586a7a;margin:0 0 16px;font-size:13px">{r.portee} · généré le {date.today().isoformat()}</p>
  <p style="font-size:15px;margin:0 0 14px"><b>{r.collectes}</b> prospects collectés ·
     <b>{r.qualifies}</b> qualifiés (score ≥ 60)</p>
  <table style="border-collapse:collapse;width:100%;font-size:14px;border:1px solid #d6dee5;border-radius:8px">
    <tbody>{''.join(rows)}</tbody>
  </table>
  <p style="color:#586a7a;font-size:12px;margin:10px 0 0">Coût API estimé : {r.cout_estime_eur:.2f} €</p>
  {'<h3 style="font-size:15px;margin:18px 0 6px">File d&rsquo;appel — top qualifiés</h3><ol style="padding-left:20px;font-size:13px;margin:0">' + top + '</ol>' if top else ''}
</div>"""


# --------------------------------------------------------------------------- #
#  Envoi Brevo (inerte sans config)
# --------------------------------------------------------------------------- #
async def envoyer_brevo(sujet: str, html: str) -> None:
    """Envoie via Brevo. HALT clair si clé/destinataire manquants (jamais d'envoi implicite)."""
    import httpx
    from config.settings import get_settings
    s = get_settings()
    dests = [e.strip() for e in (s.rapport_email_to or "").split(",") if e.strip()]
    if not s.brevo_api_key or not s.rapport_email_from or not dests:
        raise SystemExit(
            "Envoi Brevo impossible : renseigner BREVO_API_KEY, RAPPORT_EMAIL_FROM et "
            "RAPPORT_EMAIL_TO dans .env. (Le rapport a été généré ; rien n'a été envoyé.)"
        )
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={"api-key": s.brevo_api_key, "accept": "application/json",
                     "content-type": "application/json"},
            json={"sender": {"email": s.rapport_email_from},
                  "to": [{"email": e} for e in dests],
                  "subject": sujet, "htmlContent": html},
        )
        resp.raise_for_status()
    print(f"✓ Rapport envoyé à {', '.join(dests)}")


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
async def _run(args: argparse.Namespace) -> int:
    from utils import db
    try:
        pool = await db.get_pg_pool()
        async with pool.acquire() as conn:
            rapport = await collecter(conn, since_days=args.since_days, campagne_id=args.campagne_id)
    finally:
        await db.close()

    sortie = rendre_html(rapport) if args.format == "html" else rendre_texte(rapport)
    if args.out:
        Path(args.out).write_text(sortie, encoding="utf-8")
        print(f"✓ Rapport écrit dans {args.out}")
    else:
        print(sortie)

    if args.send:
        sujet = f"Prospection — {rapport.portee} — {rapport.qualifies} qualifiés"
        await envoyer_brevo(sujet, rendre_html(rapport))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Rapport hebdo de KPIs de prospection (#38).")
    p.add_argument("--since-days", type=int, default=7,
                   help="Fenêtre glissante en jours (défaut : 7). Ignoré si --campagne-id.")
    p.add_argument("--campagne-id", metavar="UUID", default=None,
                   help="Restreint le rapport à une campagne précise.")
    p.add_argument("--format", choices=("text", "html"), default="text",
                   help="Format de sortie (défaut : text).")
    p.add_argument("--out", metavar="PATH", default=None,
                   help="Écrit le rapport dans un fichier au lieu de stdout.")
    p.add_argument("--send", action="store_true",
                   help="Envoie le rapport par email via Brevo (exige clé + destinataire).")
    return p


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdio()
    args = _build_parser().parse_args(argv)
    if args.campagne_id is not None:
        try:
            uuid.UUID(args.campagne_id)
        except ValueError:
            raise SystemExit(f"--campagne-id invalide : '{args.campagne_id}' (UUID attendu).")
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
