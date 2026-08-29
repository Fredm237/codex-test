# FILON — rapport de phase P0.c Quality Lab

Mesure de contrôle : 29 août 2026
Références historiques : scorecard `5ee87f2`, intégrité CLI/CI `45e7768`,
vérité offre `f5ae21b`. Quality Lab v0.5, runner et provenance : `6e12386`,
mesurés le 29 août 2026.

## Phase et statut

**P0.c — infrastructure locale v0.5 : verte. Datasets indépendants : EN COURS
/ NO-GO. Product/Variant Graph : toujours bloqué.**

Le contrat v0.5 sait préparer, fusionner, contrôler, exécuter aveuglément et
comparer deux mesures d'un holdout humain indépendant. Les sept fichiers gold
sont encore absents : le manifeste déclaré
reste `bootstrap_not_ready` et la readiness calculée vaut
`integrity_valid=true`, `ready=false`, `status=not_ready`. L'infrastructure est
intègre, mais aucun score produit n'est publiable.

## Architecture livrée

- un manifeste versionné ferme le roster à exactement sept datasets :
  `taxonomy`, `entity_resolution`, `variant_resolution`, `offer_attachment`,
  `offer_truth`, `retrieval` et `decision` ;
- dix JSON Schemas Draft 2020-12 couvrent les sept golds, le manifeste, le run
  et les prédictions ;
- un split déterministe par `group_id` empêche le même groupe déclaré de
  traverser train/dev/test ; l'intégrité du regroupement famille → `group_id`
  doit être assurée lors de la constitution humaine du holdout ;
- les packs aveugles n'exposent que les champs autorisés et retirent
  récursivement gold labels, annotations et sorties moteur ;
- deux `annotator_id` distincts et des labels structurés concordants sont
  requis ; le schéma ne prouve ni l'humanité ni l'indépendance
  organisationnelle, qui doivent être garanties et auditées par le processus
  externe ;
- tout désaccord part en adjudication et n'est jamais promu automatiquement ;
- les empreintes des packs complétés engagent les annotations exactes et sont
  conservées dans chaque gold final sous `source_pack_fingerprints` ;
- Decision reçoit un inventaire aveugle `evidence_ref` → `source_ref` ; les
  claims gold et prédits doivent citer cette provenance, sans auto-attestation ;
- la readiness détecte contrats incohérents, doublons, fuites de split,
  duplication d'entrée aveugle, altération d'empreinte, bootstrap invalide et
  supports de mesure insuffisants ;
- le runner retire récursivement gold, annotations, strates et identifiants
  avant chaque appel moteur. Il branche les moteurs applicatifs réels de
  taxonomie/rôle produit, EAN, projection Awin, recherche catalogue et décision
  générale ; la requête Decision est fermée, son horloge est figée et ses
  claims de sélection réutilisent uniquement les preuves inventoriées. Les deux
  surfaces sans interface compatible (`variant_resolution`,
  `offer_attachment`) échouent fermé au premier cas non vide ;
- l'identité canonique du run engage la version système, l'évaluateur, le
  manifeste gold, le roster/version des adaptateurs et le contenu exact des
  sept sorties. La publication est transactionnelle, atomique et
  `NOREPLACE`, y compris face à un producteur concurrent non coopératif ;
- le scorecard joint exactement le holdout aux sept fichiers de prédictions,
  recalcule l'identité du run, vérifie tous les digests et refuse toute métrique
  partielle. Son `holdout_fingerprint` engage le contenu exact des cas test,
  labels et annotations, sans dépendre de l'ordre des JSONL ni du `run_id` ;
- les métriques couvrent faux merge/split, relation de variante, attachement et
  éligibilité, résolution Retrieval (`matched`, `no_match`, `ambiguous`),
  recall/NDCG et contraintes, sécurité des décisions, couverture sourcée et
  calibration ;
- les 27 gates couvrent en plus taxonomie/rôle produit, vérité prix-stock-
  livraison-affiliation, exact-product top-1, pertinence top-3 binaire,
  résultats absurdes et strates scénario/langue/verticale ;
- un gold ou une prédiction `no_match`/`ambiguous` interdit une liste de
  produits non vide : ces cas sont mesurés et ne peuvent plus disparaître du
  dénominateur de résolution ;
- le comparateur de régression exige exactement les sept datasets, sept
  adaptateurs et 27 gates canoniques. Un holdout modifié, un roster tronqué,
  une provenance incohérente ou une scorecard invalide produit
  `not_measurable`, jamais un faux vert.

## Contrat de mesure

| Dataset | Minimum total | Minimum test | Supports scorables principaux |
|---|---:|---:|---|
| Taxonomy | 1 000 | 500 | 500 cas |
| Entity Resolution | 2 000 | 1 000 | 800 `different`, 200 `same`, 200 relations de variante |
| Variant Resolution | 500 | 200 | 200 cas |
| Offer Attachment | 1 000 | 500 | 500 offres, dont 200 éligibles et 200 non éligibles |
| Offer Truth | 1 000 | 500 | 500 faits offre |
| Retrieval | 3 000 | 1 300 | 475 répondables, 300 exact-product, 600 `no_match`, 225 ambiguës |
| Decision | 500 | 500 | 500 décisions, dont 381 non-abstentionnistes |

La calibration exige 1 000 observations. Les gates binomiaux de taux/accuracy
et la couverture sourcée sont évalués sur la borne prudente de l'intervalle de
Wilson à 95 % : borne haute pour les taux d'erreur, borne basse pour les
accuracies et la couverture. `recall@50` et `NDCG@10` utilisent désormais la
borne basse d'une borne empirique de Bernstein à 95 % sur les scores par
requête. `ECE` utilise la borne haute d'un bootstrap percentile déterministe à
2 000 rééchantillonnages. La gate top-3 mesure un hit binaire par requête ; la
precision@3 reste descriptive. La gate `absurd_result_rate` est strictement
inférieure à 1 %. Les compteurs de fausse éligibilité, violations de contraintes
et claims non supportés gardent une tolérance nulle.

## Preuves

- suites ciblées du workflow humain, des schémas, de la readiness, des
  métriques, du scorecard, du runner, de la provenance et de la régression
  v0.5 : **359/359** ;
- suite Quality sans dépendance réseau : **257 réussis** sur le collecteur,
  l'intégrité, les schémas et la scorecard ;
- suite backend complète courante sous Python 3.12 et les dépendances déclarées :
  **2 035 réussis, 1 ignoré** en 109,18 s ;
- archive propre du HEAD `a78401a`, qui contient le lot Quality `6e12386`,
  suite backend complète : **1 907 réussis, 1 ignoré**, 7 avertissements
  `datetime.utcnow()` historiques, en **370,53 s** ;
- le golden bootstrap historique reste explicitement non indépendant et non
  éligible au lancement ;
- rapport de readiness référencé :
  [`quality/reports/readiness-2026-08-29.json`](../../quality/reports/readiness-2026-08-29.json) ;
- l'état réel du rapport est `integrity_valid=true`, `ready=false`,
  `status=not_ready`, fingerprint
  `sha256:e949de01a819a5b5ef4fb0b53b5efd15241bc514b71831d32c7b1146b491262f`,
  avec **0 cas humain** sur les sept jeux ;
- un run incomplet, incohérent ou sous-support reste `not_measurable`, jamais
  partiellement « pass ».
- un collecteur d'inventaire réel, borné et immuable ajoute **15 tests ciblés
  verts** ; son vérificateur recalcule chaque empreinte, refuse les champs
  moteur ajoutés, les sources non canoniques, les comptes altérés, les
  doublons inter-strates et toute curation préremplie.

## Contrat CLI et CI

Le commit `45e7768` sépare l'intégrité du gate de lancement :

| Situation | Mode CLI | Code de sortie |
|---|---|---:|
| Rapport intègre et `ready=true` | normal ou `--strict` | 0 |
| Rapport intègre et `ready=false` | normal | 0 |
| Rapport intègre et `ready=false` | `--strict` | 1 |
| Manifeste, schéma, dataset, empreinte, invariant ou bootstrap invalide | normal ou `--strict` | 2 |

Le workflow emploie le mode normal pour produire le rapport, puis le mode
strict pour fermer la promotion. GitHub Actions #343 a publié l'artefact
`quality-readiness-e04dfc2c18ef58177d4182acbb67c966058ff9c0`, conservé 14
jours. Les quatre jobs sont requis sur `main` par la ruleset `21798272`. Le job
backend reste volontairement rouge sur le code 1 tant que les cas humains sont
absents ; une invalidité technique sortirait avec le code 2.

## Inventaire réel initial

Le 29 août 2026, une première collecte publique a figé **1 000 observations** :
200 par filtre d'échantillonnage `appliances`, `headphones_audio`, `laptops`,
`smartphones` et `tv`. Le JSONL et son reçu sont publiés sous
[`quality/candidates`](../../quality/candidates/README.md), avec l'empreinte
d'inventaire
`sha256:dee650b3140755022b37890f74f4d1fc61e1265f22b3621366c44462cb9131c8`.

Le lot ne contient aucun label et reste `ready_for_annotation=false`. Prix,
devise, stock, fraîcheur, type d'offre, catégorie/sous-catégorie FILON, image et
lien affilié sont exclus. Le contrôle du contenu a révélé des catégories source
incompatibles avec certains filtres FILON ; `sampling_vertical` n'est donc
jamais copié dans `curation.vertical`. Cette anomalie réelle confirme que la
curation humaine est une condition de vérité, pas une formalité.

## État des données

| Dataset | Cas indépendants présents | Statut |
|---|---:|---|
| Taxonomy | 0 | NO-GO |
| Entity Resolution | 0 | NO-GO |
| Variant Resolution | 0 | NO-GO |
| Offer Attachment | 0 | NO-GO |
| Offer Truth | 0 | NO-GO |
| Retrieval | 0 | NO-GO |
| Decision | 0 | NO-GO |

Ces zéros expliquent le NO-GO sans invalider l'intégrité du laboratoire. Le
moteur, un LLM ou cet agent ne peuvent pas se substituer aux annotateurs
indépendants.

## Procédure de collecte

1. Extraire des cas réels bornés et sans donnée personnelle dans
   `quality/candidates/`. Un premier inventaire catalogue de 1 000 lignes est
   acquis ; il doit encore être curé et complété par des requêtes réelles
   anonymisées pour Retrieval/Decision.
2. Pour Decision, joindre l'inventaire de provenance autorisé à chaque entrée.
3. Générer un pack aveugle distinct pour chaque annotateur.
4. Faire annoter sans sortie moteur visible et conserver les packs complétés
   comme artefacts immuables.
5. Fusionner atomiquement les accords et envoyer les divergences en
   adjudication humaine.
6. Relancer d'abord la readiness normale pour distinguer toute invalidité
   (exit 2), puis la readiness stricte ; elle vérifie volumes, strates, splits,
   empreintes, invariants de labels et absence de fuite.
7. Exécuter les sept adaptateurs applicatifs sur l'entrée aveugle, figer le
   manifeste du run et les sept digests de prédictions, puis produire le
   scorecard fail-closed.
8. Comparer baseline/candidat uniquement si l'empreinte du holdout et le contrat
   canonique complet sont identiques.

## Next gate

Obtenir les sept jeux humains aux volumes et supports minimaux, avec provenance
Decision, double annotation réellement indépendante, adjudications tracées et
holdout figé. Brancher ensuite des interfaces applicatives réelles pour les
deux datasets encore volontairement refusés par le runner. P0.c reste
`en_cours` et P0.f reste NO-GO jusqu'à deux scorecards mesurables sur le même
holdout et une comparaison conforme aux 27 gates.
