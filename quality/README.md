# FILON Quality Lab v0.5

Le Quality Lab mesure la qualité métier sur un holdout humain indépendant. Son
état courant reste volontairement **NOT READY** : aucun score de lancement ne
peut être dérivé des 14 cas historiques, d'annotations synthétiques ou d'un
lot trop petit pour prouver les seuils.

## Contrat de lancement

| Jeu | Minimum total | Minimum test | Risque principal |
|---|---:|---:|---|
| Taxonomy | 1 000 | 500 | catégorie, sous-catégorie et rôle produit |
| Entity Resolution | 2 000 | 1 000 | faux merge, faux split, relation de variante |
| Variant Resolution | 500 | 200 | variante et attributs exacts |
| Offer Attachment | 1 000 | 500 | rattachement et fausse éligibilité |
| Offer Truth | 1 000 | 500 | prix, stock, livraison et lien affilié |
| Retrieval | 3 000 | 1 300 | top-1 exact, résultats absurdes, pertinence top-3, recall@50, NDCG@10, contraintes top-10 |
| Decision | 500 | 500 | décision, claims, preuves et abstention |

La readiness vérifie aussi les strates nécessaires aux mesures : 500 cas
Taxonomy, 800 paires produit `different`, 200 `same`, 200 vraies relations de
variante, 200 cas Variant, 500 offres dont 200 éligibles et 200 non éligibles,
et 500 vérités d'offre. Parmi les 1 300 requêtes Retrieval du holdout, elle exige
au moins 475 cas répondables, dont 300 recherches exactes, 600 `no_match` et 225
cas ambigus. Elle exige enfin 500 décisions, 381 décisions
non-abstentionnistes et au moins 1 000 observations de calibration. Les minima
total et test sont indépendants : le split déterministe peut nécessiter de
collecter plus que le minimum brut. Un volume suffisant mais mal stratifié
reste `not_ready`.

Chaque cas porte obligatoirement `strata.scenario_type`, `strata.language` et
`strata.vertical`. Le manifeste exige du support pour les dix scénarios du
mandat, les langues FR/NL/EN et les cinq verticales initiales smartphones,
laptops, TV, audio et appliances. Ces supports de couverture sont calculés
uniquement sur les golds Retrieval test intègres ; les strates des autres jeux
ne peuvent pas rendre une recherche mesurable. Une strate Retrieval absente
bloque readiness et scorecard.

Les gates binomiaux de taux/accuracy et la couverture sourcée utilisent la
borne conservatrice d'un intervalle de Wilson à 95 %, pas seulement
l'estimation ponctuelle. La recherche exacte doit ainsi prouver au moins 98 %
de bons produits en première position sur 300 cas dédiés. Un cas exact porte un
ensemble fermé `exact_product_ids`, non vide, inclus dans les produits pertinents ;
seul un de ces équivalents exacts en première position compte comme succès. Le
taux de résultat absurde utilise la borne haute de Wilson et doit rester
strictement inférieur à 1 % ; 600 cas `no_match` permettent encore de prouver ce
seuil avec une erreur. La précision@3 reste publiée comme métrique descriptive,
tandis que la gate Top-3 mesure par requête la présence binaire d'au moins un
produit pertinent dans les trois premiers résultats. `recall@50` et `NDCG@10`
utilisent la borne basse d'une borne
empirique de Bernstein à 95 % sur les scores par requête. `ECE` utilise la borne
haute d'un bootstrap percentile déterministe à 2 000 rééchantillonnages. Un
seul cas ne peut donc jamais prouver une gate. Les contraintes et claims non
sourcés restent des compteurs à tolérance zéro.

Chaque gold et prédiction Retrieval déclare explicitement `matched`,
`no_match` ou `ambiguous`. Un cas `matched` exige au moins un produit pertinent ;
les deux autres interdisent tout produit pertinent ou résultat retourné. Les
cas sans résultat ne peuvent ainsi plus être exclus silencieusement des
métriques. Hors scénario `exact_product` répondable, `exact_product_ids` est
obligatoirement vide.

## Intégrité des données

- roster fermé de sept datasets et schémas Draft 2020-12 versionnés ;
- split canonique par `group_id`, identifiants NFC et détection des fuites entre
  train/dev/test ;
- JSON strict : clés dupliquées, nombres non finis et UTF-8 invalide refusés ;
- deux `annotator_id` distincts, puis un troisième identifiant distinct en cas
  de désaccord ; le caractère humain et l'indépendance organisationnelle de ces
  identités relèvent du processus externe et ne peuvent pas être prouvés par le
  schéma ;
- labels et tableaux ensemblistes normalisés avant comparaison ;
- empreintes du schéma, de l'entrée, du pack assigné, du pack complété et du cas
  final ;
- clones de contenu sous un nouvel identifiant, doublons globaux et régression
  d'un manifeste déclaré `ready` refusés ;
- bootstrap présent validé sémantiquement ; son absence reste un état valide et
  non prêt, jamais une preuve de lancement ;
- écritures atomiques et sorties protégées contre l'écrasement d'un artefact
  d'entrée ;
- aucune sortie moteur, prédiction ou gold n'entre dans un pack aveugle.

Les décisions utilisent un contrat d'entrée fermé : requête et langue,
`reference_time` horodaté avec offset, au plus 50 snapshots d'offres, ordre
canonique des `candidate_ids` et inventaire
`evidence[{evidence_ref, source_ref}]`. Chaque offre cite au moins une preuve de
cet inventaire. La langue doit correspondre à la strate, les identifiants
d'offre et de candidat sont uniques, et toute dérive d'ordre ou de provenance
fait échouer le lot. Chaque référence citée par le gold doit exister dans cet
inventaire, puis chaque référence prédite doit être autorisée par le gold. Une
auto-attestation du système ne compte jamais comme preuve.

## Workflow humain

Depuis `filon-backend`, créer un pack séparé par annotateur :

```bash
python -m quality_lab.annotation_workflow prepare \
  --dataset entity_resolution \
  --input ../quality/candidates/entity-resolution.jsonl \
  --output ../quality/annotation-packs/entity-human-a.jsonl \
  --annotator-id human-a
```

L'humain remplit uniquement `annotation.label` et `annotation.confidence`. Les
packs complétés doivent être conservés comme artefacts immuables d'audit. La
fusion publie les accords et les désaccords ensemble ; aucune sortie partielle
n'est laissée si une écriture échoue.

```bash
python -m quality_lab.annotation_workflow merge \
  --dataset entity_resolution \
  --input ../quality/annotation-packs/entity-human-a.jsonl \
  --input ../quality/annotation-packs/entity-human-b.jsonl \
  --output ../quality/datasets/entity-resolution.jsonl \
  --disagreements ../quality/adjudication/entity-resolution.jsonl
```

Un merge valide avec désaccords retourne `1`. Les erreurs de contrat, lecture
ou écriture retournent `2`. L'adjudication se fait en deux étapes aveugles :

```bash
python -m quality_lab.annotation_workflow prepare-adjudication \
  --dataset entity_resolution \
  --input ../quality/adjudication/entity-resolution.jsonl \
  --output ../quality/adjudication/entity-third-human.jsonl \
  --adjudicator-id human-c

python -m quality_lab.annotation_workflow adjudicate \
  --dataset entity_resolution \
  --disagreements ../quality/adjudication/entity-resolution.jsonl \
  --input ../quality/adjudication/entity-third-human.jsonl \
  --output ../quality/datasets/entity-resolution-adjudicated.jsonl
```

## Readiness et scorecard

```bash
python -m quality_lab.evaluate --manifest ../quality/manifest.json
python -m quality_lab.evaluate --manifest ../quality/manifest.json --strict
python -m quality_lab.evaluate \
  --manifest ../quality/manifest.json \
  --run ../quality/runs/example/run.json \
  --output ../quality/reports/example-scorecard.json
```

Le runner applicatif produit un run aveugle et immuable depuis le holdout :

```bash
python -m quality_lab.runner \
  --manifest ../quality/manifest.json \
  --output-dir ../quality/runs/git-<sha> \
  --system-version git:<sha>
```

Il retire les golds, annotations, identifiants de cas et strates avant chaque
appel moteur, puis publie transactionnellement sept JSONL et
`run-manifest.json`. Le renommage natif atomique refuse une destination déjà
présente, y compris si un producteur non coopératif la crée pendant la
publication. L'identité `run_id` engage la version système, la version
de l'évaluateur, le digest du manifeste gold, toutes les prédictions et la
provenance `{engine_id, engine_version}` de chaque adaptateur. Le scorecard
recalcule cette identité : modifier une sortie ou sa provenance sans produire
un nouveau run rend l'artefact invalide.

Les cinq adaptateurs intégrés actuellement sont Taxonomy/Product Role, Entity
Resolution par EAN, Offer Truth Awin, Retrieval catalogue et Decision général.
Decision rejoue `resolve_intent` puis `compose_general_plan` à
`reference_time` fixe ; une recommandation expose uniquement des claims
`selected_candidate:<candidate_id>` reliés aux preuves de l'offre sélectionnée,
et la confiance reste explicitement non calibrée à `0.0`. Variant Resolution et
Offer Attachment n'ont pas encore d'interface moteur compatible avec leur
contrat v0.5. Un seul cas sélectionné sur l'un de ces deux jeux fait donc
échouer le runner ; aucun gold n'est recopié et aucune prédiction de
remplacement n'est inventée. Pour Retrieval, les identifiants retournés
appartiennent explicitement aux espaces `ean:<GTIN>` ou `offer:<id>`.

Le manifeste de run engage le digest exact du manifeste gold et de chacun des
sept fichiers de prédictions. Le scorecard joint exactement les `case_id` du
holdout, refuse doublons, absences, extras, mauvaises empreintes et métriques
partielles. Son `holdout_fingerprint` engage le contenu validé des sept golds
test — entrées, labels, annotations et provenance — sans dépendre de l'ordre
des JSONL ni de la version système. Codes de sortie : `0` pass, `1` fail
mesurable, `2` non mesurable ou artefact invalide.

Deux scorecards réelles et mesurables se comparent avec :

```bash
python -m quality_lab.regression \
  --baseline ../quality/reports/baseline-scorecard.json \
  --candidate ../quality/reports/candidate-scorecard.json \
  --output ../quality/reports/regression.json
```

La comparaison exige deux runs distincts, le même contenu de holdout, le même
évaluateur, les mêmes empreintes gold/manifeste, exactement les sept
adaptateurs canoniques et les 27 gates canoniques. Les versions de
moteurs peuvent changer et restent visibles. Un candidat `fail` rend la
régression bloquante ; une scorecard absente, non mesurable, corrompue ou
incompatible produit `not_measurable`, jamais un faux vert. Codes de sortie :
`0` sans régression bloquante, `1` candidat mesurable en échec, `2` comparaison
non mesurable ou invalide. Aucun rapport comparatif réel n'est publié tant que
le holdout humain reste vide.

Pour la readiness seule, `integrity_valid` distingue la validité de l'artefact
de son volume. Sans `--strict`, une entrée intègre mais encore sous-volume rend
`0`, tandis qu'une invalidité rend toujours `2`. Avec `--strict`, les sorties
sont `0` pour `ready`, `1` pour un état intègre mais `not_ready`, et `2` pour une
invalidité. La CI publie toujours le rapport non strict et bloque toute
corruption. Elle exécute en plus la readiness stricte lorsque le moteur, ses
contrats ou ses surfaces de décision changent : les sept datasets vides ne
peuvent donc jamais devenir une gate de lancement verte par omission.

Le golden catalogue historique reste un `bootstrap` de régression : il n'est
ni indépendant ni éligible au gate de lancement.
