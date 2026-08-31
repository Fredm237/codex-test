# ADR-002 — Raw Source, Observation et Quarantine

- Statut : **accepté pour shadow**
- Date : 28 août 2026
- Périmètre : ingestion Awin ; aucun lecteur v1
- Feature flag : `OBSERVATION_SHADOW_ENABLED=false` par défaut

## Contexte

L'ingestion actuelle transforme directement une ligne Awin en `Offer`. Une fois
la ligne normalisée, il est impossible de distinguer la valeur source, la
transformation appliquée et l'incertitude, ou de reconstruire le résultat avec
une nouvelle version des règles. Les lignes invalides sont principalement
ignorées ou converties en `None`, sans preuve durable expliquant le rejet.

Le Product Graph ne peut pas devenir une source de vérité s'il dépend d'une
transformation non rejouable et si un incident de feed efface son propre
contexte.

## Décision

Ajouter, en expansion uniquement, trois tables parallèles :

1. `raw_source_records` conserve le payload reçu, sa source, son checksum et
   une clé de replay. Les enregistrements sont immuables au niveau applicatif et
   dédupliqués par événement source (record, contenu et date d'observation).
2. `observations` conserve un fait par champ avec sujet, valeur, statut
   `verified | inferred | unknown`, provenance, date, confiance et version de
   transformation.
3. `quarantine_records` conserve les anomalies structurées avec code d'erreur,
   étape, champ, motif et cycle de résolution. Le raw n'est jamais supprimé.

La projection Awin est une fonction déterministe du payload, du contexte source
et de la version de transformation. Rejouer deux fois la même entrée avec la
même version produit le même checksum, les mêmes observations et les mêmes
anomalies.

Le writer shadow s'exécute dans un savepoint. Son échec est observable mais ne
fait pas échouer l'upsert v1. Aucun endpoint, ranking ou regroupement actuel ne
lit ces tables.

## Sémantique d'inconnu

- champ absent : observation `unknown`, valeur SQL `NULL`, confiance `0` ;
- valeur brute invalide : observation `unknown` + quarantaine ;
- valeur source correctement observée : `verified` ;
- taxonomie/rôle produit dérivé par une règle : `inferred`, jamais `verified` ;
- `unknown`, `false`, `0` et `not_applicable` restent distincts.

## Alternatives rejetées

- **Ajouter uniquement des colonnes à `offers`** : ne conserve ni historique de
  transformation, ni replay, ni anomalies.
- **Stocker seulement le CSV compressé** : utile pour l'archive, insuffisant pour
  une lineage par record et un replay idempotent.
- **Remplacer immédiatement l'ingestion v1** : big bang contraire aux gates et
  sans benchmark indépendant.
- **Utiliser le LLM pour corriger les lignes suspectes** : non déterministe et
  incompatible avec la source de vérité.

## Migration

1. Migration Alembic expand-only des trois tables et index.
2. Déploiement avec flag désactivé.
3. Activation sur ingestion limitée, puis comparaison des comptes/checksums.
4. Replay de lots réels et mesure des taux d'unknown/quarantaine.
5. Aucun lecteur v2 avant validation du Quality Lab.

## Rollback

Rollback immédiat : remettre `OBSERVATION_SHADOW_ENABLED=false`. Les lectures v1
ne changent pas. La migration descendante peut supprimer les trois tables
uniquement après export de leurs données et seulement tant qu'aucun lecteur v2
n'en dépend. Les tables Core, les offres et l'historique de prix ne sont jamais
modifiés par ce downgrade.

## Gates de sortie P0.e

- migration upgrade/downgrade et drift verts ;
- projection déterministe et idempotente ;
- valeur inconnue jamais convertie en valeur favorable ;
- anomalie conservée avec son raw ;
- activation/désactivation testée ;
- tests v1 inchangés et suite backend complète verte.
