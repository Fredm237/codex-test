# FILON — PHASE_1_FINAL_RECEIPT

- Date de décision : **31 août 2026**
- Verdict : **PHASE 1 = GO**
- Phase suivante : **PHASE 2 — ENTITY RESOLUTION OUVERTE**
- Lecteurs publics Product Graph : **NON PROMUS**
- Immersive : **NO-GO inchangé**

## Décision exécutive

Phase 1 a livré une identité Variant exacte par GTIN, sourcée, idempotente et
réversible en shadow. Le système s'abstient lorsqu'une preuve forte manque et
ne déduit pas Brand canonique, Family, Model ou MPN depuis un titre marchand.

Le benchmark autonome, la CI PostgreSQL et un backfill réel borné convergent :
aucun faux merge déterministe, faux split GTIN, lien résolu incomplet,
collision silencieuse ou duplication de replay n'a été observé. Aucun risque
ouvert d'intégrité ou de récupérabilité nécessaire à Entity Resolution ne
subsiste dans le périmètre de sortie.

## Gates de sortie

| Gate | Verdict | Preuve autoritative |
|---|---|---|
| Contrat d'identité | **GO** | ADR-006 et contrats Brand/Family/Model/Variant versionnés |
| Exact-product | **GO** | 960/960, borne Wilson basse 99,601 % |
| Variant resolution | **GO** | 3 840/3 840 dans le benchmark ; 330 exact-GTIN réels |
| Offer attachment | **GO** | 2 880/2 880 ; 1 000/1 000 raws réels reliés à une Offer |
| Faux merge | **GO** | 0/2 880 hard negatives ; 0 variante réelle avec GTIN contradictoires |
| Faux split | **GO borné** | 0 GTIN réel réparti entre plusieurs variantes |
| Unknown / abstention | **GO** | 670 `missing_gtin` restent en quarantaine sans fallback |
| Provenance | **GO** | 330 preuves d'identifiant et 2 330 assertions sourcées |
| Idempotence | **GO** | replay réel : 0 nouvelle assertion, lien ou variante |
| Schéma / rollback | **GO** | Alembic `b3e1a7c4d9f2`, expansion isolée et flags shadow |
| Compatibilité Core | **GO** | aucune lecture publique v1 ni contrat v1 modifié par le Graph |
| CI | **GO** | run `33425556598`, quatre jobs `success`, benchmark inclus |

## Snapshot de production

- déploiement web : `e2a434b4-aedd-47c7-9532-7c6de39cdb67` ;
- API : `alive=true`, `ready=true`, statut global `ok` ;
- PostgreSQL : `ok`, révision `b3e1a7c4d9f2` ;
- Redis : `ok` ;
- catalogue : `fresh`, dernier succès public run `19` ;
- corpus shadow : 1 000 raws, 10 000 observations ;
- Graph : 321 variantes, 321 identifiants, 330 preuves, 1 000 liens ;
- assertions : 2 330, dont 1 000 `observed` et 1 330 `validated` ;
- résolutions : 330 `resolved / exact_gtin`, 670
  `quarantine / missing_gtin` ;
- ingestion concurrente : aucune observée pendant les opérations P1E/P1F.

## Git et qualification distante

- dépôt public : `Fredm237/codex-test` ;
- PR d'intégration Product Identity : `#386` ;
- commit de fusion `main` :
  `98f93c79ce9a134cbe5fe90817782532de8da051` ;
- run CI : `33425556598` ;
- job Backend/contrats/Quality Lab : `99598128288`, `success` ;
- migrations PostgreSQL, régressions catalogue, Quality Lab autonome et
  benchmark Product Identity : `success`.

## Limites transmises à Phase 2

- la preuve réelle couvre 1 000 offres d'un seul feed Awin, pas le catalogue
  complet ;
- 67 % du lot n'a pas de GTIN et reste volontairement non résolu ;
- Family, Model, MPN, attributs complexes et rapprochements multi-source ne
  sont pas encore produits ;
- le backfill doit être vectorisé ou regroupé avant extension massive ;
- `NO_EXTERNAL_HUMAN_GROUND_TRUTH` reste explicite ;
- les lecteurs publics Core v1 restent la seule surface servie ;
- le premier événement GitHub `schedule` du moniteur Phase 0 reste une
  limitation fournisseur non bloquante s'il n'a pas encore été créé ;
- l'Immersive Experience demeure interdite jusqu'à sa gate Core propre.

## Passage de phase

La promesse de Phase 1 est satisfaite : une même preuve GTIN converge vers une
seule Variant, une preuve contradictoire ne peut pas être fusionnée
favorablement, chaque décision est sourcée et le replay ne duplique rien.

**Phase 1 est fermée avec le verdict GO. Phase 2 — Entity Resolution est
ouverte.** Elle doit augmenter la couverture au-delà du GTIN exact par des
preuves structurées, des relations Brand/Family/Model/Variant et des
abstentions mesurées, sans affaiblir les invariants acquis ici.
