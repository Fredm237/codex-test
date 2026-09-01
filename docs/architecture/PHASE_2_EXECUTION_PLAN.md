# FILON — Phase 2 Entity Resolution Execution Plan

- Ouverture : **31 août 2026**
- Statut : **FERMÉE — GO**
- Entrée : [PHASE 1 = GO](PHASE_1_FINAL_RECEIPT.md)
- Gate de sortie : **False Merge sous le target ratifié**
- Lecteurs publics Product Graph : **NON PROMUS**
- Immersive : **NO-GO inchangé**

## Objectif

Augmenter la couverture d'identité au-delà du GTIN exact sans dégrader la
précision acquise en Phase 1. Le moteur doit combiner des preuves structurées,
produire une décision explicable et s'abstenir dès qu'un conflit empêche une
fusion sûre.

La règle de conception est prioritaire sur la couverture : **un faux merge est
plus dangereux qu'un faux split**.

## Point de départ mesuré

Le premier lot réel Phase 1 contient 1 000 offres :

- 330 résolutions exact-GTIN ;
- 670 abstentions `missing_gtin` ;
- 321 variantes et identifiants ;
- 0 GTIN scindé, 0 variante à GTIN contradictoires ;
- replay sans duplication ;
- 67 % de couverture à expliquer ou améliorer sans fallback.

Phase 2 ne doit pas « résoudre » artificiellement ces 670 inconnus. Elle doit
d'abord mesurer quels signaux supplémentaires sont réellement présents.

## Signaux candidats

Dans l'ordre de force et sous réserve de l'audit réel :

1. GTIN/EAN/UPC valide et non contradictoire ;
2. MPN dans un scope Brand prouvé ;
3. modèle extrait et attributs de variante structurés ;
4. capacité, stockage, couleur, taille et génération ;
5. taxonomie et rôle produit ;
6. metadata marchand et identifiant source scopé ;
7. titre, image et similarité sémantique uniquement comme génération de
   candidats ou corroboration, jamais comme preuve exacte isolée.

## Contrat de décision à figer

| Statut | Sens initial | Effet public pendant Phase 2 |
|---|---|---|
| `EXACT_VERIFIED` | identifiant fort exact sans conflit | shadow uniquement |
| `HIGH_CONFIDENCE` | plusieurs preuves structurées concordantes | shadow uniquement |
| `PROBABLE` | candidat utile mais preuve insuffisante | aucune fusion canonique |
| `AMBIGUOUS` | plusieurs candidats non départageables | abstention |
| `UNRESOLVED` | aucune preuve suffisante ou conflit | abstention |

Les seuils et transitions ne seront pas fixés par intuition. Ils doivent être
ratifiés par le benchmark et par la distribution des signaux réels.

## Gates

| Gate | Exigence |
|---|---|
| Faux merge | borne supérieure 95 % sous le target ratifié, avec zéro conflit silencieux |
| Faux split | mesuré par niveau de preuve et verticale, sans optimisation au détriment du faux merge |
| Exact product | le niveau `EXACT_VERIFIED` conserve les résultats Phase 1 |
| Variant match | stockage, taille, couleur, capacité et génération contradictoires bloquent la fusion |
| Confiance | statut dérivé de preuves versionnées, jamais d'un nombre opaque seul |
| Provenance | chaque signal, transformation et décision est rejouable |
| Abstention | `AMBIGUOUS` et `UNRESOLVED` restent des sorties normales |
| Idempotence | deux projections identiques produisent le même état shadow |
| Compatibilité | aucun lecteur public v1 n'est modifié avant revue de sortie |

## Séquence

1. Figer le contrat des décisions et des conflits.
2. Auditer la disponibilité réelle des signaux par verticale.
3. Ratifier le benchmark, son target de faux merge et son budget d'abstention.
4. Écrire les extracteurs de modèle et d'attributs versionnés.
5. Construire le candidate generator et le resolver hiérarchique.
6. Exécuter un shadow replay réel borné et idempotent.
7. Publier couverture, faux merges, faux splits et abstentions.
8. Tenir la revue Phase 2 vers Phase 3 Offer Truth.

## Avancement

| Lot | État | Preuve attendue |
|---|---|---|
| P2A — contrat de décision | **terminé** | [ADR-007](ADR-007-ENTITY-RESOLUTION-DECISION-CONTRACT.md), schéma, exemples et 36 tests |
| P2B — audit des signaux réels | **terminé** | [audit production borné](PHASE_2B_ENTITY_RESOLUTION_SIGNAL_AUDIT.md) |
| P2C — benchmark étendu | **terminé** | [benchmark et targets ratifiés](PHASE_2C_ENTITY_RESOLUTION_BENCHMARK_REPORT.md) |
| P2D — extracteurs shadow | **terminé** | [faits versionnés et unknown explicite](PHASE_2D_ENTITY_SIGNAL_EXTRACTORS_REPORT.md) |
| P2E — resolver multi-signal | **terminé** | [resolver hiérarchique et benchmark vert](PHASE_2E_MULTI_SIGNAL_RESOLVER_REPORT.md) |
| P2F — replay réel borné | **terminé en production** | [migration, replay réel et idempotence](PHASE_2F_ENTITY_RESOLUTION_REPLAY_REPORT.md) |
| P2G — qualification | **terminé — PASS** | [reçu production et neuf gates verts](PHASE_2G_ENTITY_RESOLUTION_QUALIFICATION_GATE.md) |
| P2H — revue de sortie | **terminé — GO** | [reçu final Phase 2](PHASE_2_FINAL_RECEIPT.md) ; Phase 3 ouverte |

Les travaux SRE non bloquants et l'Immersive restent séparés. Aucun nouveau
gate Phase 2 ne doit être créé sans risque démontré pour l'intégrité ou la
récupérabilité nécessaires à Offer Truth.
