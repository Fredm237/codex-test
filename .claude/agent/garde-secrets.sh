#!/usr/bin/env bash
# Garde-fou secrets — hook PreToolUse sur Bash.
#
# Deux fautes déjà commises sur ce dépôt sont visées :
#   1. un ADMIN_SYNC_TOKEN écrit en clair dans un fichier suivi, dans la ligne
#      même qui le déclarait « jamais commité » ;
#   2. une clé collée en conversation puis recopiée dans un commit.
#
# Le hook ne juge pas l'intention : il refuse qu'un secret reconnaissable parte
# dans un commit. Tout le reste passe. Sortie 2 = appel bloqué, le message sur
# stderr revient à l'agent.
#
# Il est volontairement étroit : un garde-fou qui crie tout le temps finit
# désactivé, et ne protège plus rien.

set -uo pipefail

charge=$(cat 2>/dev/null || true)
cmd=$(printf '%s' "$charge" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    print(""); raise SystemExit
print((d.get("tool_input") or {}).get("command",""))
' 2>/dev/null || true)

[ -z "$cmd" ] && exit 0

# Formes de secrets réellement rencontrées ici.
MOTIFS='(apify_api_[A-Za-z0-9]{20,}|fc-[a-f0-9]{24,}|filon-sync-[A-Za-z0-9]+|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})'

# 1. Un secret écrit en dur dans une commande qui produit un commit.
if printf '%s' "$cmd" | grep -qE 'git +(commit|push)' &&
   printf '%s' "$cmd" | grep -qE "$MOTIFS"; then
  echo "BLOQUÉ : un secret en clair figure dans cette commande de commit." >&2
  echo "Passe par une variable d'environnement." >&2
  exit 2
fi

# 2. Un commit dont les fichiers indexés contiennent un secret.
if printf '%s' "$cmd" | grep -qE 'git +commit'; then
  if indexe=$(git diff --cached -U0 2>/dev/null); then
    if trouve=$(printf '%s' "$indexe" | grep -E '^\+' | grep -oE "$MOTIFS" | head -1); then
      echo "BLOQUÉ : le contenu indexé contient un secret (${trouve:0:12}…)." >&2
      echo "Retire-le, puis pense à le révoquer — l'ôter du fichier ne l'ôte pas de l'historique." >&2
      exit 2
    fi
  fi
fi

exit 0
