# Jeux annotés du Quality Lab v0.5

Ce dossier n'embarque aucune annotation synthétique. Son roster est fermé à
exactement sept fichiers :

| Dataset | Fichier | Contrat gold principal |
|---|---|---|
| Taxonomy | `taxonomy.jsonl` | catégorie, sous-catégorie et rôle produit exacts |
| Entity Resolution | `entity-resolution.jsonl` | relation produit et relation de variante cohérentes |
| Variant Resolution | `variant-resolution.jsonl` | variante résolue avec clé, ou clé nulle si ambiguë/inconnue |
| Offer Attachment | `offer-attachment.jsonl` | éligibilité et rattachement de variante cohérents |
| Offer Truth | `offer-truth.jsonl` | prix, stock, livraison et lien affilié observés |
| Retrieval | `retrieval.jsonl` | produits pertinents, équivalents exacts fermés et produits violant les contraintes |
| Decision | `decision.jsonl` | issues acceptables, claims interdits et claims reliés à des preuves |

Chaque ligne finale respecte le schéma v0.5 déclaré dans `../manifest.json`, le
split canonique dérivé de `group_id` et les empreintes du schéma, de l'entrée et
du cas. Aucun huitième dataset ni payload brut contenant une donnée personnelle
ou un secret marchand ne doit être ajouté au dépôt.

Chaque entrée contient aussi une strate fermée : un des dix types de scénario,
une langue parmi FR/NL/EN et une des cinq verticales prioritaires. Ces champs
sont obligatoires dès le pack aveugle. Leurs supports de couverture sont comptés
sur le holdout Retrieval validé, jamais sur les autres jeux ni sur de simples
candidats.

Pour Decision, l'entrée aveugle inventorie explicitement
`evidence[{evidence_ref, source_ref}]` et fournit une requête fermée avec
`query`, `locale`, `reference_time` et les snapshots d'offres candidats. La
langue correspond à la strate ; `candidate_ids` répète exactement l'ordre des
offres ; chaque offre a un identifiant unique et cite au moins une preuve
inventoriée. `reference_time` doit inclure un offset et fige le contrôle de
fraîcheur du benchmark. Un gold `recommend` ou `wait` contient au moins un
`claim_evidence`, dont chaque référence doit appartenir à cet inventaire. Cette
provenance empêche une prédiction de se déclarer elle-même « sourcée ».

## Origine et intégrité

Les datasets finaux ne sont jamais édités à partir d'une sortie moteur. Ils sont
produits par `quality_lab.annotation_workflow` après deux annotations humaines
aveugles concordantes ou une adjudication documentée par un troisième humain
distinct.

Les deux `source_pack_fingerprints` d'un cas final sont les empreintes des packs
**complétés** : elles engagent le contenu exact remis par chaque annotateur,
annotations comprises, et pas seulement l'affectation initiale. Toute
divergence de contenu, empreinte, schéma, split ou identité fait échouer le lot
sans publication partielle.

## Holdout mesurable

La présence des fichiers ne suffit pas. Le holdout test doit atteindre les
supports déclarés dans le manifeste : 800 paires Entity `different`, 200
`same`, 200 relations de variante, 500 cas Taxonomy, 200 cas Variant, 500 offres
dont 200 éligibles et 200 non éligibles, 500 vérités d'offre et 1 300 requêtes
Retrieval. Ces dernières comprennent au moins 475 cas répondables, dont 300
recherches exactes, 600 `no_match` et 225 cas ambigus. Le holdout exige aussi
500 décisions dont 381 non-abstentionnistes, 1 000 observations de calibration
et les minima explicites par scénario, langue et verticale.

En dessous d'un de ces supports, le scorecard reste `not_measurable`. Les gates
de proportion utilisent les bornes conservatrices de Wilson à 95 % ; 300 cas
exacts rendent le seuil de 98 % en top-1 prouvable avec une erreur, et 600 cas
`no_match` rendent le seuil strict de 1 % de résultats absurdes prouvable avec
une erreur. Chaque recherche exacte répondable fournit un `exact_product_ids`
non vide, sous-ensemble fermé des produits pertinents ; ce tableau est vide
partout ailleurs. Precision@3 reste descriptive, tandis que la gate Top-3 est un
hit-rate binaire avec Wilson. Un bon score ponctuel sur un petit lot n'est donc
jamais une preuve de lancement.
