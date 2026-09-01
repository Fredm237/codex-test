# FILON — Phase 4C Product Ontology Benchmark

- Date : **1er septembre 2026**
- Statut du benchmark : **RATIFIED**
- Version : **1.1.0**
- Promotion de l'oracle : **INTERDITE**
- Adaptateur legacy : **UNSAFE / NON PROMOUVABLE**
- Limitation : **NO_EXTERNAL_HUMAN_GROUND_TRUTH**

## Corpus ratifié

Le holdout déterministe contient 18 442 cas sur six verticales : smartphones,
mode, pneus, électroménager/HVAC, hébergement et contenu numérique. Il couvre
les neuf rôles fermés du contrat et sépare quatre strates statistiques :

- rôle connu ;
- négatif `PRIMARY_PRODUCT` sans objet vendu positivement identifié ;
- surface inconnue exigeant l'abstention ;
- relation textuelle observée sans cible canonique.

Chaque strate générée possède au moins 4 609 cas. Le générateur utilise quatre
seeds, n'accepte aucune sortie du moteur en développement et lie l'identité de
l'évaluation au manifeste, au corpus et aux régressions.

## Erratum transparent v1.0 → v1.1

La première version locale du corpus contenait des positifs
`PRIMARY_PRODUCT` dont le titre ne nommait pas toujours l'objet vendu. Ce défaut
de surface a été découvert pendant le développement de P4D. La version 1.0 a
donc été retirée avant publication de l'extracteur, sans réutiliser ses
résultats comme preuve de promotion.

La version 1.1 ajoute un quatrième seed et corrige uniquement ces surfaces pour
nommer explicitement l'objet positif. Elle conserve les négatifs, unknowns,
relations observées, seuils et interdiction de lire l'oracle attendu. Les
identifiants v1.0 suivants restent consignés comme **superseded** : oracle
`sha256:70596999…97090`, legacy `sha256:8e026734…db62`, corpus
`sha256:61446a6d…12fc`.

## Gates

| Gate | Seuil |
|---|---:|
| Borne basse Wilson exactitude rôle connu | ≥ 99,5 % |
| Borne basse Wilson abstention unknown | ≥ 99,0 % |
| Borne haute Wilson faux `PRIMARY_PRODUCT` | ≤ 0,5 % |
| Borne haute Wilson fausse relation canonique | ≤ 0,5 % |
| Échecs bloquants | 0 |

L'oracle contractuel passe toutes les gates avec zéro mismatch et reste
`promotion_eligible=false` : un oracle n'est pas un extracteur de production.

Identité de l'évaluation oracle :
`sha256:40e0559f326b75db1818160d521851dabf4932e9e62e3fd5c64362fa648d5352`.

Empreinte du corpus :
`sha256:af5e5dfd208dd8eb690063364bfd059c078ece74fdb6820d8f1826a4e1588735`.

## Résultat du moteur legacy

| Mesure | Résultat |
|---|---:|
| Cas totaux | 18 442 |
| Exactitude rôle connu | 83,34 % |
| Borne basse Wilson rôle connu | 82,23 % |
| Faux `PRIMARY_PRODUCT` | 3 841 / 4 609 |
| Taux de faux `PRIMARY_PRODUCT` | 83,34 % |
| Promotions de relation canonique | 0 |
| Mismatches de relation | 0 |

Le moteur legacy conserve correctement les relations comme texte observé, mais
échoue les gates rôle et faux produit principal. Cet échec est attendu : tout
bien physique sans signal contraire devient actuellement `main_product`, et
l'hébergement est aplati en `service`.

L'identité de cette évaluation legacy est
`sha256:12aa53c26782e7efbceb741fb421fd1993b74712692e2fe7defa64eef4128acc`.

## Décision

P4C est terminée localement. P4D doit fournir un extracteur fail-closed qui
atteint ces gates sans lire l'oracle attendu. Aucun writer, lecteur public ou
replay production n'est autorisé par ce résultat.
