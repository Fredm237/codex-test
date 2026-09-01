# FILON — PHASE_4_FINAL_RECEIPT

- Date de décision : **1er septembre 2026**
- Verdict : **PHASE 4 = GO**
- Phase suivante : **PHASE 5 — HYBRID RETRIEVAL OUVERTE**
- Lecteurs publics Product Ontology : **NON PROMUS**
- Immersive : **NO-GO inchangé**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Décision exécutive

Phase 4 a livré une ontologie produit versionnée, sourcée, abstentionniste et
persistée en shadow. Un rôle `PRIMARY_PRODUCT` exige désormais un objet vendu
positivement identifié ; une relation textuelle ne devient jamais canonique
sans résolution d'entité positive ; catégories legacy, attributs et facettes
conservent leur provenance et leurs inconnus.

Le benchmark adversarial, la CI PostgreSQL et un replay réel borné convergent.
Le premier passage a créé exactement 1 000 snapshots ; le passage strictement
identique a reconnu les 1 000 snapshots sans création ni divergence. Aucun
risque ouvert d'intégrité ou de récupérabilité nécessaire à Hybrid Retrieval
ne subsiste dans le périmètre de sortie.

## Gates de sortie

| Gate | Verdict | Preuve autoritative |
|---|---|---|
| Contrat Product Ontology | **GO** | ADR-009, schéma v1, roster fermé et unknowns versionnés |
| Rôles | **GO** | 4 615 / 4 615 rôles connus corrects |
| Abstention | **GO** | 4 609 / 4 609 unknowns correctement abstenus |
| Faux `PRIMARY_PRODUCT` | **GO** | 0 / 4 609 ; borne haute Wilson 0,0833 % |
| Relations canoniques | **GO** | 0 fausse promotion sur 4 609 cas |
| Taxonomie / attributs / facettes | **GO shadow** | concepts, types, unités et huit familles versionnés |
| Provenance | **GO** | raw, source, observation, champ et transformation conservés |
| Persistance | **GO** | 1 000 snapshots append-only créés |
| Idempotence | **GO** | second replay : 0 création, 1 000 snapshots existants |
| Schéma / rollback | **GO** | Alembic `e6b4d8f0a2c5`, expansion isolée et flags process-scoped |
| Compatibilité Core | **GO** | aucun endpoint ni lecteur public v1 modifié |
| CI | **GO** | run `33493822607`, quatre jobs `success` |

## Replay production P4F

- instant d'évaluation immuable : `2026-09-01T09:52:35Z` ;
- fenêtre : `after_raw_id=0`, `limit=1000` ;
- sources scannées : 1 000 ;
- sources projetées : 1 000 ;
- liens offre manquants : 0 ;
- statuts : 1 `VERIFIED`, 329 `PARTIAL`, 670 `QUARANTINED`, 0 `INVALID` ;
- couverture de la fenêtre : 0,1 % vérifiée, 32,9 % partielle et 67,0 %
  quarantainée ;
- premier apply : 1 000 créés, 0 existant ;
- apply idempotent : 0 créé, 1 000 existants ;
- identifiant d'évaluation :
  `sha256:c234e72b940ba6f88c363fea72394bd989621c58af5f82527a22234ce423538d`.

L'activation d'Observation, Product Graph, Entity Resolution et Product
Ontology a été limitée aux deux processus d'apply. Aucune variable Railway
persistante n'a été modifiée et aucune ingestion catalogue n'a été lancée.

## Qualification P4G

Le holdout v1.1 contient 18 442 cas sur six verticales et quatre strates
adversariales. L'extracteur `product-ontology-extractor/v1` termine avec zéro
mismatch de rôle, zéro mismatch de relation et zéro échec bloquant. Ses bornes
Wilson satisfont les budgets ratifiés ; le moteur legacy reste `UNSAFE` avec
3 841 faux `PRIMARY_PRODUCT` et 5 378 mismatches de rôle sur le même corpus.

La faible part `VERIFIED` du replay réel n'est pas transformée en échec ni en
succès artificiel : elle mesure la disponibilité actuelle des preuves
ontologiques et des Variant admissibles. La quarantaine est le comportement
fail-closed attendu lorsque ces preuves manquent.

## Snapshot de production

- déploiement web : `7809ce13-ba8b-4691-9848-02d7b75ec590` ;
- déploiement Cron : `51c9d9c8-eb4c-405c-80e3-fcbab1d8845a` ;
- API après replay : `alive=true`, `ready=true`, statut global `ok` ;
- PostgreSQL : `ok`, révision `e6b4d8f0a2c5` ;
- Redis : `ok` ;
- cadence Cron : `Ready`, prochaine occurrence conservée ;
- ingestion catalogue lancée par P4F : aucune ;
- journal catalogue antérieur : run 22 stale, `recovery_required=true`, sans
  rapport avec Product Ontology et sans nouvelle ingestion concurrente.

## Git et qualification distante

- dépôt public : `Fredm237/codex-test` ;
- PR d'intégration Product Ontology : `#393` ;
- commit de fusion `main` et branche de production :
  `cc95f008a75ba68333d0a55805587b7140bd47b5` ;
- run CI : `33493822607`, quatre jobs `success` ;
- migrations PostgreSQL, dérive Alembic, régressions catalogue, clients et
  Quality Lab : `success`.

## Limites transmises à Phase 5

- la preuve réelle couvre 1 000 observations, pas le catalogue complet ;
- 670 raws restent quarantinés et 329 partiels faute de preuves suffisantes ;
- une seule projection est entièrement vérifiée dans la fenêtre auditée ;
- aucune cible textuelle de compatibilité n'est promue sans entité résolue ;
- les huit familles de facettes existent mais leur couverture réelle varie ;
- aucune ground truth humaine externe ne calibre encore le corpus ;
- les lecteurs publics Core v1 restent la seule surface servie ;
- le run catalogue 22 stale relève du chantier d'exploitation existant ;
- l'Immersive Experience demeure interdite jusqu'à sa gate Core propre.

## Passage de phase

La promesse de Phase 4 est satisfaite : le type et le rôle produit ne sont plus
supposés, les relations non résolues restent textuelles, chaque assertion est
rejouable et la persistance shadow est idempotente en production.

**Phase 4 est fermée avec le verdict GO. Phase 5 — Hybrid Retrieval est
ouverte.** Elle doit maintenant générer des candidats produit à haut rappel en
combinant lexical, sémantique et structuré, sans confondre retrieval, ranking
ou optimisation d'offre.
