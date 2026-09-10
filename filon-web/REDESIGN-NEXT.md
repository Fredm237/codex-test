# FILON NEXT — refonte immersive

Branche de revue : `redesign/filon-front-end-2026`.

## Direction

Une identité originale graphite / chrome / vert électrique. Le monogramme FILON est une géométrie extrudée calculée en temps réel. Le monde WebGL est monté dans le layout partagé et change de composition entre cinq familles de routes : accueil, catalogue, assistant, produit et contenu éditorial.

Le monde réagit au pointeur et au défilement. Les commandes « Changer de vue » et pause sont accessibles au clavier. Le dock donne accès aux principales destinations. Les cartes possèdent une profondeur réactive au pointeur. La navigation interne principale conserve le contexte 3D.

## Périmètre implémenté

- Nouvel accueil : recherche, départements réels, offres réelles, méthode et guides.
- Nouveau logo, navigation desktop, menu mobile natif dialog, pied de page et dock.
- Nouvelle palette et nouvelle couche de présentation remplaçant les anciennes surcharges de `filon.css`.
- Catalogue, rayons, cartes, filtres, pagination, assistant et dossiers produits réhabillés dans le même système.
- Nouvelle présentation des pages de contenu utilisant ContentHero.
- Projection spatiale de la photographie produit lorsqu'une texture autorisée et une comparaison qualifiée existent. Il s'agit d'une photo sur un support 3D, pas d'un modèle 360° du produit.
- Dépendances et API métier conservées. Aucune offre, note ou économie inventée.

## Limites assumées

- Les contenus éditoriaux et juridiques existants sont conservés.
- Les anciens fichiers expérimentaux restent dans le dépôt, mais l'accueil et le layout public utilisent le nouveau monde.
- Les formulaires GET restent fonctionnels sans JavaScript ; leur soumission native peut recharger le document.
- Sans WebGL ou en économie de données : repli typographique, parcours HTML conservé. En mouvement réduit : scène statique. Les pages ne dépendent pas de la 3D pour leurs liens ou leurs prix.
- Aucun contrôle visuel dans un navigateur ni mesure FPS sur appareil physique n'a été effectué. La fluidité GPU, les débordements réels et l'acceptation artistique doivent être validés sur desktop et mobile avant fusion.

## Vérification exécutée

- `npm run typecheck` : réussi.
- `npm run build` : réussi, génération des pages et compilation de la 3D incluses.
- `node scripts/test-contract-v1.mjs` : réussi.
- `node scripts/test-product-truth.mjs` : réussi. Les assertions économiques sont conservées ; les assertions de présentation ont été adaptées au remplacement du volume et du header.
- `node scripts/test-truth-claims.mjs` : réussi.
- Le build avertit que certains fragments du sitemap dépassent 2 Mo et ne peuvent être mis dans le cache Next. Le build termine ; ce mécanisme n'a pas été modifié.
- La suite globale `npm test` n'est pas déclarée verte. Plusieurs scripts historiques décrivent explicitement l'ancienne mise en scène et n'ont pas été migrés dans ce mandat.

## Livraison

Cette branche est destinée à une revue et une prévisualisation. Elle ne modifie pas la branche de production et ne prétend pas avoir été déployée.
