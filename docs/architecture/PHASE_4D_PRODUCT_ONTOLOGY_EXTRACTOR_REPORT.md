# FILON — Phase 4D Product Ontology Extractor Report

- Date : **1er septembre 2026**
- Statut : **PASS LOCAL — SHADOW UNIQUEMENT**
- Extracteur : `product-ontology-extractor/v1`
- Policy : `product-ontology-policy/v1`
- Benchmark : `product-ontology-benchmark-manifest/v1`, version `1.1.0`
- Limitation : **NO_EXTERNAL_HUMAN_GROUND_TRUTH**

## Verdict

P4D livre un extracteur déterministe et fail-closed. Il ne transforme plus un
bien physique ambigu en `PRIMARY_PRODUCT`, ne promeut jamais une cible de
relation textuelle en Variant canonique et conserve les catégories legacy
comme signaux de migration, non comme vérité centrale.

L'extracteur passe toutes les gates du holdout v1.1 : 18 442 cas, zéro mismatch
de rôle, zéro mismatch de relation et zéro échec bloquant. Ce résultat autorise
la préparation du writer shadow P4E ; il n'autorise aucun lecteur public.

## Comportements qualifiés

- neuf rôles fermés, avec `UNKNOWN` sans preuve positive ;
- `ACCOMMODATION`, `DIGITAL_CONTENT` et `SERVICE` distincts lorsqu'un champ
  structuré l'établit ;
- `PRIMARY_PRODUCT` seulement avec un objet vendu explicitement nommé et sans
  relation accessoire contradictoire ;
- accessoire, pièce, consommable et bundle issus de lexèmes explicites ;
- cible de compatibilité conservée `observed_text` ;
- concepts catégorie, sous-catégorie et type versionnés ;
- attributs simples typés et unités bornées ;
- huit familles de facettes présentes, les valeurs absentes restant vides ;
- chaque assertion connue conserve raw, source, observation, champ,
  transformation, version et force de preuve.

## Benchmark extracteur v1.1

| Mesure | Résultat |
|---|---:|
| Cas totaux | 18 442 |
| Rôles connus corrects | 4 615 / 4 615 |
| Borne basse Wilson rôle connu | 99,9168 % |
| Abstentions unknown | 4 609 / 4 609 |
| Borne basse Wilson abstention | 99,9167 % |
| Faux `PRIMARY_PRODUCT` | 0 / 4 609 |
| Borne haute Wilson faux principal | 0,0833 % |
| Fausses relations canoniques | 0 / 4 609 |
| Borne haute Wilson fausse relation | 0,0833 % |
| Mismatches de rôle / relation | 0 / 0 |
| Promotion shadow éligible | `true` |

Identité d'évaluation extracteur :
`sha256:d68c43dad0d642b8c52a07219fc59be51a3924ebf1f3934355630be40ddc1c24`.

Empreinte du corpus commun :
`sha256:af5e5dfd208dd8eb690063364bfd059c078ece74fdb6820d8f1826a4e1588735`.

Empreinte des régressions :
`sha256:66d3546dc03bf714fa43f822af8ec4191345f123d4a941aa8306f1f9281bad18`.

## Régression legacy

Sur le même corpus, le moteur `product-role-v1` reste `UNSAFE` : 3 841 faux
`PRIMARY_PRODUCT`, 5 378 mismatches de rôle et une exactitude de 83,34 % sur
les rôles connus. L'extracteur P4D ne remplace donc pas encore le moteur public ;
il constitue un shadow candidat explicitement plus strict.

## Limites et prochaine gate

Le holdout est déterministe et sans ground truth humaine externe. Ses surfaces
v1.1 ont été corrigées avant qualification finale parce que certains positifs
v1.0 ne nommaient pas l'objet vendu ; l'erratum et les anciennes empreintes
sont conservés dans le rapport P4C.

P4E doit maintenant ajouter une persistance expand-only, append-only et
désactivée par défaut. P4F devra ensuite comparer ces résultats à un lot réel
borné avant toute promotion.
