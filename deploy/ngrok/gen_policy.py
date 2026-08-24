"""Génère la traffic-policy ngrok (OAuth + allowlist d'emails) depuis un fichier
d'adresses (une par ligne).

    python3 deploy/ngrok/gen_policy.py

Entrée  : NGROK_ALLOW_EMAILS   (défaut: /etc/ngrok/allow_emails.txt)
Sortie  : NGROK_POLICY_OUT     (défaut: /etc/ngrok/oauth-policy.yml)
Provider: NGROK_OAUTH_PROVIDER (défaut: google ; ex: microsoft, github)

Le match d'email est INSENSIBLE À LA CASSE (lowerAscii() des deux côtés), pour
qu'une majuscule dans l'allowlist ne bloque pas un login. Le script n'imprime QUE
le nombre d'adresses, jamais les adresses elles-mêmes (vie privée).

NB ngrok : un endpoint = UN seul provider (pas de choix Google/Microsoft sur la
même URL). Pour changer de provider, réexporter NGROK_OAUTH_PROVIDER puis relancer.
"""
from __future__ import annotations

import os
import sys

SRC = os.environ.get("NGROK_ALLOW_EMAILS", "/etc/ngrok/allow_emails.txt")
DST = os.environ.get("NGROK_POLICY_OUT", "/etc/ngrok/oauth-policy.yml")
PROVIDER = os.environ.get("NGROK_OAUTH_PROVIDER", "google")


def main() -> int:
    try:
        with open(SRC, encoding="utf-8") as fh:
            emails = [ln.strip() for ln in fh
                      if ln.strip() and not ln.lstrip().startswith("#")]
    except FileNotFoundError:
        print("ERREUR: fichier introuvable:", SRC, file=sys.stderr)
        return 1
    if not emails:
        print("ERREUR: aucune adresse dans", SRC, file=sys.stderr)
        return 1

    allow = ", ".join("'%s'" % e.lower() for e in emails)
    policy = (
        "on_http_request:\n"
        "  - actions:\n"
        "      - type: oauth\n"
        "        config:\n"
        "          provider: " + PROVIDER + "\n"
        "  - expressions:\n"
        '      - "!(actions.ngrok.oauth.identity.email.lowerAscii() in [' + allow + '])"\n'
        "    actions:\n"
        "      - type: deny\n"
    )
    with open(DST, "w", encoding="utf-8") as fh:
        fh.write(policy)
    print("OK: %d email(s) autorise(s) -> %s (provider=%s)" % (len(emails), DST, PROVIDER))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
