# FILON — Phase 2E Multi-Signal Resolver Report

- Date locale : **1er septembre 2026**
- Statut : **TERMINÉ LOCALEMENT — SHADOW**
- Resolver : `entity-resolution-shadow-v1`
- Politique : `entity-resolution-policy-v1`
- Évaluation multi-signal : `sha256:00f3594a111513788e27aa8fd744fbbc210ca5f89c83016a135a60c03f20388a`
- Promotion publique : **INTERDITE**

## Verdict

Le candidate generator et le resolver hiérarchique passent le benchmark P2C
sans faux merge ni contournement de conflit. La décision conserve une preuve
par raw, la version de transformation, les candidats et les vetos. Un score
est calculé seulement après la décision de preuve et ne peut jamais lever un
veto.

Cette qualification est déterministe et sans ground truth humaine externe.
Elle prouve le comportement sur le holdout versionné ; elle ne prétend pas que
le feed production actuel contient déjà les champs nécessaires à 965
résolutions réelles.

## Hiérarchie implémentée

1. un GTIN exact valide et unique reste autoritatif ;
2. un identifiant fourni mais invalide ou contradictoire bloque tout fallback ;
3. les candidats non-GTIN sont générés par intersections de signaux sourcés ;
4. MPN ne devient fort que dans un scope Brand concordant ;
5. `HIGH_CONFIDENCE` exige un candidat unique, au moins deux **types** de
   signaux forts distincts et aucun conflit ;
6. une seule preuve forte ou des signaux faibles produisent `PROBABLE`, sans
   identité canonique ;
7. un candidat contredit ou plusieurs candidats produisent `AMBIGUOUS` ;
8. aucune preuve exploitable produit `UNRESOLVED`.

Les conflits bloquants couvrent GTIN, scope Brand/MPN, modèle, attribut de
variante, rôle produit, identifiant invalide et candidats multiples.

## Benchmark multi-signal

| Mesure | Résultat | IC Wilson 95 % | Gate |
|---|---:|---:|---|
| Exact-GTIN préservé | 960 / 960 | borne basse 99,601 % | PASS |
| Faux merges | 0 / 3 844 | borne haute 0,100 % | PASS |
| Conflits en abstention | 2 884 / 2 884 | borne basse 99,867 % | PASS |
| Signaux faibles en abstention | 961 / 961 | borne basse 99,602 % | PASS |
| Positifs structurés résolus | 965 / 965 | borne basse 99,604 % | PASS |
| Abstentions sur positifs structurés | 0 / 965 | borne haute 0,397 % | PASS |
| Écarts à l'oracle | 0 / 6 730 | — | PASS |

Toutes les gates de sécurité, couverture et support statistique du manifest
P2C sont vertes avec l'adaptateur multi-signal. La même suite conserve le
baseline exact-GTIN `SAFE_INCOMPLETE` lorsque l'adaptateur `exact` est demandé,
ce qui empêche de réécrire l'histoire de P2C.

## Contrat de sortie

Les cinq états sont validés par le JSON Schema P2A. Deux cas découverts pendant
l'implémentation ont été explicités sans rendre le contrat plus permissif :

- un seul candidat contredit suffit pour `AMBIGUOUS` ;
- `UNRESOLVED` peut porter zéro evidence lorsqu'aucun signal n'existe ; un
  conflit `AMBIGUOUS` peut s'appuyer sur ses raw IDs si la valeur invalide
  n'est pas normalisable.

Les décisions favorables et `PROBABLE` exigent toujours une evidence
normalisée. `PROBABLE`, `AMBIGUOUS` et `UNRESOLVED` interdisent toujours un
`canonical_id`.

## Vérification ciblée

La suite de 79 tests couvre contrats, extracteurs, resolver, benchmark et
compatibilité Product Identity. Elle vérifie notamment :

- absence de fallback après GTIN invalide ou différent ;
- deux preuves fortes distinctes pour `HIGH_CONFIDENCE` ;
- une preuve forte limitée à `PROBABLE` ;
- titre/image faibles ;
- attribut contradictoire, scope MPN/Brand, aliases conflictuels et roster
  multiple ;
- roster borné à 100 candidats et IDs uniques ;
- conformité JSON de chaque état produit.

## Limites et décision P2E

- aucune table ni migration de persistance Entity Resolution n'est ajoutée à
  cette étape ;
- aucun lecteur public ne consomme ces décisions ;
- le score est descriptif et non calibré sur des observations humaines ;
- le feed réel audité reste principalement sans MPN/modèle/attributs.

P2E est fermé localement. P2F doit maintenant exécuter un replay réel borné,
vérifier que les raws actuels restent abstentionnistes, puis prouver
l'idempotence d'une persistance shadow avant toute revue P2G.
