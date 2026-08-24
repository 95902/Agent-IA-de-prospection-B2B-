# Déploiement — front servi par l'API + accès public OAuth (ngrok)

Codifie la « Slice 3 » : le front est servi par l'API sur une seule origine, et l'app
est exposée sur **un lien public unique protégé par login Google** (ngrok), sans ouvrir
de port entrant ni toucher au DNS d'un domaine.

> Ces artefacts vivaient jusqu'ici en scp non-tracké sur le VPS. Ce dossier `deploy/` les
> rend reproductibles. Fichiers versionnés = **templates** ; les vraies valeurs (domaine,
> emails, authtoken) restent hors git.

## ⚠️ Ordre de fusion (important)

Cette PR **se fusionne APRÈS #119** : `deploy/serve.py` fait `from api.main import app`,
et `api/` n'arrive sur `main` qu'avec **#119** (qui remplace **#117** — fermer #117, ne pas
le fusionner). Le front (dist/) se construit depuis **#118**.

Séquence recommandée : **#119** (ferme #117) → **#118** → **cette PR** → puis, sur le VPS,
`rm -rf api/` **avant** `git pull` (sinon l'`api/` scp'é non-tracké bloque le merge).

## Prérequis

- PR **#119** et **#118** fusionnées sur `main` (api/ + front présents).
- Node local pour builder le front (pas de node sur le VPS → build local + scp).
- `fastapi` / `uvicorn` dans le venv du VPS (déjà dans `requirements.txt`).
- Compte ngrok + **agent authtoken** (dashboard → *Your Authtoken*, PAS l'API key), et un
  **dev domain** gratuit (dashboard → *Domains*).

## 1. Builder le front (en local)

Base d'API **vide** ⇒ le front appelle `/api/...` en relatif (même origine que l'API) :

```bash
VITE_API_URL= npm run build          # (ou: pnpm build) ; produit dist/
grep -rl "localhost:8000" dist && echo "KO: base non vide" || echo "OK: appels /api relatifs"
```

## 2. Déposer dist/ sur le VPS

`tar` préserve les octets (contrairement à `git archive` sous Windows qui réécrit en CRLF) :

```bash
tar -C dist -cf - . | ssh -i <clé> ubuntu@"$IP" \
  'rm -rf /opt/prospection-b2b/dist && mkdir -p /opt/prospection-b2b/dist && tar -C /opt/prospection-b2b/dist -xf -'
```

## 3. Service API + front (systemd)

```bash
sudo cp deploy/systemd/prospection-api.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now prospection-api
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/            # 200 (front)
curl -s http://127.0.0.1:8000/api/health                                    # {"status":"ok"}
```

Le unit lance `uvicorn deploy.serve:app` (front dist/ + /api), lié `127.0.0.1:8000`,
`Restart=always`, démarrage au boot.

## 4. Agent ngrok

```bash
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt-get update && sudo apt-get install -y ngrok
ngrok config add-authtoken <VOTRE_AGENT_AUTHTOKEN>     # écrit ~/.config/ngrok/ngrok.yml
```

## 5. Gate OAuth + allowlist

```bash
sudo mkdir -p /etc/ngrok && sudo chown "$USER" /etc/ngrok
printf '%s\n' 'toi@gmail.com' > /etc/ngrok/allow_emails.txt     # une adresse par ligne
python3 deploy/ngrok/gen_policy.py                              # -> /etc/ngrok/oauth-policy.yml
```

`gen_policy.py` génère un match **insensible à la casse** (`lowerAscii()`). Provider par
défaut `google` ; pour Outlook/Hotmail : `NGROK_OAUTH_PROVIDER=microsoft python3 deploy/ngrok/gen_policy.py`.
**Un endpoint = un seul provider** (pas de choix Google/Microsoft sur la même URL).

## 6. Service ngrok

Éditer `ExecStart` de `deploy/systemd/ngrok-prospection.service` : remplacer
`VOTRE-DOMAINE.ngrok-free.dev` par votre dev domain. Puis :

```bash
sudo cp deploy/systemd/ngrok-prospection.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now ngrok-prospection
# Vérif depuis l'extérieur : doit rediriger vers le login (gate actif), pas servir l'app.
curl -sI https://VOTRE-DOMAINE.ngrok-free.dev | grep -iE '^HTTP/|^location:'   # 302 -> idp.ngrok.com
```

## Ajouter / retirer un testeur

```bash
echo 'coequipier@gmail.com' >> /etc/ngrok/allow_emails.txt      # ">>" (append, pas ">")
python3 deploy/ngrok/gen_policy.py
sudo systemctl restart ngrok-prospection
```

## Limites & pièges

- **ngrok gratuit** : 1 domaine, **5 utilisateurs/mois** (OAuth), 20 000 req & 1 Go/mois.
  Au-delà → payer ou passer à Cloudflare Access (migration DNS complète requise, 50 users).
- **Aucun port entrant** ouvert : l'agent ngrok compose vers l'extérieur (ufw reste sur 22).
- **CRLF** : après tout transfert de `.py`, revérifier `git hash-object` / `file` (Windows).
- **`rm -rf api/` avant `git pull`** au premier pull post-#119 (untracked scp qui bloque).
- Ne jamais committer `deploy/ngrok/allow_emails.txt` ni `oauth-policy.yml` (gitignorés).

## Migration depuis l'état intérimaire

Le VPS tourne aujourd'hui avec `uvicorn api.main:app` **plus** un mount SPA collé en fin de
`api/main.py` (scp, non-tracké, sauvegarde `api/main.py.bak`). En adoptant cette PR :
après `rm -rf api/ && git pull` (api/main.py redevient propre), basculer le service sur
`deploy.serve:app` (déjà le cas dans le unit ci-dessus) — le front-serving vient alors de
`deploy/serve.py`, plus de l'append. Aucun autre changement.
