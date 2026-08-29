# FILON Product Error Taxonomy v1

Statut : `active`. Périmètre : qualité produit interne.

Ce registre versionne les codes utilisés pour qualifier une erreur de données,
de recherche ou de décision produit. Il est volontairement séparé des
contrats clients publics figés dans `contracts/v1` et des codes opérationnels
des sondes de santé.

## Compatibilité

- la valeur complète, par exemple `E008_WRONG_PRICE`, est la valeur persistée ;
- un identifiant, un nom ou une valeur déjà publiés ne sont ni renommés, ni
  renumérotés, ni réutilisés dans v1 ;
- un consommateur ancien conserve et signale un code inconnu ; il ne le remappe
  jamais silencieusement ;
- un ajout exige au minimum une version mineure et un test du comportement des
  consommateurs face à l'inconnu ;
- le sens est immuable dans v1. Une rupture exige une nouvelle version majeure,
  un nouveau code si nécessaire et une migration explicite des consommateurs et
  des enregistrements existants ; une version de transformation ne suffit pas.

Pour la quarantaine Awin, `reason` et `details` n'entrent volontairement pas
dans la clé d'identité. Toute modification de ces champs persistés exige donc
aussi une nouvelle version de transformation : un replay append-only ne réécrit
pas le texte d'une ligne historique.

Le fichier `product-error-codes.json` porte les métadonnées canoniques et
`product-error-code.schema.json` ferme la liste des valeurs v1 autorisées.
Un producteur construit obligatoirement un `ProductErrorCode`, ce qui refuse une
valeur inventée. Un lecteur inter-version peut utiliser
`decode_product_error_code()` : le résultat indique si la valeur est connue tout
en conservant la chaîne brute sans normalisation.

## Origine et couverture

Les codes E001 à E015 proviennent du mandat de gouvernance produit. E016 à
E018 sont des extensions FILON déjà utilisées par la projection d'observation
Awin ; leur valeur est conservée pour ne casser ni la quarantaine, ni ses clés
d'idempotence.

Le registre ne signifie pas que chaque erreur de production est déjà
classifiée. Au moment de sa création, la projection Awin émet seulement E008,
E010 et E016 à E018. Les treize autres codes sont disponibles pour les futurs
producteurs, qui devront ajouter leurs preuves et leurs tests avant usage.

## Espaces distincts

Les valeurs comme `database_probe_failed`, `redis_probe_failed` et
`schema_revision_invalid` décrivent la santé opérationnelle. Elles ne sont pas
des erreurs de qualité produit et ne doivent pas être converties en codes E.

Le type mobile historique `FashionErrorCode` emploie certains noms courts
semblables, par exemple `WRONG_CATEGORY`. Il reste un vocabulaire local de
feedback Fashion, gelé hors du Core pendant la Phase 0 : ses valeurs sans
préfixe E ne sont ni des alias, ni des valeurs wire de cette taxonomie.
