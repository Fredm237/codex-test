# Benchmark mobile 2026 — direction FILON

## Sources étudiées

| Source | Enseignement vérifié | Application FILON |
|---|---|---|
| Apple HIG — Motion | Le mouvement doit signaler un état, fournir un retour ou guider ; il doit rester bref, optionnel et ne jamais être l’unique moyen de communication. | Les animations FILON doivent confirmer une recherche, un suivi ou un changement de prix ; elles ne doivent jamais masquer une information de prix ou de disponibilité. |
| Apple HIG — Materials | Les matériaux définissent une hiérarchie ; les couches translucides sont réservées à la navigation et aux contrôles au-dessus du contenu, tandis que le contenu dense exige une surface lisible. | Les données Catalogue restent sur des surfaces opaques contrastées. Un effet de matière discret peut servir aux feuilles, filtres et actions temporaires, pas aux cartes de prix. |
| Material Design 3 / I-O 2026 | La direction expressive associe couleur, mouvement, formes, composants adaptatifs et typographie flexible — sans remplacer la clarté fonctionnelle. | FILON utilise l’ambre comme signal de focalisation, la géométrie orthogonale comme structure et le mouvement court comme retour de décision. |
| Muzli — Mobile patterns 2026 | Les tendances robustes sont structurelles : adaptation par intention, gestes avec alternative visible, actions accessibles au pouce, profondeur fonctionnelle et support natif du sombre. | FILON doit ordonner ses modules selon le contexte réel : recherche, suivis, comparaison ou exploration — sans déplacer arbitrairement la navigation. |
| UX Collective — Experience trends 2026 | Les expériences d’IA centrées sur l’intention doivent rendre les signaux et les limites compréhensibles ; les interfaces multimodales exigent une transition fluide et des solutions de repli. | L’Assistant FILON explique ce qu’il a trouvé, ce qui manque et permet de corriger la demande ou de revenir aux données Catalogue. |
| Google PAIR Guidebook | La transparence doit calibrer les attentes et préserver le contrôle utilisateur, surtout quand le système produit des recommandations. | Les verdicts FILON affichent la source, l’évidence disponible, la fraîcheur et les actions de contrôle plutôt qu’un conseil opaque. |

## Ce que FILON ne doit pas faire

FILON ne doit pas imiter une interface de chatbot générique, une grille e-commerce surchargée, ni un tableau de bord financier froid. Les effets de verre, la 3D, les gradients et les animations ne sont pertinents que lorsqu’ils expliquent une couche, une hiérarchie ou une transition. Aucun module ne doit être « personnalisé » à partir d’une hypothèse non confirmée.

## Principes de conception proposés

1. **Décision avant découverte.** L’écran d’entrée privilégie le besoin actuel : rechercher, suivre une baisse, comparer un produit ou demander un éclairage à l’Assistant.
2. **Preuve avant promesse.** Chaque signal visible précise ce qui est observé : prix courant, haut relevé, nombre de relevés, date de source ou disponibilité inconnue.
3. **Matière utile.** La profondeur distingue contenu, action primaire et contrôle temporaire ; elle n’est jamais utilisée pour décorer une carte de données.
4. **Adaptation explicable.** Les modules peuvent remonter selon des préférences ou une action récente explicitement enregistrée, mais la personne garde les entrées stables et peut ignorer la suggestion.
5. **Vivant avec retenue.** Les micro-mouvements répondent aux pressions, à la fraîcheur et aux changements observés. Respecter Réduire les animations et garder une alternative lisible.
6. **Mobile d’abord, grand écran ensuite.** Les actions décisionnelles restent dans la zone du pouce. Tablette et pliable élargissent le contenu sans transformer l’app en site web.

## Direction FILON : « la matière de la décision »

FILON ne doit pas se présenter comme un catalogue enrichi ni comme un chatbot qui parle d’achats. Sa différence consiste à matérialiser l’incertitude d’un achat : l’offre actuellement visible, les observations qui la soutiennent, le temps couvert, l’absence éventuelle de donnée, puis l’action que la personne conserve en main. L’interface devient une succession de **moments de décision** plutôt qu’une collection de pages.

La matière visuelle reste spécifique à FILON : fond minéral clair ou sombre, ambre réservé au point de focalisation, géométrie orthogonale légèrement décalée et surfaces calmes pour les chiffres. Les mouvements doivent être courts, directionnels et attachés à une cause : la source s’actualise, un seuil est atteint, une comparaison s’ouvre, une offre est suivie. Les produits et les prix ne doivent jamais flotter dans des effets décoratifs ou des bulles dorées.

## Feuille de route front-end priorisée

| Priorité | Évolution | Rôle dans le parcours | Données et garde-fous |
|---|---|---|---|
| P0 | **Pont de décision Catalogue → Assistant** | À partir d’un mouvement observé ou d’une recherche, la personne peut demander « est-ce adapté à mon besoin ? » sans recommencer son contexte. | Transmettre seulement nom, catégorie, prix et marchand connus ; aucune inférence non affichée. |
| P0 | **Fiche « preuve » sur Produit** | Regrouper prix courant, plage observée, nombre de relevés, disponibilité et date de source dans une structure scannable avant le CTA marchand. | Afficher « inconnu » quand une donnée n’est pas fournie ; ne pas produire de tendance sans historique suffisant. |
| P1 | **Accueil par intention stable** | Trois entrées immuables : trouver, suivre, éclairer. Un seul module secondaire peut remonter selon une action récente explicitement enregistrée. | Ne jamais déplacer les entrées principales, ni personnaliser sans raison visible et réversible. |
| P1 | **Suivi comme rituel court** | Une alerte franchie ou un changement observé produit une carte concise : ce qui a changé, pourquoi, que faire. | Haptique léger uniquement après une action explicite et alternative visuelle systématique. |
| P2 | **Matière fonctionnelle** | Employer une couche translucide seulement pour les contrôles temporaires : filtres, confirmations, feuille de comparaison. | Prévoir des surfaces opaques contrastées et le respect de Réduire la transparence / Réduire les animations. |
| P2 | **Progression d’Intelligence explicable** | Afficher une courte séquence : « je cherche », « je compare les offres FILON », « voici l’évidence ». | Actions Modifier, Ignorer et Rechercher dans le Catalogue restent toujours visibles. |

## Première règle de mise en œuvre

Avant chaque nouvelle surface, l’équipe doit pouvoir répondre à trois questions dans le composant même : **quelle décision aide-t-elle ? quelle donnée réelle la soutient ? quelle action garde le contrôle à la personne ?** Si l’une des réponses est absente, il ne s’agit pas encore d’une fonctionnalité FILON.

## Sources

1. [Apple Human Interface Guidelines — Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
2. [Apple Human Interface Guidelines — Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
3. [Material Design 3](https://m3.material.io/)
4. [Muzli — Mobile App Design Trends 2026](https://muz.li/blog/whats-changing-in-mobile-app-design-ui-patterns-that-matter-in-2026/)
5. [UX Collective — Experience Design Trends 2026](https://uxdesign.cc/the-most-popular-experience-design-trends-of-2026-3ca85c8a3e3d)
6. [Google PAIR — Principles and Patterns](https://pair.withgoogle.com/guidebook/patterns)
