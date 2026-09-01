# FILON — PHASE_3_FINAL_RECEIPT

- Date de décision : **1er septembre 2026**
- Verdict : **PHASE 3 = GO**
- Phase suivante : **PHASE 4 — PRODUCT ONTOLOGY OUVERTE**
- Lecteurs publics Offer Truth : **NON PROMUS**
- Immersive : **NO-GO inchangé**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Décision exécutive

Phase 3 a livré un contrat Offer Truth temporel, sourcé, abstentionniste et
persisté en shadow. Prix et devise restent atomiques, le stock est tri-state,
les champs absents restent `unknown`, une observation future ou stale n'est
jamais favorable et chaque claim connu conserve sa provenance.

Le benchmark adversarial, la CI PostgreSQL et un replay réel borné convergent.
Le premier passage a créé exactement 1 000 snapshots ; le passage strictement
identique a reconnu ces 1 000 snapshots sans création ni divergence. Aucun
risque ouvert d'intégrité ou de récupérabilité nécessaire à Product Ontology
ne subsiste dans le périmètre de sortie.

## Gates de sortie

| Gate | Verdict | Preuve autoritative |
|---|---|---|
| Contrat Offer Truth | **GO** | ADR-008, schéma v1, unknowns et provenance versionnés |
| Prix / devise | **GO** | montant décimal et devise atomiques, zéro fallback |
| Stock | **GO** | tri-state ou preorder, jamais disponible par défaut |
| Shipping / retours / garantie | **GO par abstention** | champs non prouvés conservés `unknown` |
| Fraîcheur | **GO** | policy 72 h versionnée, futur et stale exclus |
| Exactitude | **GO** | 14 352 cas adversariaux, zéro échec |
| Provenance | **GO** | 1 000 projections réelles, sources et transformations versionnées |
| Persistance | **GO** | 1 000 snapshots append-only créés |
| Idempotence | **GO** | second replay : 0 création, 1 000 snapshots existants |
| Schéma / rollback | **GO** | Alembic `d5a3c7e9f1b4`, expansion isolée, activation bornée par processus |
| Compatibilité Core | **GO** | aucun lecteur public v1 modifié |
| CI | **GO** | run `33488434850`, quatre jobs `success` |

## Replay production P3F

- instant d'évaluation immuable : `2026-09-01T08:53:10Z` ;
- fenêtre : `after_raw_id=0`, `limit=1000` ;
- sources scannées : 1 000 ;
- sources projetées : 1 000 ;
- liens offre manquants : 0 ;
- statuts : 330 `VERIFIED`, 670 `QUARANTINED`, 0 `PARTIAL`, 0 `STALE`, 0 `INVALID` ;
- premier apply : 1 000 créés, 0 existant ;
- apply idempotent : 0 créé, 1 000 existants ;
- identifiant d'évaluation :
  `sha256:45b26466b8e899a52e1c3b587e1af2cf8c6d46063ca253088fc50c1349c13b88`.

L'activation des flags shadow a été limitée aux deux processus de replay. Aucune
variable Railway persistante n'a été modifiée et aucun replay complet du
catalogue n'a été lancé.

## Snapshot de production

- déploiement web : `414de5cf-b1a1-4dfa-9fcc-9afda21d6bb5` ;
- déploiement Cron : `00d3ee12-8ac7-4ff4-92b7-158c8d1a7018` ;
- API : `alive=true`, `ready=true`, statut global `ok` ;
- PostgreSQL : `ok`, révision `d5a3c7e9f1b4` ;
- Redis : `ok` ;
- cadence Cron : `Ready`, prochaine occurrence conservée ;
- ingestion catalogue lancée par P3F : aucune ;
- journal catalogue antérieur : run 22 stale, `recovery_required=true`, sans
  rapport avec le replay Offer Truth et sans nouveau blocker Phase 3.

## Git et qualification distante

- dépôt public : `Fredm237/codex-test` ;
- PR d'intégration Offer Truth : `#391` ;
- commit de fusion `main` et branche de production :
  `ecf9596410dc56a1e774a2819e7507e7f956a076` ;
- run CI : `33488434850`, quatre jobs `success` ;
- migrations PostgreSQL, dérive Alembic, régressions catalogue, clients et
  Quality Lab : `success`.

## Limites transmises à Phase 4

- la preuve réelle couvre 1 000 offres, pas le catalogue complet ;
- 670 raws restent quarantinés faute d'identité Variant admissible ;
- shipping, retours et garantie ne sont pas suffisamment observés dans le
  feed audité et restent donc `unknown` ;
- la fraîcheur de 72 h est une policy provisoire, pas un SLO commercial ;
- aucune ground truth humaine externe ne calibre encore le corpus ;
- les lecteurs publics Core v1 restent la seule surface servie ;
- le journal catalogue stale relève du mécanisme d'exploitation existant ;
- l'Immersive Experience demeure interdite jusqu'à sa gate Core propre.

## Passage de phase

La promesse de Phase 3 est satisfaite : une offre favorable exige des faits
courants et sourcés, l'absence de preuve devient une abstention, chaque
snapshot est rejouable et la persistance shadow est idempotente en production.

**Phase 3 est fermée avec le verdict GO. Phase 4 — Product Ontology est
ouverte.** Elle doit maintenant représenter le produit principal, ses rôles,
facettes et relations sans convertir un texte, une catégorie ou une image en
vérité ontologique non prouvée.
