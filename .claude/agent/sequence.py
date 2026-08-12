#!/usr/bin/env python3
"""Découpe un film en séquence d'images pilotable au défilement.

La technique des pages produit d'Apple, et la seule qui donne du
photoréalisme sur le web : le film est rendu HORS LIGNE, découpé en images,
puis le défilement choisit l'image à dessiner dans un canvas. Aucun WebGL,
donc aucune limite de temps réel — la qualité ne dépend plus de la carte
graphique du visiteur.

Ce que ce module produit : les images optimisées, plus un manifeste JSON que
le lecteur lit pour connaître le nombre d'images et leur gabarit.

Trois réglages méritent d'être compris plutôt que subis :

- **Le nombre d'images.** Au-delà d'environ 80 sur une course d'écran, l'œil
  ne distingue plus rien au défilement : on paie du poids pour rien. En deçà
  de 40, le mouvement redevient saccadé.
- **La largeur.** 1280 px suffit : l'image est recadrée en `cover`, et un
  écran large l'étire de toute façon.
- **La qualité JPEG.** 72 est le point où l'artefact reste invisible sur une
  image sombre. Le grain du film masque ce qui resterait.

    python3 .claude/agent/sequence.py film.mp4 --sortie public/seq/descente
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def ffmpeg() -> str:
    """Le ffmpeg complet. Celui livré avec Playwright est un build minimal
    qui refuse un mp4 ordinaire — piège déjà rencontré."""
    for essai in ("ffmpeg", shutil.which("ffmpeg")):
        if essai and shutil.which(essai):
            return essai
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg introuvable. Installe-le, ou : pip install imageio-ffmpeg")


def duree(exe: str, film: Path) -> float:
    r = subprocess.run([exe, "-hide_banner", "-i", str(film)], capture_output=True, text=True)
    for mot in r.stderr.split():
        pass
    for ligne in r.stderr.splitlines():
        if "Duration:" in ligne:
            h, m, s = ligne.split("Duration:")[1].split(",")[0].strip().split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    sys.exit("Durée illisible — le fichier est-il bien une vidéo ?")


def main() -> None:
    p = argparse.ArgumentParser(description="Film → séquence d'images pour défilement")
    p.add_argument("film")
    p.add_argument("--sortie", required=True)
    p.add_argument("--images", type=int, default=72, help="nombre d'images (défaut 72)")
    p.add_argument("--largeur", type=int, default=1280)
    p.add_argument("--qualite", type=int, default=72)
    a = p.parse_args()

    film = Path(a.film)
    if not film.exists():
        sys.exit(f"Introuvable : {film}")
    sortie = Path(a.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    for vieux in sortie.glob("*.jpg"):
        vieux.unlink()

    exe = ffmpeg()
    d = duree(exe, film)
    fps = a.images / d

    brut = sortie / "_brut"
    brut.mkdir(exist_ok=True)
    subprocess.run(
        [exe, "-hide_banner", "-loglevel", "error", "-i", str(film),
         "-vf", f"fps={fps},scale={a.largeur}:-2", "-q:v", "3",
         str(brut / "b_%04d.jpg"), "-y"],
        check=True,
    )

    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow requis : pip install pillow")

    bruts = sorted(brut.glob("*.jpg"))
    if not bruts:
        sys.exit("Aucune image extraite.")
    # ffmpeg rend rarement le compte exact : on rééchantillonne pour tomber juste.
    choix = [bruts[round(i * (len(bruts) - 1) / (a.images - 1))] for i in range(a.images)]

    total = 0
    gabarit = None
    for i, f in enumerate(choix):
        im = Image.open(f).convert("RGB")
        gabarit = im.size
        cible = sortie / f"{i:03d}.jpg"
        im.save(cible, quality=a.qualite, optimize=True, progressive=True)
        total += cible.stat().st_size
    shutil.rmtree(brut)

    (sortie / "manifeste.json").write_text(
        json.dumps(
            {"images": a.images, "largeur": gabarit[0], "hauteur": gabarit[1],
             "motif": "{i}.jpg", "octets": total},
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"{a.images} images · {gabarit[0]}×{gabarit[1]} · {total/1024/1024:.2f} Mo · {sortie}")
    if total > 6 * 1024 * 1024:
        print("Attention : au-delà de 6 Mo, prévoir un chargement progressif.")


if __name__ == "__main__":
    main()
