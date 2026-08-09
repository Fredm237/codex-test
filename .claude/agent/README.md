# Agent FILON — architecture

Trois fichiers, trois rôles. Rien d'autre : un agent qui a besoin d'un
framework pour tenir debout ne tient pas debout.

| Fichier | Rôle |
|---|---|
| `mission.py` | l'état qui survit à la perte de contexte |
| `web.py` | une seule porte vers le web, avec ordre de repli imposé |
| `garde-secrets.sh` | refuse qu'un secret parte dans un commit |

Les règles de comportement sont dans `CLAUDE.md`, à la racine — c'est lui qui
est chargé à chaque session.

---

## mission.py — l'état de mission

Le contexte d'une session se résume et finit par s'effacer. Un fichier, non.
Une mission longue s'écrit dans `.claude/agent/missions/courante.json`,
versionné avec le dépôt et relisible d'une session à l'autre.

```bash
python3 .claude/agent/mission.py init "Refonte du catalogue"
python3 .claude/agent/mission.py add t1 "Auditer les jetons" --outil Read
python3 .claude/agent/mission.py add t2 "Réécrire" --depend t1 --attendu "build vert"
python3 .claude/agent/mission.py next     # ce qui est exécutable maintenant
python3 .claude/agent/mission.py start t1
python3 .claude/agent/mission.py verify t1 "84 jetons relus, 24 orphelins"
python3 .claude/agent/mission.py done t1 --obtenu "audit complet"
python3 .claude/agent/mission.py show
python3 .claude/agent/mission.py archive
```

Deux comportements méritent d'être connus :

- **`done` est refusé sans `verify`.** Une commande qui rend 0 n'est pas une
  preuve. Pour clore malgré tout, il faut `--sans-preuve`, et l'assumer.
- **`next` rend *toutes* les tâches débloquées.** Plusieurs lignes en sortie
  veulent dire : ces tâches sont indépendantes, elles peuvent partir en
  parallèle.

Le `journal` du fichier garde qui a fait quoi et quand — c'est
l'observabilité, et elle ne contient jamais de secret.

## web.py — l'accès web

L'environnement a plusieurs voies vers le web et elles n'ont pas les mêmes
droits. Les essayer au hasard produit des conclusions fausses : « le site est
mort » alors que c'est l'outil qui est bloqué. `web.py` impose l'ordre,
mémorise ce qui est définitivement fermé, et annonce toujours **par quelle
voie** le résultat est arrivé (sur `stderr`, pour ne pas polluer la sortie).

```bash
python3 .claude/agent/web.py etat                      # sonde réellement chaque voie
python3 .claude/agent/web.py lire https://exemple.be   # firecrawl → curl → apify
python3 .claude/agent/web.py chercher "cashback 2026"
python3 .claude/agent/web.py social https://www.instagram.com/w.wearebrand/
```

`RETRY → FALLBACK → RECOVERY` : trois tentatives à attente croissante, puis
la voie suivante. Un `4xx` définitif n'est pas réessayé — insister sur un
refus de politique ne fait que perdre du temps.

### Ce qui a été mesuré sur cet environnement

- `curl` passe par `$HTTPS_PROXY` et fonctionne.
- **Le navigateur local ne peut pas sortir.** Chromium prend un
  `ERR_CONNECTION_RESET` sur tout domaine externe, y compris à travers le
  proxy. C'est la politique d'egress, pas une panne : le README du proxy
  interdit de la contourner. Playwright reste utile pour `localhost` — c'est
  ainsi que le rendu de `filon-web` a été vérifié.
- **Le port du proxy est dynamique.** Il a changé trois fois en une session
  (40829 → 40259 → 39343). Lire `$HTTPS_PROXY`, ne jamais coder un port.
- Firecrawl fonctionne, **sauf refus de politique** : Instagram est refusé
  explicitement (« we do not support this site »), définitivement.
- **Apify est la seule voie vers Instagram.** Elle a rendu le profil, 18
  posts et les vidéos de `w.wearebrand`.
- Le sandbox `higgsfield` (E2B) a, lui, un **réseau externe libre**
  (Instagram y répond 302) et un vrai ffmpeg. C'est le navigateur distant
  quand un rendu réel est indispensable.

### Variables attendues

`FIRECRAWL_API_KEY` est déjà dans l'environnement. `APIFY_TOKEN` ne l'est pas
et doit être exporté avant d'utiliser `social` :

```bash
export APIFY_TOKEN=...    # jamais écrit dans un fichier suivi
```

## garde-secrets.sh — le hook

Branché en `PreToolUse` sur `Bash` dans `.claude/settings.json`. Il refuse
deux choses, et rien d'autre : un secret reconnaissable écrit en clair dans
une commande de commit, et un commit dont le contenu indexé contient un
secret.

Il est volontairement étroit. Un garde-fou qui crie tout le temps finit
désactivé, et ne protège plus rien.

Deux fautes réelles l'ont motivé : un `ADMIN_SYNC_TOKEN` en clair dans
`docs/REPRISE.md`, dans la ligne même qui le déclarait « jamais commité » ;
et une clé collée en conversation. Rappel : retirer un secret d'un fichier ne
le retire pas de l'historique — il reste à révoquer.
