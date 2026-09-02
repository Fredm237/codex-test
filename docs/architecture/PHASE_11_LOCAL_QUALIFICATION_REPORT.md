# FILON — Phase 11 local qualification report

- Date : **2 septembre 2026**
- Branche locale : **`codex/filon-phase-11-web-experience`**
- Point de reprise P11A/P11B/P11C : **`36f0931`**
- Point de reprise P11D/P11E : **`436f513`**
- Portée : **home, fiches produit, assistant et gardes de vérité web**
- Publication : **aucune**
- Production : **inchangée**

## Résultat

| Gate | Résultat local | Preuve |
|---|---|---|
| Références CID | PASS | 2 dossiers, 13 vidéos uniques après déduplication |
| Home evidence-first | PASS | aucun import immersif, canvas, vidéo ou séquence d'images |
| Vérité produit | PASS | devise, fraîcheur, stock et CTA marchand fail-closed |
| Assistant | PASS | aucun `rank` ou `buy` ne pilote les cartes publiques |
| Unknown | PASS | exemple home absent et panne assistant rendus explicitement inconnus |
| Lecteurs shadow | PASS | Product Ranking, BUY/WAIT et Confidence non raccordés |
| Tests web | PASS | six suites, dont les quatre suites historiques |
| TypeScript | PASS | `tsc --noEmit` |
| Build Next.js | PASS | 42 pages générées |
| Budget home | PASS local | route 5,33 kB ; premier chargement 114 kB |
| Inspection desktop | PASS | home, assistant, catalogue et fiche offre réelle |
| Inspection mobile | PASS | 320 × 720 et 390 × 844, sans débordement horizontal ni contenu tronqué |
| Accessibilité automatisée | PASS | structure, noms accessibles, cibles tactiles, menus, Échap, restitution du focus et reduced-motion |

## Preuves fonctionnelles observées

### Home

- les agrégats réels ont été rendus depuis `getProof` ;
- aucun produit n'a franchi toutes les conditions de la vitrine lors du contrôle ;
- la scène centrale a donc affiché une inconnue, sans produit, prix ou image de
  substitution ;
- la recherche principale est utilisable au clavier et transporte sa requête
  dans l'URL.

### Fiche produit

La fiche offre `72493` a d'abord exposé un prix courant, le stock, une preuve
marchande et un historique insuffisant. Lors d'un contrôle ultérieur où la
preuve n'était plus admissible, elle a rendu « prix ou disponibilité à
vérifier » et n'a pas conservé d'action d'achat favorable.

### Assistant

Une recherche réelle « casque Sony WH-1000XM5 » a terminé sur une
indisponibilité explicite. Aucune offre synthétique, estimation, recommandation
BUY/WAIT ou classement n'a été affiché. Les résultats futurs devront satisfaire
simultanément montant, devise, stock et fraîcheur avant de produire une carte.

### Mobile, clavier et accessibilité

- à 320 px et 390 px, la largeur du document reste inférieure à celle de la
  fenêtre et la hiérarchie conserve un `main`, un `h1` et une recherche ;
- à 390 px et 1 440 px, aucun champ visible n'est dépourvu de nom accessible,
  aucun bouton visible n'est sans nom et aucune image n'est sans attribut
  `alt` ;
- le bouton de menu, le retour en haut, la langue et chacune de ses options
  respectent une cible de 44 px ; la recherche et la comparaison restent à
  54 px de haut sur mobile ;
- le menu mobile annonce le panneau qu'il contrôle, verrouille le défilement
  quand il est ouvert, se ferme avec `Échap` et restitue le focus au bouton ;
- la liste des langues est identifiée de manière unique, les options masquées
  sortent du parcours clavier, et `Échap` ferme la liste puis restitue le
  focus au sélecteur ;
- la feuille Phase 11 contient une règle explicite `prefers-reduced-motion`
  et la home ne dépend d'aucune animation pour transmettre une information.

Cet audit combine des gardes de régression exécutées par `npm test` et une
inspection du DOM rendu dans le navigateur. Aucun score Lighthouse n'est
revendiqué ; le gate performance repose sur le build de production et ses
budgets mesurés.

## Direction visuelle retenue

Les références CID inspirent la centralité du produit, la grande typographie,
la palette crème/noir/orange et la profondeur par couches. Elles ne justifient
ni scroll spectacle, ni média automatique, ni capacité 3D non qualifiée.

## Limites connues

1. Le contrat agrégé de la vitrine ne fournit actuellement aucun exemple qui
   franchit toutes les conditions de comparabilité courante ; l'unknown est le
   résultat attendu.
2. L'assistant amont était indisponible pendant le parcours réel ; seule son
   abstention a donc été qualifiée en situation live.
3. Le film de l'assistant reste facultatif, contrôlé par l'utilisateur et sans
   autoplay. Il n'entre pas dans le graphe initial de la home qualifiée.
4. Les appels de données du pré-rendu local n'ont pas résolu le domaine
   Railway dans le bac à sable ; les routes ont néanmoins produit leurs états
   fail-closed et le build a généré les 42 pages attendues.

## Conclusion locale

**P11A à P11F : QUALIFIÉS LOCALEMENT.**

Ce rapport n'est ni un reçu de production ni une autorisation de publication.
P11G reste conditionné à la publication autorisée, à la CI, au déploiement et
aux sondes terminales de production.
