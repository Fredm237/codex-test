# FILON — Phase 3 Offer Truth Execution Plan

- Ouverture : **1er septembre 2026**
- Statut : **OUVERTE**
- Entrée : [PHASE 2 = GO](PHASE_2_FINAL_RECEIPT.md)
- Gate de sortie : **offer correctness target passes**
- Lecteurs publics Offer Graph : **NON PROMUS**
- Immersive : **NO-GO inchangé**

## Objectif

Transformer chaque offre en faits temporels sourcés : prix, stock, livraison,
retours, garantie, marchand et fraîcheur. Une valeur inconnue, invalide,
future, stale ou contradictoire doit rester non favorable. La Phase 3 ne choisit
pas encore la « meilleure offre » : elle établit d'abord quelles offres et
quels champs sont correctement observés.

## Point de départ

- 1 000 raws Awin sont reliés à leurs offres Core et à leur Variant shadow ;
- l'Offer Graph P0.5 stocke déjà argent décimal, devise, stock tri-state et lien
  HTTPS public strict ;
- shipping, retours et garantie restent non mesurés dans le feed audité ;
- la fraîcheur provisoire est de 72 h, sans prétention de SLO définitif ;
- Merchant Intelligence expose des compteurs mais aucune note calibrée ;
- `NO_EXTERNAL_HUMAN_GROUND_TRUTH` reste explicite et non bloquant.

## Gates

| Gate | Exigence |
|---|---|
| Prix | montant décimal et devise atomiques ; zéro fallback |
| Stock | tri-state ou preorder ; jamais disponible par défaut |
| Shipping | connu avec devise ou explicitement inconnu ; jamais gratuit par défaut |
| Retours / garantie | faits sourcés ou `unknown`, sans extraction spéculative |
| Marchand | identité Registry et relation commerciale non embellie |
| Fraîcheur | futur/stale exclus de la vérité courante ; policy versionnée |
| Provenance | chaque claim connu cite raw, source, observation et transformation |
| Exactitude | benchmark adversarial sous les targets ratifiés |
| Idempotence | deux projections identiques produisent le même snapshot shadow |
| Compatibilité | aucune lecture publique v1 modifiée avant revue de sortie |

## Séquence

1. P3A — figer le contrat Offer Truth et ses unknowns.
2. P3B — auditer les champs réels et la fraîcheur par marchand/verticale.
3. P3C — ratifier le benchmark et les targets d'exactitude.
4. P3D — écrire les extracteurs de claims versionnés.
5. P3E — ajouter la persistance expand-only et le writer shadow.
6. P3F — exécuter un replay réel borné puis son replay idempotent.
7. P3G — publier les gates d'exactitude, couverture et abstention.
8. P3H — tenir la revue de sortie vers Product Ontology.

## Avancement

| Lot | État | Preuve attendue |
|---|---|---|
| P3A — contrat Offer Truth | **terminé localement** | [ADR-008](ADR-008-OFFER-TRUTH-V1-CONTRACT.md), schéma, exemples et 33 tests |
| P3B — baseline réelle | **terminé en lecture seule** | [couverture réelle des sept claims](PHASE_3B_OFFER_TRUTH_BASELINE.md) |
| P3C — benchmark | **terminé localement** | [14 352 cas, zéro échec, gates ratifiées](PHASE_3C_OFFER_TRUTH_BENCHMARK_REPORT.md) |
| P3D — extracteurs | **terminé localement** | [extracteur réel : 14 352 cas PASS](PHASE_3D_OFFER_TRUTH_EXTRACTOR_REPORT.md) |
| P3E — schéma/writers | **terminé localement** | [migration `d5a3c7e9f1b4`, writer sec et idempotent](PHASE_3E_OFFER_TRUTH_SHADOW_REPORT.md) |
| P3F — replay production | à faire | lot borné, provenance et idempotence |
| P3G — qualification | à faire | offer correctness et limitations publiées |
| P3H — revue de sortie | à faire | reçu Phase 3 et décision vers Product Ontology |

Les travaux SRE et l'Immersive restent séparés. Aucun score marchand, total
livré, comparaison multidevise ou claim public nouveau n'est autorisé par ce
plan.
