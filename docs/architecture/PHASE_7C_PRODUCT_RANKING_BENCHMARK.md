# FILON — Phase 7C Product Ranking Benchmark

- Date : **1er septembre 2026**
- Périmètre : **holdout synthétique autonome**
- Limitation : `NO_EXTERNAL_HUMAN_PREFERENCE_GROUND_TRUTH`
- Évaluation sûre : `sha256:ec1b8484f5f5e27bb41355addad3f272c2a9f552cb1d1ead8489717b57ab1ffa`
- Contrôle négatif : `sha256:11008ba9ab06dd42aa59498677cad2b3ff89b9148aa1cf81613e1dcff1565e03`

## Corpus

Le générateur produit 4 608 cas déterministes sur six verticales, trois langues,
huit seeds et six scénarios adversariaux : ordre exact, bascule de poids par
verticale, dimension inconnue, tentative de réintroduction d'un exclu, mutation
de commission et stabilité des égalités.

## Résultats techniques

| Mesure | Product Ranking sûr | Contrôle universel commercial |
|---|---:|---:|
| ordre exact | 4 608 / 4 608 | 452 / 4 608 |
| exactitude ordre | 100 % | 9,809028 % |
| borne basse Wilson 95 % | 99,916704 % | non ratifiée |
| top-1 exact | 100 % | 27,756076 % |
| candidats inéligibles classés | 0 | 720 |
| candidats avec unknown classés | 0 | 720 |
| échecs d'invariance affiliation | 0 | 4 608 |
| provenance complète | 100 % | 0 % |
| verdict ingénierie | **PASS** | **UNSAFE** |

## Gate humain

Le manifest exige au moins 200 jugements humains externes. Le corpus courant en
contient 0 : `PENDING_EXTERNAL_GROUND_TRUTH`. Par conséquent,
`engineering_passed=true` mais `phase_gate_passed=false` et `passed=false`.
La CI utilise `--strict-engineering` afin de détecter toute régression technique
sans fabriquer une ratification humaine.
