# Audit de l’expérience immersive — 13 août 2026

## Observation en production

La page d’accueil affichait la navigation, le titre et la recherche, mais la séquence restait sur **« Chargement de l’expérience… »** avec un canvas noir. L’approche précédente attendait que les 271 images soient chargées avant d’activer le rendu. Une image lente ou indisponible bloquait donc l’intégralité de l’expérience.

## Correction déployée

Le composant `ImmersiveExperience.tsx` a été modifié pour :

- activer le rendu dès que la première image est disponible ;
- précharger le reste des images en arrière-plan ;
- afficher la frame la plus proche déjà disponible pendant le chargement ;
- ne jamais bloquer l’interface si une image échoue ;
- écouter proprement le scroll et le redimensionnement sans boucle d’animation permanente.

Commit : `6661a58`.

## Vérification à effectuer

Après le déploiement Vercel, vérifier sur desktop et mobile que l’image initiale apparaît immédiatement puis que la séquence répond au scroll.

## Contrôle responsive à 390 × 844

La capture mobile a confirmé que la première image s’affiche correctement après le correctif progressif : la navigation, l’image, la recherche et l’indicateur de scroll restent dans le viewport sans débordement horizontal.

Un détail a été identifié : le titre du premier chapitre était invisible exactement au chargement car le fondu d’entrée partait d’une opacité nulle à `0 %` du scroll. Le premier chapitre est désormais visible immédiatement ; les chapitres suivants conservent leur fondu d’entrée et de sortie.

Prochaine vérification : déployer ce correctif puis tester l’ouverture et le scroll sur mobile.

## Vérification de production après le commit `66959d7`

Le premier affichage peut rester noir pendant le court instant de téléchargement de la toute première image, mais la seconde vérification, moins de quinze secondes plus tard, confirme que :

- la première scène est rendue correctement sur le canvas ;
- le premier titre est immédiatement lisible dès que l’image apparaît ;
- l’indicateur de scroll remplace bien le message de préparation ;
- la recherche reste visible et dans la zone de clic.

Le prochain axe est de supprimer l’instant noir restant avec une poster image/fallback immédiat et de finaliser le rendu mobile/tablette.

## Vérification du poster — commit `7b17e38`

Le contrôle de production confirme que le poster `/seq/hero/001.jpg` est visible immédiatement dès l’ouverture. La scène, le premier message, la barre de recherche et l’indicateur de défilement apparaissent sans écran noir ni état de chargement bloquant. Le scroll a ensuite été positionné à mi-parcours afin d’inspecter la continuité de la narration.

## Validation de la homepage mobile

La capture finale à 390 × 844 confirme que l’accroche raccourcie tient sur une seule ligne, que le titre conserve deux lignes lisibles, et que les contrôles de langue, menu, recherche et action restent séparés, accessibles et sans débordement. La première scène est nette dès l’ouverture grâce au poster prioritaire.

## Audit de l’assistant — commit `ccc5655`

L’état initial de l’assistant affiche désormais une scène cinématique fiable au lieu d’une vidéo inexistante. Le formulaire, le choix du territoire et les suggestions restent lisibles au-dessus du fond. Une recherche réelle a été lancée pour contrôler les résultats, les libellés de source et les liens d’offre.

## Contrôle de provenance des résultats — commit `bba88cc`

La page Assistant est rechargée après déploiement du garde-fou. Une requête de test est prête à être envoyée afin de confirmer que les résultats provenant de Google Shopping ne sont plus présentés comme des recommandations FILON.

## Contrôle final des estimations — commit `5a5e58b`

Le garde-fou est déployé. Une requête identique à celle qui retournait auparavant des estimations et des marchands externes est préparée afin de vérifier que l’interface affiche désormais un refus transparent plutôt que des recommandations non vérifiées.

## Vérification de l’orientation catalogue — commit `cd429ad`

La recherche de contrôle est prête. Le prochain contrôle doit confirmer qu’en l’absence d’offre partenaire vérifiée, l’assistant propose une exploration du catalogue avec la requête préremplie, et non une relance sans issue.

## Validation — commit `cd429ad`

Le test de production confirme le comportement attendu : les réponses estimées ou externes ne sont plus présentées comme des recommandations FILON. L’interface annonce l’absence d’offre vérifiée et dirige vers `/catalogue/?q=<recherche>`, sans lien Google Shopping.

## Vérification responsive — itération performance `bd254fa`

- **iPhone 390×844** : logo, sélecteur de langue et menu respectent les marges de sécurité ; le titre tient sur deux lignes sans coupe ; le champ de recherche reste entièrement visible et son bouton conserve une cible tactile confortable.
- **Tablette 834×1112** : la scène couvre correctement le viewport ; la hiérarchie logo → promesse → recherche reste équilibrée ; aucun débordement horizontal observé.
- **Constat** : le préchargement progressif conserve une image immédiate via le poster et la scène reste lisible sur les deux formats contrôlés.
