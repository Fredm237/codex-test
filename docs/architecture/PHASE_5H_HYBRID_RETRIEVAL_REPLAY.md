# FILON — Phase 5H Hybrid Retrieval Replay

- Date : **1er septembre 2026**
- Statut : **LOCAL READY — PRODUCTION PENDING**
- Version : `hybrid-retrieval-production-replay/v1`
- Fenêtre maximale : **1 000 snapshots**
- Valeur par défaut : **100 snapshots**
- Lecteur public : **INCHANGÉ**

## Objectif

Exécuter le pipeline Hybrid Retrieval sur une fenêtre réelle, résolue et
bornée de Product Ontology, persister uniquement les digests et preuves shadow,
puis rejouer exactement le même instant pour démontrer l'idempotence.

## Source réelle

Le replay lit uniquement les snapshots Product Ontology avec `variant_id`
résolue et leur offre Core associée, ordonnés par identifiant de snapshot. Les
surfaces marque/titre servent à construire une requête technique en mémoire.

Cette requête :

- ne provient pas d'un utilisateur ;
- n'est jamais écrite dans la base ou le rapport ;
- est remplacée par un SHA-256 et une référence `p5h:<snapshot_id>` ;
- ne figure dans aucun log de résultat.

Les documents de la fenêtre conservent uniquement identité, offre, type, rôle
et attributs observés. Le replay mesure la mécanique réelle, pas la distribution
des requêtes humaines.

## Pipeline

Pour chaque snapshot cible :

1. construire les documents lexical, structuré et sémantique de la fenêtre ;
2. exécuter les trois adaptateurs bornés à 50 ;
3. préserver l'ambiguïté et les abstentions ;
4. fusionner en RRF product-first ;
5. comparer le top-1 à la Variant cible ;
6. calculer les digests ;
7. dry-run ou persister via le writer P5G.

Le rapport ne contient que compteurs, bornes de fenêtre, digests et versions.

## Commandes qualifiées

Dry-run, toujours disponible après migration :

```bash
python -m app.hybrid_retrieval.replay \
  --evaluated-at 2026-09-01T18:00:00Z \
  --after-snapshot-id 0 \
  --limit 100
```

Apply borné, uniquement dans un processus de maintenance où le flag est activé :

```bash
HYBRID_RETRIEVAL_SHADOW_ENABLED=true \
python -m app.hybrid_retrieval.replay \
  --evaluated-at 2026-09-01T18:00:00Z \
  --after-snapshot-id 0 \
  --limit 100 \
  --apply
```

Le replay d'idempotence réutilise strictement le même `evaluated-at`, la même
borne et les mêmes versions. Un autre instant représente une nouvelle
évaluation append-only, pas un replay.

## Qualification locale

Le test d'intégration SQLite construit une vraie chaîne Merchant → Offer →
RawSource → Variant → ProductOntologySnapshot, puis démontre :

- dry-run : zéro écriture ;
- premier apply : un run et un candidat ;
- replay identique : un run existant et un candidat existant ;
- même `evaluation_id` ;
- top-1 égal à l'entité cible ;
- aucune requête brute dans le modèle ou le rapport.

## Gate production

P5H n'est pas terminale en production. Il reste à :

1. publier le lot Phase 5 autorisé ;
2. obtenir les quatre surfaces CI vertes ;
3. sauvegarder/restaurer puis migrer vers `f7c5e9a1b3d6` ;
4. garder le flag persistant OFF ;
5. exécuter dry-run, apply et replay identique avec activation process-only ;
6. comparer compteurs, digests, top-1 et absence de double écriture ;
7. restaurer le processus sans lancement automatique.

Aucune réussite P5H production ne sera annoncée sans ces preuves terminales.
