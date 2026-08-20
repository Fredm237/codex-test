# FILON Intelligence Layer — matrice de couverture V2

> Audit local de l’implémentation existante, réalisé à partir de la spécification maître V2 fournie. Ce document sépare les capacités effectivement livrées des extensions qui restent à construire ; il ne décrit aucun prix, stock ou attribut marchand non vérifié.

## Invariants déjà respectés

| Exigence V2 | État | Réalisation observée |
|---|---|---|
| Extension additive, indépendante et désactivable | Couvert | Modules isolés dans `lib/`, entrée Outfit Studio et trois feature flags. |
| Core FILON préservé | Couvert | La couche consomme les offres et les parcours existants sans modifier le catalogue, les prix, les marchands ni l’affiliation. |
| Données locales et réversibles | Couvert pour les préférences, dressing, journal, Lookbook et planificateur | Persistance AsyncStorage bornée et actions de retrait ; Recreate reste le seul appel serveur demandé. |
| Véracité et abstention | Couvert | Les propositions ne prennent que des offres disponibles avec lien partenaire sûr ; le moteur s’abstient lorsque les preuves sont insuffisantes. |
| Neutralité commerciale | Couvert pour le score actuel | L’explication de score exclut explicitement la commission. |

## Fashion Expert et Outfit Studio

| Domaine V2 | État | Couverture actuelle | Écart prioritaire |
|---|---|---|---|
| Intention et contraintes | Partiel | Brief, occasion, saison, budget, style déclaré et pièce possédée. | Ajouter préférences négatives, couleurs, formalité et tolérances sans alourdir le brief. |
| Style DNA | Partiel | Préférence déclarée, répétition, récence, Discover. | Étendre aux couleurs, formalité, silhouettes et préférences de logos avec provenance de chaque signal. |
| Fashion reasoning | Partiel | Rôles, relations, contexte et saison déclarés. | Évaluer explicitement couleur, matière, proportion, silhouette et formalité lorsque la preuve catalogue existe. |
| Composition | Couvert pour le MVP | Base, structure, chaussures, accessoires et Complete autour d’une pièce possédée. | Ajouter une stratégie `Statement` sans dégrader les stratégies Safe et Signature. |
| Critique | Partiel | Détection de lacunes de structure/accessoire, contexte, saison et relations. | Ajouter des codes non spéculatifs pour conflits de contexte, budget et qualité de preuve. |
| Scores | Partiel | Style Score et Confidence Score séparés, reproductibles et expliqués. | Décomposer les sous-scores et rendre les pondérations contextuelles auditables. |
| Modes | Partiel | Create, Complete, Recreate, Discover, comparaison Safe/Signature. | Ajouter Optimize et un mode Compare explicite pour deux tenues sauvegardées. |
| Image/Recreate | Partiel | Observations certain/probable/inconnu, limites et image locale. | Relier les observations à une composition globale sans déduire marque, prix ni disponibilité. |
| Budget et panier | Partiel | Total observé, budget déclaré, restant et proximité de limite. | Conserver l’état « inconnu » pour livraison, cashback et promotions ; aucune optimisation panier n’est encore fournie. |

## Contrats de connaissance et gouvernance

| Domaine V2 | État | Couverture actuelle | Écart prioritaire |
|---|---|---|---|
| Product Intelligence parallèle | Partiel | Rôle de tenue inféré à partir du nom et de la catégorie, sans mutation d’offre. | Créer un contrat générique d’attribut avec valeur, source, confiance et date. |
| Provenance et confiance | Partiel | Provenance sur pièces et relations ; niveaux high/medium/low. | Uniformiser provenance, niveau de preuve et date de calcul pour chaque attribut et décision. |
| Knowledge Graph | Partiel | `COMPLEMENTS`, `RECOMMENDED_WITH`, `SUITABLE_FOR`, `SUITABLE_IN_SEASON`. | Étendre le vocabulaire de relation demandé et stocker score, justification et date. |
| Domain Expert Contract | Non couvert | Fashion possède ses propres types. | Formaliser un contrat réutilisable pour Fashion puis Home, Tech et les domaines futurs. |
| Observabilité | Partiel | Trace d’intention, offres examinées, éligibles et écartées ; registre de décision. | Ajouter une trace de classement, sous-scores et version de règles, toujours locale. |
| Benchmark | Non couvert | Tests unitaires par modules. | Définir des cas Fashion de référence, attendus et versionnés. |
| Taxonomie d’erreurs | Non couvert | Avertissements de critique limités. | Créer les codes d’erreurs V2, leur sévérité et la capture locale d’une correction. |
| Human-in-the-loop | Non couvert | Feedback utile/à revoir. | Permettre la correction structurée d’une recommandation, sans modifier silencieusement le catalogue. |
| Data-quality loop | Non couvert | Aucune file de signalement structurée. | Créer des candidats de correction locaux, explicitement séparés du Core. |
| Métriques et performance | Partiel | Limites de conservation, requêtes limitées et tests. | Mesurer localement les résultats de recommandation et définir des budgets de calcul. |

## Ordre d’implémentation retenu

La suite privilégie les fondations qui rendent chaque extension future plus sûre : **contrats de domaine/provenance**, **relations et sous-scores explicables**, **Optimize et Statement**, puis **benchmark, taxonomie d’erreurs et correction structurée**. Les fonctions commerciales non vérifiables — livraison, cashback, promotion ou panier — ne seront jamais inventées : elles resteront explicitement inconnues tant que le Core n’expose pas une donnée confirmée.
