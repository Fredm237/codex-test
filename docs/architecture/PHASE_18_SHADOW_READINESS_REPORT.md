# Phase 18 — Rapport de préparation shadow Personal Commerce

Date : 2026-09-02

Révision candidate : `b5d3f7a9c1e4`

## Décision actuelle

**P18F = INTEGRATED LOCALLY, NO-GO production.**

Le journal, le writer, l'export, l'effacement et le replay sont construits et
qualifiés localement. La nouvelle tête Alembic est raccordée au runtime et à
la configuration, mais elle n'est ni publiée, ni fusionnée, ni appliquée en
production. Aucun flag, writer, lecteur ou Cron n'a été activé.

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
`filon_test` en loopback. Aucune CI distante n'est déclenchée sans publication.

## Gates encore ouverts

1. exécuter `alembic check`, la suite backend complète et la preuve PostgreSQL
   locale jetable ;
2. publier une branche auditée et obtenir une CI distante verte ;
3. fusionner et appliquer la migration additive en production ;
4. exécuter un seul replay borné `dry-run → apply → replay` avec writer
   temporairement ON et tous les lecteurs OFF ;
5. produire une preuve d'export/effacement sur cohorte consentante avant tout
   canary ;
6. promouvoir la chaîne nécessaire de façon atomique et réversible.

Ce document ne ferme donc pas Phase 18 et ne déclenche pas le mandat créatif
post-Phase 18.
