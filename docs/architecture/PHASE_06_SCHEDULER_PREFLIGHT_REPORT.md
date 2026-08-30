# FILON — qualification du préflight scheduler Railway

- Date : **30 août 2026**
- Lot : **P0.6 / ordonnanceur catalogue autonome**
- Statut : **qualifié localement ; service Cron Railway non créé**
- Décision : **GO technique du préflight ; activation production encore NO-GO**

## Objet

Le scheduler disposait déjà d'un processus mono-exécution distinct du serveur
web. Il lui manquait une commande de qualification exploitable avant
l'activation de la cadence Railway. Le mode suivant est désormais canonique :

```bash
python -m app.ingest.scheduler --check
```

Cette commande ne lance aucune ingestion. Elle valide la configuration du job,
les plafonds de ressources, la présence de la base, puis lit la révision
Alembic et l'état persistant du catalogue. En cas de succès, elle émet un seul
objet JSON expurgé contenant uniquement :

- `status` ;
- `schema_revision` ;
- `interval_hours` ;
- `catalog_state` ;
- `due`.

Aucun jeton, identifiant marchand, hôte ou URL de base n'est affiché.

## Garde-fous fail-closed

Le job et son préflight refusent maintenant ensemble :

- une cadence désactivée ;
- l'absence d'un des deux secrets Awin ;
- l'absence de `DATABASE_URL` ;
- tout mode de schéma autre que `alembic` ;
- `AWIN_MAX_ROWS_PER_FEED` nul ou supérieur à 100 000 ;
- un téléchargement autorisé au-delà de 256 MiB ;
- une décompression autorisée au-delà de 512 MiB ;
- une base non versionnée ou dont la révision diffère de la tête attendue.

Le contrôle du schéma utilise seulement un `SELECT` sur `alembic_version`.
Le chemin DDL historique est explicitement rejeté avant cette lecture.

## Preuves locales

- scheduler ciblé : **14/14** ;
- configuration, migrations et scheduler : **76/76** ;
- backend complet : **2 124 réussis, 2 ignorés** en 65,60 s ;
- compilation Python : **verte** ;
- `git diff --check` : **vert**.

Les tests prouvent que `--check` consulte l'état courant sans jamais appeler
la synchronisation, produit du JSON interprétable et refuse les arguments
inconnus. Le linter Ruff n'est pas installé dans l'environnement local ; ce
contrôle n'est donc pas revendiqué par ce rapport.

## Procédure d'activation future

Après confirmation explicite du coût Railway :

1. créer un service privé depuis la même image et la racine
   `filon-backend`, sans domaine public ;
2. copier les variables de production nécessaires et fixer les trois plafonds
   documentés ;
3. exécuter manuellement `--check` et archiver son JSON expurgé ;
4. seulement si le code vaut 0 et `status` vaut `ready`, remplacer la commande
   par `python -m app.ingest.scheduler` et activer `0 */6 * * *` en UTC ;
5. vérifier un run réel, son journal persistant et l'absence de concurrence.

## Rollback

Le rollback ne demande aucune migration : désactiver la cadence puis supprimer
le seul service scheduler, sans toucher au service web ni à PostgreSQL. Le
préflight est additif et l'ancienne commande mono-exécution reste inchangée.

## Limites

Ce rapport ne prouve ni la création du service, ni un run Awin réel, ni une
cadence Railway. Redis, agrégateur, backend de traces, pager et trafic
représentatif restent également ouverts. Le NO-GO global et le gate humain
Quality restent inchangés.
