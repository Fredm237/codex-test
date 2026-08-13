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
