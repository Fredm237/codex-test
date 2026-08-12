#!/usr/bin/env python3
"""Assemble plusieurs séquences en une seule page pilotée au défilement.

Un film unique tient un chapitre. Une page en tient plusieurs, et le passage
de l'un à l'autre est le seul endroit où la couture peut se voir. Deux règles
l'évitent, et elles sont la raison d'être de ce module :

1. **Un seul canvas pour tous les chapitres.** Empiler un canvas par film
   ferait clignoter au raccord et multiplierait la mémoire GPU.
2. **Le chapitre suivant se précharge pendant qu'on regarde le précédent.**
   Sans cela, le raccord tombe sur une image manquante — exactement ce qui
   trahit un montage bricolé.

Les images sont servies comme fichiers, pas inlinées : au-delà de deux
chapitres, un HTML en base64 devient trop lourd pour être analysé par le
navigateur avant le premier rendu.

    python3 .claude/agent/lecteur.py \
        --chapitre "Le bon moment:public/seq/moment:0.0" \
        --chapitre "L'écart:public/seq/ecart:0.5" \
        --sortie public/experience.html
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GABARIT = """<title>{titre}</title>
<style>
:root{{--fond:#0e0c0b;--texte:#f2eee7;--ambre:#c89544;--doux:#a89e90}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--fond);color:var(--texte);
 font-family:"Helvetica Neue",Helvetica,Arial,system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
#scene{{position:fixed;inset:0;z-index:0;background:var(--fond)}}
#px{{display:block}}
#piste{{position:relative;z-index:1}}
.chap{{position:sticky;top:0;height:100vh;display:grid;align-content:center;
 padding:0 clamp(24px,6vw,92px);opacity:0;transition:opacity .5s ease;pointer-events:none}}
.chap.on{{opacity:1}}
.chap h2{{margin:0;max-width:17ch;font-size:clamp(30px,5.4vw,72px);font-weight:200;
 line-height:1.04;letter-spacing:-.035em;text-wrap:balance;
 text-shadow:0 2px 44px rgba(8,7,6,.95),0 1px 4px rgba(8,7,6,.85)}}
.chap em{{font-style:normal;color:var(--ambre)}}
#barre{{position:fixed;left:0;top:0;height:2px;width:0;background:var(--ambre);z-index:3}}
#etat{{position:fixed;z-index:3;left:50%;bottom:22px;transform:translateX(-50%);font-size:11px;
 letter-spacing:.2em;text-transform:uppercase;color:var(--doux);text-shadow:0 1px 10px rgba(8,7,6,.9)}}
@media (prefers-reduced-motion:reduce){{.chap{{opacity:1;position:relative;height:auto;padding-block:22vh}}}}
</style>
<div id="scene"><canvas id="px"></canvas></div>
<div id="barre"></div>
<div id="piste">{sections}</div>
<p id="etat">chargement…</p>
<script>
(function(){{
 const CH={chapitres};
 const cv=document.getElementById('px'),ctx=cv.getContext('2d',{{alpha:false}});
 const etat=document.getElementById('etat'),barre=document.getElementById('barre');
 const blocs=[...document.querySelectorAll('.chap')];
 // Un plan par chapitre ; chacun garde ses images décodées.
 CH.forEach(c=>{{c.imgs=new Array(c.images); c.charge=false; c.prets=0;}});
 let courantId=-1,courantIdx=-1,raf=0;

 function charger(k,onPremiere){{
  const c=CH[k]; if(!c||c.charge) return; c.charge=true;
  for(let i=0;i<c.images;i++){{
   const im=new Image();
   im.onload=()=>{{c.imgs[i]=im;c.prets++;
    if(i===0&&onPremiere) onPremiere();
    if(k===0) etat.textContent = c.prets<c.images
      ? 'chargement '+Math.round(c.prets/c.images*100)+' %' : 'faites défiler';}};
   im.src=c.base+'/'+String(i).padStart(3,'0')+'.jpg';
  }}
 }}

 function dim(){{const d=Math.min(devicePixelRatio||1,2);
  cv.width=innerWidth*d;cv.height=innerHeight*d;
  cv.style.width=innerWidth+'px';cv.style.height=innerHeight+'px';
  courantIdx=-1;peindre();}}

 function peindre(){{
  const course=document.documentElement.scrollHeight-innerHeight;
  const p=course>0?Math.min(Math.max(scrollY/course,0),1):0;
  barre.style.width=(p*100).toFixed(2)+'%';
  // Quel chapitre, et où dedans.
  let k=0; for(let i=0;i<CH.length;i++) if(p>=CH[i].depart) k=i;
  const c=CH[k];
  const fin=(k+1<CH.length)?CH[k+1].depart:1;
  const local=fin>c.depart?(p-c.depart)/(fin-c.depart):0;
  const idx=Math.round(Math.min(Math.max(local,0),1)*(c.images-1));
  // Précharge le suivant dès qu'on entame la seconde moitié du courant.
  if(local>0.5&&k+1<CH.length) charger(k+1);
  const im=c.imgs[idx];
  if(im&&(k!==courantId||idx!==courantIdx)){{
   courantId=k;courantIdx=idx;
   const cw=cv.width,ch=cv.height,e=Math.max(cw/im.width,ch/im.height);
   const w=im.width*e,h=im.height*e;
   ctx.drawImage(im,(cw-w)/2,(ch-h)/2,w,h);
  }}
  blocs.forEach(b=>{{const a=+b.dataset.at,z=+b.dataset.to;
   b.classList.toggle('on',p>=a-0.04&&p<z);}});
 }}

 addEventListener('scroll',()=>{{if(!raf)raf=requestAnimationFrame(()=>{{peindre();raf=0;}});}},{{passive:true}});
 addEventListener('resize',dim);
 charger(0,()=>{{courantIdx=-1;peindre();}});
 dim();peindre();
}})();
</script>
"""


def main() -> None:
    p = argparse.ArgumentParser(description="Assemble des séquences en une page")
    p.add_argument("--chapitre", action="append", required=True,
                   help="« Titre|Suite:dossier:depart » — depart entre 0 et 1")
    p.add_argument("--titre", default="FILON")
    p.add_argument("--sortie", required=True)
    p.add_argument("--base-url", default="", help="préfixe d'URL des images")
    a = p.parse_args()

    chaps, sections = [], []
    for i, brut in enumerate(a.chapitre):
        try:
            texte, dossier, depart = brut.rsplit(":", 2)
        except ValueError:
            sys.exit(f"Chapitre mal formé : {brut}")
        d = Path(dossier)
        man = d / "manifeste.json"
        if not man.exists():
            sys.exit(f"Manifeste absent : {man} — lance d'abord sequence.py")
        images = json.loads(man.read_text(encoding="utf-8"))["images"]
        base = (a.base_url.rstrip("/") + "/" + d.name) if a.base_url else "/" + str(d).lstrip("/")
        chaps.append({"base": base, "images": images, "depart": float(depart)})
        titre, _, suite = texte.partition("|")
        fin = 1.0 if i == len(a.chapitre) - 1 else float(a.chapitre[i + 1].rsplit(":", 1)[1])
        sections.append(
            f'<div class="chap" data-at="{float(depart)}" data-to="{fin}">'
            f'<h2>{titre} <em>{suite}</em></h2></div>'
        )

    # La piste doit être assez haute pour que chaque image ait de la course.
    total_images = sum(c["images"] for c in chaps)
    hauteur = max(300, total_images * 7)
    html = GABARIT.format(
        titre=a.titre,
        sections="".join(sections),
        chapitres=json.dumps(chaps, ensure_ascii=False),
    ).replace('id="piste">', f'id="piste" style="height:{hauteur}vh">')

    Path(a.sortie).write_text(html, encoding="utf-8")
    print(f"{a.sortie} · {len(chaps)} chapitres · {total_images} images · piste {hauteur}vh")


if __name__ == "__main__":
    main()
