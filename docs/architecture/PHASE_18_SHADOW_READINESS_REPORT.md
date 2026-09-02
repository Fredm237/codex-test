# Phase 18 — Rapport de préparation shadow Personal Commerce

Date : 2026-09-02

Révision candidate : `b5d3f7a9c1e4`

## Décision actuelle

**P18F = GO shadow production. P18G canary/public = NO-GO.**

Le journal, le writer, l'export, l'effacement et le replay sont construits,
qualifiés et déployés. La migration `b5d3f7a9c1e4` est appliquée en production
et le triplet borné dry-run, apply unique, replay identique est terminalement
vert. Le secret HMAC est configuré dans Railway sans être consigné. Les flags,
writers persistants, lecteurs publics et Cron Personal Commerce restent OFF.

## Contrat de persistance

`personal_commerce_decision_runs` conserve uniquement :

- une référence au run BUY/WAIT amont ;
- l'empreinte de l'objectif et du résultat ;
- le statut de consentement ;
- un identifiant sujet HMAC-SHA-256 uniquement si le consentement est actif ;
- l'action, la solution sélectionnée, des compteurs et codes raison bornés ;
- l'horodatage d'évaluation.
- une échéance de conservation obligatoire pour toute décision consentie.

Le contexte brut, les préférences, les identifiants de préférence, les profils,
les tailles, les budgets et les données de garde-robe ne sont pas persistés.
Une décision sans consentement doit être une abstention. Une action `BUY` ou
`WAIT` divergente du run amont est refusée.

`personal_commerce_erasure_receipts` ne conserve ni sujet ni digest sujet. Sa
clé idempotente est une empreinte combinant le HMAC du sujet et la référence
opaque de la demande. Une reprise de la même demande, même avec un nouvel
horodatage, retourne le reçu existant et vérifie que plus aucun enregistrement
du sujet ne subsiste.

## Export et effacement

- l'export est filtré par HMAC sujet et n'expose jamais ce HMAC ;
- le format `personal-commerce-portable-export/v1` restitue uniquement les
  décisions appartenant au sujet ;
- l'effacement possède un mode sec, un mode apply et un replay idempotent ;
- le reçu n'est écrit qu'après une requête de vérification à zéro ;
- une nouvelle donnée apparue après un effacement empêche silencieusement de
  réutiliser l'ancien reçu comme fausse preuve.
- une décision consentie sans échéance, ou dont l'échéance n'est pas future,
  est refusée ;
- le purgeur de rétention possède les mêmes modes dry-run/apply/replay et
  produit un reçu agrégé seulement après vérification à zéro.

## Replay borné

Le replay lit au maximum 100 runs BUY/WAIT après un identifiant explicite. En
l'absence actuelle d'une cohorte consentante et de solutions Phase 17
persistées, il ne fabrique ni sujet ni préférence : il produit uniquement des
abstentions `personalization_consent_missing`. Le mode apply exige le futur
flag `PERSONAL_COMMERCE_SHADOW_ENABLED`.

## Preuves locales

| Contrôle | Résultat |
|---|---|
| Moteur et benchmark Personal Commerce | **PASS** |
| Persistance dry/apply/replay | **PASS** |
| Consentement absent → abstention | **PASS** |
| Sujet sans consentement refusé | **PASS** |
| Secret HMAC faible ou absent refusé | **PASS** |
| Action BUY/WAIT liée à la preuve amont | **PASS** |
| Export isolé par sujet, sans digest exposé | **PASS** |
| Effacement dry/apply/replay | **PASS** |
| Échéance obligatoire et purge de rétention | **PASS** |
| Migration SQLite upgrade/downgrade | **PASS** |
| FK BUY/WAIT restrictive | **PASS** |
| Total ciblé | **19 tests réussis** |
| Intégration configuration + migration + P18 | **91 tests réussis** |
| Suite backend complète | **2 639 réussis, 3 sautés, 1 refus sandbox** |
| Test OTLP refusé par la sandbox, rejoué avec loopback | **1/1 réussi** |
| Preuve PostgreSQL locale | **3 tests sautés — `TEST_POSTGRES_URL` absent** |

La qualification locale couvre donc les 2 640 tests exécutables dans cet
environnement. Les trois tests PostgreSQL restent une gate CI distincte : ils
ne sont pas présentés comme réussis avant exécution sur la base jetable
`filon_test` en loopback. Cette preuve est maintenant apportée par la CI
distante décrite ci-dessous.

## Qualification distante

- PR de qualification : `#413`, ouverte et non fusionnée ;
- tête GitHub qualifiée : `78b172296900efe51ad2a4cef46119a19b1f7642` ;
- run GitHub Actions : `33654292272`, terminal `success` ;
- Backend, contrats et Quality Lab : `success`, avec PostgreSQL 16 jetable,
  migrations Alembic, détection de drift et benchmark Personal Commerce ;
- Web : `success` ;
- Mobile : `success` ;
- Extension : `success` ;
- artefact : `quality-readiness-4d42b77f41355c65a4986b35e7bf5c0fd59a79b1`,
  digest `sha256:7ff1660e2c5ee3e5596413e22187ce314d9ae56e1c8c8741d0618b3beed69667`,
  expiration annoncée au `2026-09-16T16:26:10Z`.

Cette preuve ferme la gate CI et la preuve PostgreSQL jetable. Elle n'autorise
ni fusion, ni migration de production, ni activation du writer ou d'un lecteur.

## Qualification production

- PR `#413` fusionnée au commit
  `e48529bfde73c958f15ae00e1eaff953d382fedc` ;
- CI `main` `33656618219` : quatre jobs terminaux `success` ;
- déploiements Railway `c60a2674-ff63-4832-ac68-1c9335a288c7` puis
  `d444580f-6977-4610-83eb-4797b1ddd087` : `success` ;
- schéma production : `b5d3f7a9c1e4` ;
- replay d'une source BUY/WAIT : `0 -> 1 -> 1` ligne entre dry-run, apply et
  replay, identité inchangée ;
- ligne produite : abstention sans consentement, sans sujet, sans contexte brut
  et sans solution synthétique ;
- configuration persistante : writer P18 OFF, chaîne V2 OFF, lecteurs canary et
  public OFF.

Le reçu détaillé est `PHASE_18_PRODUCTION_QUALIFICATION_REPORT.md`.

## Gates encore ouverts

1. produire une preuve d'export/effacement sur cohorte consentante avant tout
   canary ;
2. promouvoir la chaîne nécessaire de façon atomique et réversible.

P18F est fermé. Ce document ne ferme pas P18G et n'autorise aucun lecteur
canary ou public.
