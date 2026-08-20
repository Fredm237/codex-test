# Design mobile — FILON

## Intention

FILON mobile est un **copilote d’achat belge** conçu pour répondre vite à une question concrète : « Est-ce le bon prix, maintenant ? » L’application doit se sentir native, dense sans être encombrée, avec une profondeur visuelle inspirée de la matière brute, de l’encre et d’un ambre précis. Elle ne reproduit pas la narration longue du site : sur téléphone, chaque transition conduit vers une donnée, une comparaison ou une décision vérifiable.

Le design est prévu en portrait 9:16, pour une utilisation à une main. Les actions principales sont dans la moitié basse de l’écran ; les surfaces touchables font au minimum 44 pt ; les gestes ont toujours une alternative visible. L’interface respecte les conventions iOS tout en restant naturelle sur Android : barre d’onglets basse, grandes feuilles modales pour les filtres, navigation native par pile, typographie lisible et retours haptiques discrets.

## Écrans

| Écran | Contenu et fonction | Composition mobile |
|---|---|---|
| Accueil | Recherche immédiate, raccourcis par besoin, repères catalogue et rail de prix observés | Une question en grand, champ de recherche bas, cartes horizontales et signal de fraîcheur. |
| Recherche | Saisie libre, suggestions, résultats vérifiés et filtres | Barre de recherche collante, résultats virtualisés, bouton filtre accessible au pouce. |
| Catalogue | Rayons, sous-catégories, offres et tri | Header compact, chips défilants, grille/liste de cartes avec prix et marchand. |
| Fiche produit | Produit regroupé, prix, offre(s), score et lien marchand | Galerie concise, bloc de verdict factuel, offres classées, CTA au bas de l’écran. |
| Assistant | Conversation avec FILON et cartes catalogue contrôlées | Questions sous forme de chips, flux de réponse progressif, aucune carte inventée. |
| Favoris | Produits sauvegardés localement et état de suivi | Liste épurée, boutons d’alerte et de suppression explicites. |
| Alertes | Création et gestion d’un seuil de prix | Feuille native avec saisie numérique et échéance facultative ; permission push demandée seulement après la création. |
| Profil / réglages | Langue, confidentialité, notifications et informations produit | Liste système claire, sans inscription forcée dans la première version. |

## Parcours clés

Le parcours d’achat principal suit : **Accueil → recherche → résultat → fiche produit → lien marchand**. Le prix affiché est toujours accompagné du marchand et de l’état de fraîcheur connu. Si aucune offre compatible n’est disponible, l’application l’indique au lieu de proposer un substitut non vérifié.

Le parcours assistant suit : **Assistant → question/budget → flux de résultats catalogue → carte produit → fiche**. La locale active FR, NL ou EN accompagne chaque demande. Le téléphone ne synthétise pas de verdict commercial ; il rend uniquement les informations du backend FILON.

Le parcours de rétention suit : **Fiche produit → définir une alerte → seuil → confirmation → permission notifications**. La permission système ne survient donc jamais à l’ouverture de l’application.

## Système visuel

| Token | Valeur | Usage |
|---|---:|---|
| Encre | `#0E0C0B` | Fond principal, profondeur et contraste. |
| Pierre | `#1A1714` | Surfaces élevées, barre d’onglets et feuilles. |
| Ivoire | `#E4DED4` | Texte principal et repères lisibles. |
| Ambre FILON | `#C89544` | Actions primaires, prix signalés et focus. |
| Ambre doux | `#E3B969` | Dégradés très courts, lueurs de focus non décoratives. |
| Feuille | `#8FB072` | Signal positif secondaire uniquement. |
| Alerte | `#E59480` | Information de prix ou état nécessitant attention. |

La géométrie se fonde sur des séparateurs fins, des angles légèrement arrondis (16–24 pt) et une grille strictement alignée. Les animations utilisent majoritairement `opacity` et `transform`, entre 80 et 250 ms : apparition de résultat, déplacement d’une carte vers les favoris, pulse court sur une baisse observée. Les préférences de réduction de mouvement désactivent tout mouvement non fonctionnel.

## Modèles de domaine

| Modèle | Champs essentiels | Source d’autorité |
|---|---|---|
| Offre | id, nom, prix, devise, image, marchand, stock, lien | Backend catalogue FILON |
| Produit | EAN, nom, marque, catégorie, prix min/max, nombre de marchands | Backend catalogue FILON |
| Recherche | requête, budget, filtres, locale, horodatage | Application + backend |
| Favori | identifiant produit/offre, date, note locale | Stockage local avant synchronisation utilisateur |
| Alerte | produit, seuil, état, consentement push | Backend dès l’introduction des comptes |
| Assistant | question, critères, événements SSE, cartes validées | Backend Assistant FILON |

## Principes d’accessibilité et de confiance

Chaque image est décorative ou possède un libellé utile. Les montants sont lisibles par lecteur d’écran ; les couleurs de verdict ne constituent jamais le seul signal. Les cartes proposent un état chargé, vide, indisponible et erreur qui expliquent la situation sans faux chiffre. Les actions externes annoncent le marchand avant d’ouvrir son lien affilié.

## Extension additive — FILON Intelligence Layer

L’extension **FILON Intelligence Layer** ne remplace aucune des surfaces précédentes. Son premier module, **Outfit Studio**, est accessible depuis l’Assistant comme un mode spécialisé. La recherche catalogue, l’affichage des produits, le prix, les marchands, les favoris et l’affiliation conservent leur comportement actuel ; Outfit Studio les consomme pour proposer une tenue uniquement lorsque des offres réelles et exploitables sont disponibles.

| Écran supplémentaire | Contenu et fonction | Composition mobile |
|---|---|---|
| Brief Outfit Studio | Intention, occasion, saison, budget et préférences facultatives | Champ large en haut, choix courts accessibles au pouce, une seule action principale bas d’écran. |
| Proposition de tenue | Résumé du brief, pièces compatibles, total estimé, variantes et explications | Cartes de pièces empilées, score de cohérence explicable et lien vers chaque parcours produit FILON existant. |
| Préférences stylistiques | Style déclaré, palette, formalité et budget | Contrôles simples, persistés localement, réinitialisables et sans effet sur le catalogue source. |

Le parcours principal suit : **Assistant → Outfit Studio → brief minimal → offres vérifiées → proposition → fiche ou marchand**. L’application doit demander seulement les informations indispensables. Lorsque les preuves sont insuffisantes ou les résultats catalogue indisponibles, l’écran signale la limite et permet d’assouplir une contrainte plutôt que de créer une recommandation artificielle.

| Niveau de confiance | Sens | Présentation |
|---|---|---|
| Élevé | Offre, disponibilité ou attribut explicitement constaté | Marqué « vérifié » et utilisable dans une recommandation essentielle. |
| Moyen | Interprétation à partir du nom, de la catégorie ou d’une description connue | Marqué « interprétation FILON » avec une justification concise. |
| Faible | Signal ambigu ou incomplet | Ne peut pas décider seul de l’inclusion d’une pièce essentielle. |
