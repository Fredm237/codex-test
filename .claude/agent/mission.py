#!/usr/bin/env python3
"""Orchestrateur de mission — l'état qui survit à la perte de contexte.

Le contexte d'une session se résume et finit par s'effacer ; un fichier, non.
Une mission longue s'écrit donc ici, dans un JSON versionné avec le dépôt, et
se relit d'une session à l'autre.

Chaque tâche porte ce qu'il faut pour être reprise par quelqu'un qui n'a rien
vu : un objectif, ses dépendances, l'outil prévu, le résultat attendu, le
résultat obtenu, et une validation explicite.

La règle qui compte : `done` est refusé tant qu'aucune vérification n'a été
enregistrée. Une commande qui rend 0 n'est pas une preuve, et l'orchestrateur
ne laisse pas confondre les deux.

    python3 .claude/agent/mission.py init "Refonte design"
    python3 .claude/agent/mission.py add t1 "Auditer les jetons" --outil Read
    python3 .claude/agent/mission.py add t2 "Réécrire" --depend t1 --attendu "build vert"
    python3 .claude/agent/mission.py next
    python3 .claude/agent/mission.py verify t1 "84 jetons relus, 24 orphelins"
    python3 .claude/agent/mission.py done t1 --obtenu "audit complet"
    python3 .claude/agent/mission.py show
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parent / "missions"
COURANTE = RACINE / "courante.json"

STATUTS = ("a_faire", "en_cours", "fait", "echec", "abandonne")
MARQUE = {
    "a_faire": "·",
    "en_cours": "→",
    "fait": "✓",
    "echec": "✗",
    "abandonne": "—",
}


def _horodate() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _charger() -> dict:
    if not COURANTE.exists():
        sys.exit("Aucune mission en cours. Lance d'abord : mission.py init \"<titre>\"")
    return json.loads(COURANTE.read_text(encoding="utf-8"))


def _ecrire(m: dict) -> None:
    RACINE.mkdir(parents=True, exist_ok=True)
    m["maj"] = _horodate()
    COURANTE.write_text(
        json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _tache(m: dict, tid: str) -> dict:
    for t in m["taches"]:
        if t["id"] == tid:
            return t
    sys.exit(f"Tâche inconnue : {tid}")


def _journal(m: dict, evenement: str, detail: str = "") -> None:
    """Observabilité : ce qui s'est passé, sans jamais de secret."""
    m.setdefault("journal", []).append(
        {"ts": _horodate(), "evenement": evenement, "detail": detail[:400]}
    )


# ── commandes ────────────────────────────────────────────────────────────


def cmd_init(a) -> None:
    if COURANTE.exists() and not a.force:
        actuelle = json.loads(COURANTE.read_text(encoding="utf-8"))
        sys.exit(
            f"Mission déjà en cours : « {actuelle['titre']} ».\n"
            "Archive-la (mission.py archive) ou relance avec --force."
        )
    m = {
        "titre": a.titre,
        "objectif": a.objectif or a.titre,
        "cree": _horodate(),
        "maj": _horodate(),
        "contraintes": [],
        "taches": [],
        "journal": [],
    }
    _journal(m, "mission_creee", a.titre)
    _ecrire(m)
    print(f"Mission créée : {a.titre}")


def cmd_add(a) -> None:
    m = _charger()
    if any(t["id"] == a.id for t in m["taches"]):
        sys.exit(f"La tâche {a.id} existe déjà.")
    for d in a.depend:
        if not any(t["id"] == d for t in m["taches"]):
            sys.exit(f"Dépendance inconnue : {d}")
    m["taches"].append(
        {
            "id": a.id,
            "objectif": a.objectif,
            "statut": "a_faire",
            "depend": a.depend,
            "outil": a.outil,
            "attendu": a.attendu,
            "obtenu": None,
            "verification": None,
            "tentatives": 0,
        }
    )
    _journal(m, "tache_ajoutee", f"{a.id} — {a.objectif}")
    _ecrire(m)
    print(f"+ {a.id} : {a.objectif}")


def cmd_next(a) -> None:
    """Les tâches réellement exécutables : dépendances toutes satisfaites.

    Plusieurs lignes en sortie = autant de tâches parallélisables.
    """
    m = _charger()
    faites = {t["id"] for t in m["taches"] if t["statut"] == "fait"}
    pretes = [
        t
        for t in m["taches"]
        if t["statut"] == "a_faire" and all(d in faites for d in t["depend"])
    ]
    if not pretes:
        reste = [t for t in m["taches"] if t["statut"] in ("a_faire", "en_cours")]
        print("Rien d'exécutable." if reste else "Mission terminée.")
        if reste:
            bloquees = [t["id"] for t in reste if t["statut"] == "a_faire"]
            if bloquees:
                print(f"Bloquées par des dépendances : {', '.join(bloquees)}")
        return
    for t in pretes:
        outil = f" [{t['outil']}]" if t["outil"] else ""
        print(f"{t['id']}{outil} : {t['objectif']}")


def cmd_start(a) -> None:
    m = _charger()
    t = _tache(m, a.id)
    t["statut"] = "en_cours"
    t["tentatives"] += 1
    _journal(m, "tache_demarree", f"{a.id} (tentative {t['tentatives']})")
    _ecrire(m)
    print(f"→ {a.id} (tentative {t['tentatives']})")


def cmd_verify(a) -> None:
    m = _charger()
    t = _tache(m, a.id)
    t["verification"] = a.preuve
    _journal(m, "verification", f"{a.id} — {a.preuve}")
    _ecrire(m)
    print(f"Vérification enregistrée pour {a.id}.")


def cmd_done(a) -> None:
    m = _charger()
    t = _tache(m, a.id)
    # Le garde-fou central : pas de « fait » sans preuve mesurée.
    if not t["verification"] and not a.sans_preuve:
        sys.exit(
            f"Refus : {a.id} n'a aucune vérification.\n"
            f"Enregistre la preuve (mission.py verify {a.id} \"...\"), "
            "ou force avec --sans-preuve en assumant."
        )
    t["statut"] = "fait"
    t["obtenu"] = a.obtenu
    _journal(m, "tache_faite", f"{a.id} — {a.obtenu or ''}")
    _ecrire(m)
    print(f"✓ {a.id}")


def cmd_fail(a) -> None:
    m = _charger()
    t = _tache(m, a.id)
    t["statut"] = "echec"
    t["obtenu"] = a.raison
    _journal(m, "tache_echouee", f"{a.id} — {a.raison}")
    _ecrire(m)
    print(f"✗ {a.id} : {a.raison}")


def cmd_show(a) -> None:
    m = _charger()
    n = len(m["taches"])
    faites = sum(1 for t in m["taches"] if t["statut"] == "fait")
    print(f"\nMISSION — {m['titre']}   [{faites}/{n}]")
    print(f"Objectif : {m['objectif']}")
    if m.get("contraintes"):
        for c in m["contraintes"]:
            print(f"  contrainte : {c}")
    print("│")
    for i, t in enumerate(m["taches"]):
        dernier = i == n - 1
        print(f"{'└──' if dernier else '├──'} {MARQUE[t['statut']]} {t['id']} : {t['objectif']}")
        pad = "    " if dernier else "│   "
        if t["depend"]:
            print(f"{pad}  dépend de : {', '.join(t['depend'])}")
        if t["outil"]:
            print(f"{pad}  outil : {t['outil']}")
        if t["attendu"]:
            print(f"{pad}  attendu : {t['attendu']}")
        if t["obtenu"]:
            print(f"{pad}  obtenu : {t['obtenu']}")
        if t["verification"]:
            print(f"{pad}  vérifié : {t['verification']}")
        if t["tentatives"] > 1:
            print(f"{pad}  tentatives : {t['tentatives']}")
    reste = [t["id"] for t in m["taches"] if t["statut"] in ("a_faire", "en_cours")]
    print(f"\nReste : {', '.join(reste) if reste else 'rien — mission terminée'}\n")


def cmd_contrainte(a) -> None:
    m = _charger()
    m.setdefault("contraintes", []).append(a.texte)
    _journal(m, "contrainte", a.texte)
    _ecrire(m)
    print(f"Contrainte notée : {a.texte}")


def cmd_archive(a) -> None:
    m = _charger()
    slug = "".join(c if c.isalnum() else "-" for c in m["titre"].lower())[:48]
    cible = RACINE / f"{datetime.now(timezone.utc):%Y%m%d-%H%M}-{slug}.json"
    COURANTE.rename(cible)
    print(f"Archivée : {cible.relative_to(Path.cwd()) if cible.is_relative_to(Path.cwd()) else cible}")


def main() -> None:
    p = argparse.ArgumentParser(description="Orchestrateur de mission FILON")
    s = p.add_subparsers(dest="cmd", required=True)

    q = s.add_parser("init", help="ouvrir une mission")
    q.add_argument("titre")
    q.add_argument("--objectif", default=None)
    q.add_argument("--force", action="store_true")
    q.set_defaults(f=cmd_init)

    q = s.add_parser("add", help="ajouter une tâche")
    q.add_argument("id")
    q.add_argument("objectif")
    q.add_argument("--depend", nargs="*", default=[])
    q.add_argument("--outil", default=None)
    q.add_argument("--attendu", default=None)
    q.set_defaults(f=cmd_add)

    q = s.add_parser("next", help="tâches exécutables maintenant")
    q.set_defaults(f=cmd_next)

    q = s.add_parser("start", help="démarrer une tâche")
    q.add_argument("id")
    q.set_defaults(f=cmd_start)

    q = s.add_parser("verify", help="enregistrer une preuve mesurée")
    q.add_argument("id")
    q.add_argument("preuve")
    q.set_defaults(f=cmd_verify)

    q = s.add_parser("done", help="clore une tâche")
    q.add_argument("id")
    q.add_argument("--obtenu", default=None)
    q.add_argument("--sans-preuve", action="store_true", dest="sans_preuve")
    q.set_defaults(f=cmd_done)

    q = s.add_parser("fail", help="marquer un échec")
    q.add_argument("id")
    q.add_argument("raison")
    q.set_defaults(f=cmd_fail)

    q = s.add_parser("contrainte", help="noter une contrainte de mission")
    q.add_argument("texte")
    q.set_defaults(f=cmd_contrainte)

    q = s.add_parser("show", help="afficher l'arbre")
    q.set_defaults(f=cmd_show)

    q = s.add_parser("archive", help="archiver la mission courante")
    q.set_defaults(f=cmd_archive)

    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
