# Phase 13 — Mobile Core Companion

Date de référence : 2026-09-02

Branche locale : `codex/filon-phase-13-mobile`

## Objectif

Faire du mobile un compagnon du Product Core, sans recréer un cerveau produit :
scan code-barres exact, consultation fail-closed, suivis et alertes fondés sur une
preuve Core, puis fondations locales du dressing en préparation des Phases 14 et
15.

## Tranches et gates

| Tranche | Livrable | Gate mesurable | État local |
|---|---|---|---|
| P13A | Contrat Mobile Barcode v1 | checksum GS1, canonicalisation identique au Core, zéro faux positif adversarial | **GO** |
| P13B | Scan caméra et saisie manuelle | seulement après action explicite ; aucun code invalide transmis ; 404 distinct d'une panne | **GO code** |
| P13C | Comparaison exacte | identité EAN de réponse identique à la requête ; offre actionnable seulement sur preuve courante/mono-devise/stock explicite | **GO code** |
| P13D | Favoris, seuils et collections | persistance locale validée ; synchronisation sérialisée après authentification ; aucun prix de route considéré comme preuve | **GO code** |
| P13E | Fondation dressing | entrées locales bornées, rôles explicites, déduplication et nettoyage des données invalides | **GO fondation** |
| P13F | Qualification native | caméra réelle iOS/Android, permission refusée, scan EAN-8/UPC/EAN-13/GTIN-14, offline/reprise | **NO-GO — appareil requis** |
| P13G | Promotion | CI distante verte, build EAS qualifié, smoke sur appareil et receipt sans secret | **NO-GO — non exécuté** |

## Frontières

- Product Core reste propriétaire de l'identité produit, des offres, prix,
  devises, stocks et historiques.
- Le mobile n'écrit aucune table produit ou shadow.
- Le code brut lu par la caméra reste local ; seul le GTIN canonique validé est
  envoyé par la route de lecture catalogue déjà publique.
- Favoris, seuils et dressing sont personnels. Ils restent locaux ou transitent
  par le service d'identité après consentement/authentification ; ils ne servent
  jamais à fabriquer une vérité produit.
- Les lecteurs shadow et flags persistants restent OFF. Aucun Cron n'est ajouté.

## Conditions de promotion

P13F exige, sur au moins un appareil iOS et un appareil Android compatibles :

1. permission caméra accordée et refusée sans boucle ni écran bloqué ;
2. 100 % du corpus physique lisible correctement classé en exact/not found ;
3. 0 code au checksum invalide envoyé au Core ;
4. 0 action marchande sur preuve absente, expirée, multidevise ou hors stock ;
5. reprise réseau sans doublon d'alerte ou de collection ;
6. VoiceOver/TalkBack : contrôles nommés et ordre de focus utilisable.

P13G exige ensuite la CI distante complète, un artefact EAS reproductible et les
smokes native documentés. Aucun de ces gates ne peut être remplacé par les tests
unitaires locaux.
