# FILON — taxonomie d'erreurs produit

Date : 29 août 2026

Version : `contracts/taxonomies/v1`

Statut : **registre canonique livré ; couverture production incomplète**

## Décision

FILON possède un seul registre E001–E018 pour les erreurs de qualité produit.
La valeur complète est le contrat persistant : `E008_WRONG_PRICE`, et non
`E008` seul. Le runtime Python, le catalogue JSON et le JSON Schema doivent
rester strictement identiques ; la suite de compatibilité bloque toute
divergence, duplication ou rupture de continuité.

Cette taxonomie ne remplace pas les codes de santé opérationnelle en minuscules
et n'étend pas le manifeste public gelé `contracts/v1/manifest.json`.

## Catalogue et frontières

| Code | Sens canonique | Frontière importante |
|---|---|---|
| `E001_WRONG_CATEGORY` | catégorie produit incorrecte | classification, pas rôle du produit |
| `E002_WRONG_PRODUCT_ROLE` | produit principal, accessoire, bundle ou pièce mal qualifié | le rôle peut être faux même si la catégorie est juste |
| `E003_FALSE_PRODUCT_MERGE` | produits distincts fusionnés | erreur d'identité entre produits, pas seulement de variante |
| `E004_FALSE_PRODUCT_SPLIT` | même produit scindé en plusieurs identités | E015 vise une duplication de sortie, pas la règle d'identité source |
| `E005_WRONG_VARIANT` | mauvaise variante attachée ou attribuée | le produit peut être juste tandis que taille, couleur ou capacité est fausse |
| `E006_IRRELEVANT_RETRIEVAL` | candidat récupéré non pertinent | la pertinence est distincte d'une contrainte dure |
| `E007_HARD_CONSTRAINT_VIOLATION` | candidat ou résultat viole une contrainte non négociable | budget, pays, sécurité, stock exigé, etc. |
| `E008_WRONG_PRICE` | prix observé faux, invalide ou non positif | un prix ancien est E009 ; un problème de devise est E018 |
| `E009_STALE_PRICE` | prix trop ancien pour l'usage annoncé | la valeur peut avoir été correcte à sa date |
| `E010_WRONG_STOCK` | disponibilité fausse ou source non reconnue | l'inconnu reste inconnu, jamais disponible par défaut |
| `E011_WRONG_SHIPPING` | coût, délai, zone ou condition de livraison faux | l'absence de donnée ne devient jamais livraison gratuite |
| `E012_UNSUPPORTED_CLAIM` | affirmation sans preuve éligible | distinct du registre documentaire C-xxx des formulations publiques à corriger |
| `E013_WRONG_VERDICT` | verdict produit incorrect au regard des faits éligibles | E007 décrit la contrainte violée ; E013 la conclusion rendue |
| `E014_OVERCONFIDENT_DECISION` | confiance annoncée supérieure à la preuve ou à la calibration | peut coexister avec un verdict finalement correct |
| `E015_DUPLICATE_PRODUCT` | même produit présenté plusieurs fois dans une sortie | n'implique pas à lui seul un faux split du graphe |
| `E016_SCHEMA_INVALID` | schéma source ou champ obligatoire invalide | le producteur Awin actuel ne détecte que `aw_product_id`/`product_name` absents ou vides ; un identifiant présent mais mal formé est E017 |
| `E017_INVALID_IDENTIFIER` | identifiant présent mais syntaxiquement ou structurellement invalide | la projection Awin valide notamment longueur et checksum GTIN/EAN |
| `E018_CURRENCY_MISMATCH` | devise inutilisable ou prix sans champ devise exploitable | le nom historique est conservé ; `stage`, `field` et `reason` portent la nuance |

E001 à E015 sont les codes du mandat de gouvernance. E016 à E018 sont des
extensions FILON nécessaires à la validation d'ingestion. Leur conservation
évite de modifier les lignes de quarantaine et les clés d'idempotence déjà
calculées.

## Règles producteur

1. importer `ProductErrorCode` ; aucun littéral Exxx n'est admis ailleurs dans
   le runtime applicatif ;
2. persister `.value` sans renommer ni normaliser le token ;
3. préciser le contexte dans `stage`, `field`, `reason` et, si nécessaire,
   `details`, plutôt que créer une variante orthographique du code ;
4. ajouter un test de preuve lorsqu'un producteur commence à émettre un code ;
5. changer de version de transformation dès qu'une sortie persistée de la
   projection change, y compris `reason` ou `details`. Ces deux champs ne font
   volontairement pas partie de la clé d'incident et un replay append-only ne
   met pas à jour une ancienne ligne. Cela n'autorise jamais à changer le sens
   d'un code dans v1 : une rupture exige une nouvelle version majeure et une
   migration explicite.

Un code inconnu provenant d'une version future doit être conservé brut et
signalé. Il ne doit jamais être converti silencieusement vers le code jugé
« le plus proche ». Le helper `decode_product_error_code()` matérialise cette
règle pour les futurs lecteurs inter-version ; les producteurs restent stricts
et construisent directement un `ProductErrorCode`.

## Couverture réelle et limite de preuve

La projection Awin émet actuellement E008, E010, E016, E017 et E018. Les
treize autres valeurs sont enregistrées mais n'ont pas encore de producteur
opérationnel dans le dépôt. Par conséquent, la phrase « chaque incident produit
de production reçoit un code » reste un objectif de gouvernance, pas un résultat
prouvé.

Pour E018, le producteur Awin actuel vérifie uniquement que le champ devise est
présent et formé de trois lettres. Il ne prouve pas encore l'appartenance au
registre ISO 4217 et ne compare pas une devise éventuellement incluse dans le
texte du prix avec le champ séparé. Une devise de quatre lettres produit deux
preuves distinctes : l'échec direct de `currency_validation/currency` et
l'inéligibilité du prix dans `price_validation/search_price`. Cette multiplicité
est intentionnelle et la clé inclut étape et champ ; elle ne doit pas être
dédupliquée sur le seul code.

Pour E016, la projection Awin n'est pas encore un validateur complet de schéma :
son helper texte convertit les valeurs non-chaînes avant de tester le vide. Le
code prouve donc aujourd'hui seulement l'absence ou le vide des deux champs
obligatoires cités, pas la validité de type de tout le payload. Les futurs
producteurs ne peuvent revendiquer le sens plus large qu'avec un schéma et des
fixtures négatives correspondantes.

Les sondes utilisent notamment `database_probe_failed`, `redis_probe_failed` et
`schema_revision_invalid`. Ces codes concernent l'état du service ; ils restent
hors de `ProductErrorCode`.

Le mobile possède aussi un ancien `FashionErrorCode` avec des noms courts comme
`WRONG_CATEGORY` et `WRONG_PRICE`. Ce vocabulaire local de feedback Fashion est
gelé hors Core en Phase 0. Sans préfixe E ni valeur wire complète, ses membres ne
sont ni des alias, ni des producteurs de la taxonomie canonique.

## Compatibilité démontrée

- E001–E018 sont uniques, ordonnés et contigus dans l'Enum, le registre et le
  schéma ;
- la projection n'émet que l'Enum canonique et la base conserve la chaîne
  historique ;
- la clé d'une quarantaine E008 connue reste bit à bit identique ;
- un contrôle AST refuse tout nouveau littéral Exxx ad hoc dans `app/` ;
- le manifeste public v1 conserve sa politique d'évolution compatible et ne
  référence pas cette taxonomie interne ; son absence de modification est aussi
  contrôlée dans la preuve Git isolée du lot.

## Preuve isolée

- commit exact : `7753dffbd99e378b7dcd287cb13ee1d32e379b39` ;
- worktree détaché propre, Python 3.12.13 ;
- taxonomie, observation et contrats publics v1 : **29 réussis, 0 échec** ;
- suite backend complète : **1 304 réussis, 0 échec** ;
- sept avertissements historiques `datetime.utcnow()`, sans nouveau warning du
  lot ;
- deux relectures indépendantes finales : aucun P0, P1 ou P2 ;
- `contracts/v1` sans diff et aucun fichier utilisateur proté dans le commit.
