# Phase 15 — Wardrobe Intelligence

Date de référence : 2026-09-02

Branche locale : `codex/filon-phase-15-wardrobe`

## Objectif

Établir un dressing personnel déterministe, effaçable et fondé uniquement sur
les déclarations explicites de la personne. Ce lot ne crée aucune identité
produit, n'infère aucune préférence et ne transmet aucune pièce hors de
l'appareil.

## Tranches

| Tranche | Preuve requise | État local |
|---|---|---|
| P15A — contrat | schéma versionné, provenance et périmètre de stockage explicites | **GO** |
| P15B — persistance | migration locale v1 → v2, validation stricte, limite de 40 pièces | **GO** |
| P15C — consentement | seules les pièces saisies par la personne sont conservées | **GO** |
| P15D — mutations | écritures concurrentes sérialisées, déduplication, export versionné et effacement vérifié | **GO** |
| P15E — expérience | réutilisation dans Complete, notice locale, suppression unitaire et totale | **GO local** |
| P15F — profil synchronisé | contrat Profile, authentification, consentement réseau et portabilité | **NO-GO — hors lot** |
| P15G — public | build natif, accessibilité et effacement qualifiés sur appareils | **NO-GO — non exécuté** |

## Invariants

1. `provenance = user_declared` pour chaque pièce ;
2. `storageScope = local_device` pour chaque pièce ;
3. aucun score ou signal de préférence n'est déduit du contenu ou de l'absence ;
4. une date invalide ou une chronologie inversée est rejetée ;
5. les mutations concurrentes ne peuvent pas écraser une pièce validée ;
6. l'effacement supprime le magasin courant et toute copie legacy ;
7. aucune écriture réseau, table backend, table shadow, writer ou Cron n'est créé.
8. la conservation locale dure jusqu'à l'effacement explicite par la personne ;
9. l'export est un instantané versionné produit localement, sans transfert implicite ;
10. un reçu d'effacement n'est émis qu'après relecture des deux clés v1/v2 à `null`.

## Conditions LOCAL → DEVICE CANARY

- 100 % du corpus adversarial qualifié ;
- zéro pièce inventée ou importée implicitement ;
- migrations v1 → v2 et effacement testés sur stockage persistant réel ;
- parcours VoiceOver/TalkBack, clavier, contraste et cibles tactiles validés ;
- build natif signé installé sur au moins un appareil iOS et un appareil Android ;
- perte, duplication et ordre des mutations mesurés à zéro sur les scénarios de
  fermeture/reprise de l'application.

## Conditions DEVICE CANARY → PUBLIC

- cohorte explicite, réversible et observable sans contenu personnel brut ;
- taux d'échec de lecture, écriture, migration et effacement sous les seuils
  ratifiés avant activation ;
- confirmation visible du stockage local et accès permanent à l'effacement ;
- rollback applicatif testé sans rendre les données v2 illisibles ;
- revue confidentialité et sécurité mobile terminée ;
- flags Intelligence/Fashion/Outfit activés uniquement pour la cohorte décidée.

Une future synchronisation serveur constitue un produit différent : elle exige
un contrat de consentement, une politique de rétention, export/effacement, une
authentification forte et une autorisation de transport séparée.
