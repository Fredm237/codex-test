#!/usr/bin/env python3
"""Rend l'état de mission en page consultable.

`mission.py show` suffit dans un terminal. Cette page sert à autre chose :
montrer l'avancement à quelqu'un qui ne lira pas les journaux — où en est la
mission, ce qui bloque, ce qui reste.

Elle n'invente aucune mise en forme : la palette et la typographie viennent du
système du dépôt (`filon-web/app/tokens.css`), le même béton chaud et le même
ambre. Un tableau de bord qui ressemble au produit qu'il surveille se lit plus
vite qu'un thème générique.

    python3 .claude/agent/tableau.py            # écrit mission.html
    python3 .claude/agent/tableau.py --sortie /tmp/m.html
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent / "missions"
COURANTE = RACINE / "courante.json"

# Le statut se lit à la forme autant qu'à la couleur : marqueur + liseré.
ETAT = {
    "fait": ("✓", "fait", "Fait"),
    "en_cours": ("→", "encours", "En cours"),
    "a_faire": ("·", "afaire", "À faire"),
    "echec": ("✗", "echec", "Échec"),
    "abandonne": ("—", "abandonne", "Abandonné"),
}

CSS = """
:root {
  /* Ton clair — le béton en plein soleil. Palette complète ici, pour que
     l'état « système » non stampé ait toujours un jeu résolu. */
  --fond: #e7e2d8;
  --fond-creux: #dcd6ca;
  --surface: #f2eee7;
  --texte: #1a1611;
  --texte-fort: #080706;
  --texte-doux: #4d453b;
  --texte-faible: #6b6155;
  --trait: rgba(8, 7, 6, 0.14);
  --trait-fort: rgba(8, 7, 6, 0.26);
  --ambre: #7a5c1c;
  --ambre-vif: #a37c2b;
  --feuille: #3d5230;
  --terre: #8f3b28;
  --ombre: 0 10px 30px -14px rgba(8, 7, 6, 0.3);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --fond: #0e0c0b;
    --fond-creux: #080706;
    --surface: #16130f;
    --texte: #e4ded4;
    --texte-fort: #f2eee7;
    --texte-doux: #a89e90;
    --texte-faible: #8d8375;
    --trait: rgba(232, 222, 205, 0.11);
    --trait-fort: rgba(232, 222, 205, 0.2);
    --ambre: #c89544;
    --ambre-vif: #e8c489;
    --feuille: #8fb072;
    --terre: #e59480;
    --ombre: 0 10px 34px -14px rgba(0, 0, 0, 0.7);
  }
}
:root[data-theme="dark"] {
  --fond: #0e0c0b;
  --fond-creux: #080706;
  --surface: #16130f;
  --texte: #e4ded4;
  --texte-fort: #f2eee7;
  --texte-doux: #a89e90;
  --texte-faible: #8d8375;
  --trait: rgba(232, 222, 205, 0.11);
  --trait-fort: rgba(232, 222, 205, 0.2);
  --ambre: #c89544;
  --ambre-vif: #e8c489;
  --feuille: #8fb072;
  --terre: #e59480;
  --ombre: 0 10px 34px -14px rgba(0, 0, 0, 0.7);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--fond);
  color: var(--texte);
  font-family: "Helvetica Neue", Helvetica, Arial, system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.6;
  letter-spacing: 0.006em;
  -webkit-font-smoothing: antialiased;
}
.enveloppe { max-width: 940px; margin-inline: auto; padding: clamp(28px, 5vw, 64px) clamp(20px, 4vw, 40px) 96px; }

/* En-tête — le mot-signe en bas de casse avec son point final, comme le produit. */
.signe { font-size: 13px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--texte-faible); }
h1 {
  margin: 10px 0 0;
  font-size: clamp(30px, 5.2vw, 52px);
  font-weight: 300;
  line-height: 1.04;
  letter-spacing: -0.035em;
  text-wrap: balance;
  color: var(--texte-fort);
}
h1::after { content: "."; color: var(--ambre); }
.objectif { margin: 14px 0 0; max-width: 62ch; color: var(--texte-doux); }

/* Sommaire avant le détail : la barre puis les compteurs. */
.resume { margin-top: 34px; display: flex; flex-direction: column; gap: 14px; }
.jauge { height: 4px; background: var(--fond-creux); border: 1px solid var(--trait); display: flex; overflow: hidden; }
.jauge i { display: block; height: 100%; }
.jauge .j-fait { background: var(--feuille); }
.jauge .j-echec { background: var(--terre); }
.compteurs { display: flex; flex-wrap: wrap; gap: 26px; }
.compteur { display: flex; flex-direction: column; gap: 2px; }
.compteur b { font-size: 26px; font-weight: 400; line-height: 1; font-variant-numeric: tabular-nums; color: var(--texte-fort); }
.compteur span { font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--texte-faible); }

/* Les contraintes bloquent la mission : elles passent avant les tâches. */
.contraintes { margin-top: 34px; display: flex; flex-direction: column; gap: 10px; }
.contrainte {
  display: flex; gap: 12px; padding: 13px 16px;
  background: var(--surface); border: 1px solid var(--trait);
  border-left: 3px solid var(--terre);
}
.contrainte::before { content: "!"; font-weight: 700; color: var(--terre); line-height: 1.5; }
.contrainte p { margin: 0; color: var(--texte-doux); font-size: 15px; }

h2 { margin: 46px 0 0; font-size: 13px; font-weight: 500; letter-spacing: 0.16em; text-transform: uppercase; color: var(--texte-faible); }

.taches { list-style: none; margin: 16px 0 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.tache {
  background: var(--surface);
  border: 1px solid var(--trait);
  border-left: 3px solid var(--trait-fort);
  padding: 16px 20px;
  box-shadow: var(--ombre);
}
.tache.fait { border-left-color: var(--feuille); }
.tache.encours { border-left-color: var(--ambre); }
.tache.echec { border-left-color: var(--terre); }
.tache.afaire { border-left-color: var(--trait-fort); }
.tache.abandonne { opacity: 0.6; }

.ligne { display: flex; align-items: baseline; gap: 12px; }
.marque { font-size: 15px; width: 1em; flex: none; color: var(--texte-faible); }
.tache.fait .marque { color: var(--feuille); }
.tache.encours .marque { color: var(--ambre); }
.tache.echec .marque { color: var(--terre); }
.ident { font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--texte-faible); flex: none; font-variant-numeric: tabular-nums; }
.titre { font-size: 17px; color: var(--texte-fort); }
.tache.fait .titre { color: var(--texte-doux); }

.meta { margin: 12px 0 0 calc(1em + 12px); display: flex; flex-direction: column; gap: 7px; }
.champ { display: flex; gap: 10px; font-size: 14px; }
.champ dt { flex: none; width: 92px; color: var(--texte-faible); }
.champ dd { margin: 0; color: var(--texte-doux); }
.champ.preuve dd { color: var(--feuille); }

.puces { display: flex; flex-wrap: wrap; gap: 6px; }
.puce {
  font-size: 12px; padding: 2px 9px; border-radius: 10px;
  background: var(--fond-creux); border: 1px solid var(--trait);
  color: var(--texte-faible); font-variant-numeric: tabular-nums;
}

.pied { margin-top: 54px; padding-top: 18px; border-top: 1px solid var(--trait); font-size: 13px; color: var(--texte-faible); }
@media (max-width: 560px) {
  .champ { flex-direction: column; gap: 1px; }
  .champ dt { width: auto; }
}
"""


def rendre(m: dict) -> str:
    e = html.escape
    taches = m.get("taches", [])
    total = len(taches) or 1
    faits = sum(1 for t in taches if t["statut"] == "fait")
    echecs = sum(1 for t in taches if t["statut"] == "echec")
    reste = sum(1 for t in taches if t["statut"] in ("a_faire", "en_cours"))

    lignes = []
    for t in taches:
        marque, classe, _ = ETAT.get(t["statut"], ("·", "afaire", ""))
        meta = []
        if t.get("depend"):
            puces = "".join(f'<span class="puce">{e(d)}</span>' for d in t["depend"])
            meta.append(f'<div class="champ"><dt>Dépend de</dt><dd><div class="puces">{puces}</div></dd></div>')
        if t.get("outil"):
            meta.append(f'<div class="champ"><dt>Outil</dt><dd>{e(t["outil"])}</dd></div>')
        if t.get("attendu"):
            meta.append(f'<div class="champ"><dt>Attendu</dt><dd>{e(t["attendu"])}</dd></div>')
        if t.get("obtenu"):
            meta.append(f'<div class="champ"><dt>Obtenu</dt><dd>{e(t["obtenu"])}</dd></div>')
        if t.get("verification"):
            meta.append(f'<div class="champ preuve"><dt>Vérifié</dt><dd>{e(t["verification"])}</dd></div>')
        bloc = f'<dl class="meta">{"".join(meta)}</dl>' if meta else ""
        lignes.append(
            f'<li class="tache {classe}">'
            f'<div class="ligne"><span class="marque" aria-hidden="true">{marque}</span>'
            f'<span class="ident">{e(t["id"])}</span>'
            f'<span class="titre">{e(t["objectif"])}</span></div>{bloc}</li>'
        )

    contraintes = "".join(
        f'<div class="contrainte"><p>{e(c)}</p></div>' for c in m.get("contraintes", [])
    )
    bloc_contraintes = (
        f'<h2>Ce qui bloque</h2><div class="contraintes">{contraintes}</div>'
        if contraintes else ""
    )

    return f"""<title>{e(m['titre'])} — état de mission</title>
<style>{CSS}</style>
<main class="enveloppe">
  <p class="signe">État de mission · filon</p>
  <h1>{e(m['titre'])}</h1>
  <p class="objectif">{e(m.get('objectif', ''))}</p>

  <section class="resume" aria-label="Avancement">
    <div class="jauge" role="img" aria-label="{faits} tâches faites sur {len(taches)}">
      <i class="j-fait" style="width:{faits / total * 100:.1f}%"></i>
      <i class="j-echec" style="width:{echecs / total * 100:.1f}%"></i>
    </div>
    <div class="compteurs">
      <div class="compteur"><b>{faits}</b><span>Faites</span></div>
      <div class="compteur"><b>{reste}</b><span>Restantes</span></div>
      <div class="compteur"><b>{echecs}</b><span>Échecs</span></div>
      <div class="compteur"><b>{len(taches)}</b><span>Total</span></div>
    </div>
  </section>

  {bloc_contraintes}

  <h2>Tâches</h2>
  <ul class="taches">{"".join(lignes)}</ul>

  <p class="pied">Généré depuis <code>.claude/agent/missions/courante.json</code> · dernière mise à jour {e(m.get('maj', '—'))}</p>
</main>"""


def main() -> None:
    p = argparse.ArgumentParser(description="Rend l'état de mission en page HTML")
    p.add_argument("--sortie", default="mission.html")
    a = p.parse_args()
    if not COURANTE.exists():
        sys.exit("Aucune mission en cours.")
    m = json.loads(COURANTE.read_text(encoding="utf-8"))
    Path(a.sortie).write_text(rendre(m), encoding="utf-8")
    print(f"Écrit : {a.sortie}")


if __name__ == "__main__":
    main()
