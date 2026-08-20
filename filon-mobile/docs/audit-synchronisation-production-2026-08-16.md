# Synchronisation FILON mobile — production du 16 août 2026

## Constats vérifiés

Le catalogue de production expose désormais des sections `highlights`, un flux `relief`, un indicateur `pulse`, des produits regroupés par EAN et des filtres marchands, marques, prix et tri. Les 1 593 612 offres, 476 283 produits et 91 263 produits multi-marchands publiés par `/api/catalog/stats` sont des chiffres réels de l’instant observé, pas des valeurs à intégrer en dur dans l’interface.

Le `pulse` de production confirme que l’état de fraîcheur ne doit pas être déduit du seul cache mobile : au relevé, le catalogue signalait une synchronisation en cours, aucun relevé ni baisse sur 24 heures et un dernier relevé datant d’environ 48 heures. L’application doit donc exposer ce statut source avec prudence.

Le flux `relief` apporte une information exploitable : prix courant, haut et bas observés, durée et nombre de relevés, ainsi qu’un niveau de confiance. À présenter exclusivement comme une observation de prix, jamais comme une prévision ou une recommandation universelle.

## Écarts à traiter maintenant

1. Le mobile charge actuellement 80 marchands alors que l’API en publie 230. Les suggestions de filtre doivent couvrir l’ensemble borné par le contrat.
2. Le signal « Actualisation automatique » affiché dans Catalogue décrit le cycle de requêtes local, non la fraîcheur effective de la source. Il doit être remplacé par un statut issu de `pulse`.
3. Les écrans Catalogue ne consomment pas encore `relief`. Une section courte, masquée sans données fiables, peut rendre l’expérience plus vivante sans inventer de verdict.

## Capacités volontairement non promises

Les promesses web de « vrai prix » et de « acheter ou attendre » ne correspondent pas à une route publique dédiée dans le contrat actuel. Le mobile conserve donc des faits observables : disponibilité, historique, prix et état de synchronisation.
