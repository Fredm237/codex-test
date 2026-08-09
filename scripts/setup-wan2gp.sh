#!/usr/bin/env bash
#
# Wan2GP — génération vidéo locale (deepbeepmeep/Wan2GP)
#
# À lire avant de lancer : ce script ne s'exécute PAS sur un MacBook.
#
# La documentation d'installation de Wan2GP ne couvre que Windows et Linux avec
# un GPU NVIDIA (GTX 10xx à RTX 50xx) ou AMD RDNA 2-4. Elle ne mentionne ni
# macOS ni Apple Silicon, et la chaîne repose sur CUDA — le `--index-url` de
# torch ci-dessous n'a pas d'équivalent Metal. Sur un MacBook Air, il n'y a pas
# d'installation dégradée mais fonctionnelle : il n'y a pas d'installation.
#
# Ce fichier existe pour la machine qui a la carte. Sur le Mac, la voie qui
# marche est Higgsfield, déjà connecté au projet (génération dans le nuage,
# rien à installer).
#
# Usage :  bash scripts/setup-wan2gp.sh [dossier-cible]
#
set -euo pipefail

CIBLE="${1:-$HOME/Wan2GP}"

echo "→ Vérification du matériel"
if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo
    echo "  nvidia-smi introuvable : aucun GPU NVIDIA détecté."
    echo
    echo "  Wan2GP a besoin d'une carte NVIDIA (ou AMD RDNA 2-4 avec la variante"
    echo "  ROCm de torch). Sans elle, l'installation aboutira mais aucun modèle"
    echo "  ne tournera — c'est un échec plus coûteux qu'un refus immédiat."
    echo
    echo "  Sur macOS : utilise Higgsfield, déjà connecté au projet."
    exit 1
fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

echo "→ Espace disque"
# Les modèles se comptent en dizaines de gigaoctets ; les télécharger sur un
# disque presque plein échoue à mi-parcours, après une heure.
DISPO_GO=$(df -BG --output=avail "$(dirname "$CIBLE")" | tail -1 | tr -dc '0-9')
echo "  ${DISPO_GO} Go disponibles"
if [ "$DISPO_GO" -lt 60 ]; then
    echo "  Moins de 60 Go : insuffisant pour les poids des modèles. Arrêt."
    exit 1
fi

echo "→ Clone dans $CIBLE"
if [ -d "$CIBLE/.git" ]; then
    git -C "$CIBLE" pull --ff-only
else
    git clone https://github.com/deepbeepmeep/Wan2GP.git "$CIBLE"
fi
cd "$CIBLE"

echo "→ Environnement virtuel"
# Isolé : Wan2GP épingle des versions précises de torch, et les installer dans
# le Python du système casse tout ce qui l'utilise par ailleurs.
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip

echo "→ torch (CUDA 13.0)"
pip install torch==2.10.0 torchvision==0.25.0 torchaudio==2.10.0 \
    --index-url https://download.pytorch.org/whl/cu130

echo "→ Dépendances"
pip install -r requirements.txt

cat <<'FIN'

Installé.

  cd <dossier>
  source .venv/bin/activate
  python wgp.py

Au premier lancement, les poids des modèles se téléchargent — compte plusieurs
dizaines de gigaoctets et une bonne heure. L'interface s'ouvre ensuite sur
http://localhost:7860.
FIN
