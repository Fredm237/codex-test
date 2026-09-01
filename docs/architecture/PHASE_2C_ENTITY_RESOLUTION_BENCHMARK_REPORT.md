# FILON — Phase 2C Entity Resolution Benchmark Report

- Date : **1er septembre 2026**
- Statut du benchmark : **RATIFIÉ**
- Statut du baseline exact-GTIN : **SAFE_INCOMPLETE**
- Promotion Entity Resolution : **INTERDITE**
- Évaluation : `sha256:a33367af77517a7710e9cba67ee8935abb59e081df31f4b6694e4f30a24cd73b`
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`

## Verdict

Le benchmark Phase 2 est suffisamment alimenté pour mesurer le target de faux
merge, la préservation du GTIN exact, les conflits structurés, les signaux
faibles et le budget d'abstention. Il est déterministe, multi-seed, couvre cinq
verticales et reste séparé des entrées du futur moteur.

Le baseline Phase 1 passe toutes les gates de sécurité mais échoue
volontairement les deux gates de couverture non-GTIN : il s'abstient sur les
965 positifs structurés connus. Ce résultat est attendu et honnête. Il ratifie
le point de départ ; il ne prétend pas que le resolver multi-signal existe ou
qu'il est promouvable.

## Corpus et puissance statistique

Le générateur produit trois seeds, 64 échantillons par verticale et les
surfaces suivantes : smartphones, laptops, pneus, électroménager/HVAC et
audio. Dix régressions statiques empêchent la disparition silencieuse d'une
verticale.

| Population | Cas | Usage |
|---|---:|---|
| Total | 6 730 | évaluation complète |
| Positifs GTIN exact | 960 | non-régression Phase 1 |
| Hard negatives | 3 844 | faux merge et vetos |
| Conflits structurés hors GTIN distinct | 2 884 | abstention obligatoire |
| Signaux faibles uniquement | 961 | titre/image non promotionnels |
| Positifs structurés non-GTIN | 965 | couverture et faux split |

Les hard negatives incluent GTIN différents, attributs de variante
contradictoires, produit principal contre accessoire/consommable et MPN hors
scope Brand. Les positifs structurés portent Brand, MPN, modèle et attribut de
variante concordants, sans GTIN.

## Baseline mesuré

| Gate | Résultat | IC Wilson 95 % | Target | État |
|---|---:|---:|---:|---|
| Préservation exact-GTIN | 960 / 960 | borne basse 99,601 % | ≥ 98 % | PASS |
| Faux merges | 0 / 3 844 | borne haute 0,100 % | ≤ 0,5 % | PASS |
| Abstention sur conflits | 2 884 / 2 884 | borne basse 99,867 % | ≥ 99,5 % | PASS |
| Abstention signaux faibles | 961 / 961 | borne basse 99,602 % | ≥ 99 % | PASS |
| Promotion de conflits connus | 0 | — | 0 | PASS |
| Résolution des positifs structurés | 0 / 965 | borne basse 0 % | ≥ 80 % | **FAIL attendu** |
| Abstention sur positifs structurés | 965 / 965 | borne haute 100 % | ≤ 20 % | **FAIL attendu** |

Les 965 écarts à l'oracle sont exclusivement les positifs structurés que le
baseline exact-GTIN ne sait pas encore résoudre. Aucun écart de sécurité n'est
masqué dans ce total.

## Targets ratifiés

### Sécurité

- borne supérieure Wilson 95 % du faux merge ≤ **0,5 %** ;
- zéro conflit connu promu favorablement ;
- borne basse Wilson 95 % de l'abstention sur conflits ≥ **99,5 %** ;
- borne basse Wilson 95 % de la préservation exact-GTIN ≥ **98 %** ;
- titre/image seuls : abstention avec borne basse ≥ **99 %**.

### Couverture contrôlée

Sur les seuls positifs qui portent au moins deux preuves structurées fortes et
aucun conflit :

- résolution avec borne basse Wilson 95 % ≥ **80 %** ;
- abstention avec borne haute Wilson 95 % ≤ **20 %**.

Ce budget ne s'applique pas aux raws actuels sans MPN/modèle/attributs. Une
offre inéligible faute de preuves peut et doit rester `UNRESOLVED`. Le budget
empêche uniquement le futur moteur de passer artificiellement les gates en
s'abstenant sur tous les cas pourtant qualifiés.

## Reproductibilité et fail-closed

- manifest : `quality/entity-resolution-manifest.json` ;
- régressions : `quality/entity-resolution-regressions.json` ;
- moteur : `quality_lab.entity_resolution` ;
- cinq verticales fermées, trois seeds et holdout non utilisé comme entrée du
  moteur ;
- seuil de faux merge rendu plus permissif, budget de conflit non nul,
  limitation humaine altérée, support statistique ou verticale manquante :
  benchmark invalide ;
- deux runs identiques produisent le même `evaluation_id` ;
- l'option `--require-promotion` échoue tant que P2E/P2G ne passent pas les
  gates de couverture.

## Décision P2C

P2C est fermé : le benchmark et les budgets sont ratifiés. P2D peut maintenant
construire les extracteurs shadow versionnés. P2E devra être évalué sans
modifier ce holdout ni relâcher les gates ; P2G sera seul autorisé à déclarer
le resolver promouvable.
