# Phase 14 — Rapport de qualification locale

Date : 2026-09-02

## Décision

**P14A–P14E = GO local. P14F–P14G = NO-GO production.**

| Contrôle | Résultat |
|---|---|
| Benchmark Fashion v1 | **PASS**, 10 cas |
| Exactitude de décision | **1,00** |
| Exactitude d'identité sélectionnée | **1,00** |
| Fausses recommandations | **0** |
| Sorties explicitement non calibrées | **1,00** |
| Tests backend ciblés | **42/42** |
| Suite backend globale locale | **93 réussis, 0 échec**, puis exécution bornée à 2 % ; CI complète requise avant fusion |
| Tests mobile Fashion ciblés | **33/33** |
| TypeScript | **PASS** |

## Correction de vérité

Le backend gardait déjà `style_score` et `confidence_score` à `null`, mais le
graphe Fashion mobile attribuait encore des scores de relation `0.72` et `0.6`,
une confiance `medium` et une pénalité numérique arbitraire. Ces nombres n'étaient
adossés à aucune calibration indépendante.

Ils sont désormais remplacés par :

- `score: null` ;
- `confidence: not_calibrated` ;
- `scorePenalty: null` ;
- des constats explicites `info` ou `advisory`.

## Corpus adversarial

Le corpus couvre une robe actuelle, une preuve périmée, un stock inconnu, un
budget EUR face à une devise étrangère, la collision cosmétique « La Petite Robe
Noire », un costume thématique non demandé, des chaussures enfant/sport pour le
travail, une chaussure Oxford documentée, un complément multidevise et un prix
non positif.

## Limites

Le benchmark prouve les invariants techniques de sélection et d'abstention. Il
ne prouve pas qu'une tenue est belle, adaptée à une personne, bien taillée ou
préférée humainement. Les trois flags Intelligence/Fashion/Outfit restent OFF ;
aucun lecteur public, replay production ou canary n'est activé par ce lot.
