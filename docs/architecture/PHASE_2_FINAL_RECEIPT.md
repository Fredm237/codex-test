# FILON — PHASE_2_FINAL_RECEIPT

- Date de décision : **1er septembre 2026**
- Verdict : **PHASE 2 = GO**
- Phase suivante : **PHASE 3 — OFFER TRUTH OUVERTE**
- Lecteurs publics Product Graph : **NON PROMUS**
- Immersive : **NO-GO inchangé**
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Décision exécutive

Phase 2 a livré un resolver Entity Resolution multi-signal, explicable,
abstentionniste et persistant en shadow. Le moteur préserve l'identité GTIN
exacte, interdit tout fallback après identifiant invalide ou contradictoire,
exige plusieurs preuves fortes pour une décision canonique non-GTIN et refuse
les conflits au lieu de les masquer par un score.

Le benchmark adversarial, la CI PostgreSQL et un replay réel borné convergent :
aucun faux merge ou conflit promu n'est observé, les 330 exact-GTIN sont
préservés, les 670 raws sans preuve structurée restent `UNRESOLVED`, et le
second replay ne duplique aucune projection ni décision. Aucun risque ouvert
d'intégrité ou de récupérabilité nécessaire à Offer Truth ne subsiste dans le
périmètre de sortie.

## Gates de sortie

| Gate | Verdict | Preuve autoritative |
|---|---|---|
| Contrat de décision | **GO** | ADR-007, cinq états, preuves et conflits versionnés |
| Exact-product | **GO** | 960/960 au benchmark ; 330/330 exacts réels préservés |
| Faux merge | **GO** | 0/3 844 hard negatives, borne Wilson haute 0,100 % |
| Conflits | **GO** | 2 884/2 884 abstentions ; zéro conflit promu |
| Signaux faibles | **GO** | 961/961 abstentions ; titre/image jamais autoritatifs seuls |
| Couverture structurée | **GO borné** | 965/965 positifs structurés résolus sur le holdout versionné |
| Provenance | **GO** | 1 000 projections réelles, sources et transformations versionnées |
| Idempotence | **GO** | replay réel : 0 création, 1 000 projections et décisions existantes |
| Schéma / rollback | **GO** | Alembic `c4f2b8d5e0a3`, expansion isolée, flags revenus à `false` |
| Compatibilité Core | **GO** | aucun lecteur public v1 modifié par Entity Resolution |
| CI | **GO** | run `33454869610`, quatre jobs `success` |
| Gate P2G | **GO** | neuf contrôles PASS, reçu `sha256:15ab40f3…86ec4` |

## Snapshot de production

- déploiement web : `44a4570c-e939-4de9-b74a-5e4e4b781494` ;
- déploiement Cron : `8a7b3077-35fb-46a0-a35d-d19e7ac282ae` ;
- API : `alive=true`, `ready=true`, statut global `ok` ;
- PostgreSQL : `ok`, révision `c4f2b8d5e0a3` ;
- Redis : `ok` ;
- flags observation, Product Graph et Entity Resolution : `false` ;
- fenêtre shadow : 1 000 raws, 321 profils candidats ;
- décisions : 330 `EXACT_VERIFIED`, 670 `UNRESOLVED`, aucune promotion
  `HIGH_CONFIDENCE` non prouvée ;
- replay : 1 000 projections et décisions reconnues, aucune création ;
- ingestion catalogue concurrente : aucune exécution Railway active pendant
  P2F/P2G ; le run journalisé `21` reste stale et récupérable fail-closed.

## Git et qualification distante

- dépôt public : `Fredm237/codex-test` ;
- PR d'intégration Entity Resolution : `#388` ;
- PR de correction worker autonome : `#389` ;
- commit de fusion `main` qualifié :
  `076a6a2bf83cefa8435fa49cf5c8a52e3c5c4661` ;
- branche publique : `codex/filon-phase-0-core` ;
- run CI : `33454869610`, quatre jobs `success` ;
- migrations PostgreSQL, régressions catalogue, contrats et benchmark Entity
  Resolution : `success`.

## Limites transmises à Phase 3

- la preuve réelle couvre 1 000 offres d'un seul feed Awin, pas le catalogue
  complet ;
- le feed réel audité ne porte pas encore assez de MPN, modèles et attributs
  structurés pour produire des résolutions non-GTIN canoniques ;
- le score reste descriptif et non calibré sur une ground truth humaine
  externe ;
- `NO_EXTERNAL_HUMAN_GROUND_TRUTH` reste explicite ;
- les lecteurs publics Core v1 restent la seule surface servie ;
- le journal catalogue stale doit être récupéré par le mécanisme d'exploitation
  existant, sans créer de gate Entity Resolution ;
- l'Immersive Experience demeure interdite jusqu'à sa gate Core propre.

## Passage de phase

La promesse de Phase 2 est satisfaite : une preuve exacte reste exacte, des
preuves structurées concordantes peuvent être résolues sans affaiblir les
vetos, toute ambiguïté reste une abstention, chaque décision est rejouable et
la persistance shadow est idempotente en production.

**Phase 2 est fermée avec le verdict GO. Phase 3 — Offer Truth est ouverte.**
Elle doit maintenant établir prix, stock, livraison, vendeur, fraîcheur et
preuve d'offre comme faits temporels sourcés, sans transformer l'identité
shadow en lecture publique prématurée.
