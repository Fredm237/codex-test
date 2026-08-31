# FILON — qualification du préflight scheduler Railway

- Date : **30 août 2026**
- Lot : **P0.6 / ordonnanceur catalogue autonome**
- Statut : **qualifié localement et à distance ; service Cron Railway activé**
- Décision : **GO technique du préflight et GO activation ; premier cycle réel en cours**

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

## Preuves distantes et production web

Le commit applicatif local `8594bd84fd4e60166dc852637807f130da752213`
et le commit distant
`5ab3c3c0da28c2df6433d773d897f1a29e6f12ec` portent exactement le même
arbre `e2124704b30d405f5d7215f4acc95bc5246dc570`. La branche publique
`codex/filon-phase-0-core` pointe sur cette référence distante.

GitHub Actions #362 (`33334944805`) a qualifié :

- Web, Mobile et Extension : **succès** ;
- baseline, stamp, drift et restauration Alembic : **succès** ;
- régressions backend, y compris le scheduler : **succès** ;
- readiness Quality normale : **succès** ;
- gate humain strict : **échec attendu**, exclusivement parce que les sept
  datasets humains restent vides.

L'artefact Quality `9738761749`, nommé
`quality-readiness-4edf53447cd19a7ab3be67d1215e867d9959f598`, porte le
digest
`sha256:751ccb0860009fcad22a12c2fddae8b6dc1fc36b2c58ac2f51df4456f10298a9`
et expire le 13 septembre 2026.

Railway a automatiquement déployé ce commit sur le **service web existant**,
sous l'identifiant `d1e17b10-fce8-4f16-90d9-68aadbac4747`, avec le statut
`Deployment successful`, en EU West et avec un réplica. Après déploiement :

- `/health/live` a retourné `alive=true` ;
- `/health/ready` a retourné `ready=true`, PostgreSQL `ok` et la révision
  `e8c3f6a0b5d2`.

Ce déploiement rend le binaire de préflight disponible dans l'image commune ;
il ne crée pas et n'exécute pas un service scheduler.

## Activation exécutée le 31 août 2026

La procédure ci-dessous a été exécutée sur le service privé
`filon-catalog-cron` (`b45d89cd-7be9-4e0e-b40e-0983fdf32c0e`). Le préflight
Railway `712c31cf-dff3-4f08-8fc4-d4956611c93c` a rendu `status=ready`,
`due=true`, l'intervalle 6 h et la révision `e8c3f6a0b5d2`, sans écriture.
L'image active `88cd96b7-6311-441b-8192-ae58e846c60d` exécute maintenant le
scheduler à la cadence `0 */6 * * *` UTC. Le premier cycle réel est suivi dans
le [reçu Redis/Cron](PHASE_06_REDIS_CRON_ACTIVATION_REPORT.md).

## Procédure d'activation appliquée

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

Le service, la cadence et un run Awin réel sont désormais prouvés. Le premier
cycle du nouveau service reste actif au moment de cette mise à jour : ses
compteurs terminaux ne sont pas encore revendiqués. Agrégateur, backend de
traces, pager, trafic représentatif et données humaines restent ouverts. Le
NO-GO global et le gate humain Quality restent inchangés.
