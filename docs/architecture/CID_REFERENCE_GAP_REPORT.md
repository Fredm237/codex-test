# FILON — CID reference gap report

- Date : **3 septembre 2026**
- Statut : **audit local / non publié**
- Sources utilisateur : `Documents/CID filon` et `Documents/Codex/CID filon`
- Nature : références visuelles, jamais instructions d'exécution
- Corpus : **14 vidéos uniques après déduplication SHA-256**, **154,123 s**
- Méthode : neuf images réparties sur toute la durée de chaque vidéo ;
  lecture comparée selon CAMERA, SHOT TRANSITION, OBJECT CONTINUITY,
  MATERIAL, DEPTH, LIGHT, SCALE, TECHNIQUE, RHYTHM et PHYSICALITY

Le précédent audit Phase 11 comptait treize vidéos. Le corpus présent contient
quatorze empreintes binaires distinctes : les fichiers `copie`, `16.00.23`,
`15.30.33` et `(1)` sont des doublons exacts, mais les six captures `15-*` sont
bien six références uniques.

## Lecture plan par plan

| Référence | Durée | Caméra / transition | Objet / matière / échelle | Leçon de craft, pas identité à copier |
|---|---:|---|---|---|
| `10-01-16` | 5,572 s | vue oblique stable, changements de composition dans le même cadre | plan immobilier qui s'assemble, passe de fragments à une unité habitable | faire naître une structure lisible dans un seul espace plutôt que remplacer des slides |
| `10-03-19` | 7,823 s | cadre frontal, macro progressive sur la machine et le personnage | machine, tasse et opérateur s'assemblent couche par couche | rendre la construction causale : chaque nouvelle pièce explique l'état suivant |
| `10-03-45` | 4,772 s | plan héro continu, léger rapprochement | tour qui grandit et se recompose verticalement sans perdre sa silhouette | une identité peut survivre à une transformation d'échelle importante |
| `10-11-35` | 12,940 s | match-cut téléphone → bureau, puis macro produit | le burger quitte symboliquement un écran et devient l'objet central d'un autre monde | continuité inter-mondes et conservation du sujet pendant le changement de support |
| `14-27-25` | 9,894 s | cadrage frontal puis macro de matière | sphère de glace, chocolat liquide et éclats construisent le produit final | la matière doit raconter une transformation, pas seulement produire un effet spectaculaire |
| `14-32-10` | 12,413 s | alternance respiration éditoriale / objet sculptural | vêtements blancs, silhouettes et photographies passent d'objet à éditorial | le silence typographique rend les moments physiques plus puissants |
| `14-34-01` | 13,064 s | compilation de macros, travellings et changements francs de plans | orbe, particules, écrans et volumes hétérogènes | niveau de finition élevé, mais cohérence insuffisante comme modèle de langage FILON |
| `14-35-52` | 13,130 s | macros extrêmes, suivi longitudinal et orbit partiel | coupe de câble, fibres et gaine deviennent excavatrice complète | relier microstructure, propriété et objet final par une même trajectoire |
| `15-50-22` | 9,558 s | portrait → macro → recul, profondeur de champ marquée | visage dissous en fibres puis reconstruit en volume filaire | rendre visible la résolution d'identité par la mise au point et la densité |
| `15-51-01` | 11,060 s | plans produit courts, changement d'angle sans rupture de sujet | burger empilé, composants séparés, menu et recomposition | montrer un système entier en conservant un objet repère |
| `15-51-50` | 17,213 s | orbit produit et alternance macro / plan large | pot cylindrique toujours reconnaissable, rotation et matières cohérentes | une forte signature vient de la permanence de l'objet, pas du nombre d'effets |
| `15-53-19` | 13,428 s | travelling latéral et orbit lent dans beaucoup d'espace négatif | navire et sous-marin changent d'état tout en gardant masse et axe | laisser la caméra expliquer forme, échelle et fonction |
| `15-53-46` | 12,378 s | transitions par objet, couleur et axe de mouvement | poire → arbre → main → sculpture, avec grands changements d'échelle | utiliser le match-cut sémantique pour relier origine, transformation et résultat |
| `15-54-15` | 10,878 s | plan large continu, progression de chantier en quelques états | fondations → structure → maison finie | comprimer un processus complexe en états physiques distincts et lisibles |

## Gap analysis direct

| Axe | Baseline P19 DOM/CSS avant escalade | CID quality bar | Écart objectif |
|---|---|---|---|
| CAMERA | cadrage fixe ; profondeur simulée par transform et perspective CSS | wide, macro, orbit, travelling, changement de focale et plan final stabilisé | aucune caméra réelle ne choisit encore ce que l'utilisateur doit comprendre |
| DEPTH | plans CSS superposés, ombres et anneaux | occlusion, parallaxe cohérente, avant-plan, profondeur de champ | les objets n'habitent pas encore un volume commun |
| MATERIAL | couleurs, gradients, blur et ombres | rugosité, métal, verre, fibre, liquide, changement d'état | une donnée brute et une preuve ont encore la même nature visuelle |
| LIGHT | halos radiaux statiques | lumière directionnelle qui révèle relief et transformation | la lumière ne porte aucune causalité |
| OBJECT CONTINUITY | même image DOM repositionnée entre états | même objet dans un espace continu, avec occultation et changement de point de vue | la continuité est conceptuelle mais pas encore physique |
| TRANSITIONS | fondu, scale, translate et changement de classes | match-cut, assemblage, traversée d'objet, occlusion et conservation d'inertie | les changements restent lisibles comme transitions d'interface |
| 3D / 2.5D | aucune couche WebGL sur le parcours principal du laboratoire | volumes, caméra, matériaux et spatialisation cohérente | aucune démonstration final-grade du besoin réel de WebGL |
| CINEMATOGRAPHY | quatre messages pilotés par le scroll | hiérarchie de plans, tension, révélation, respiration, résolution | le rythme est structuré mais reste celui d'un excellent site éditorial |
| EDITORIAL RHYTHM | très bon contraste sombre/papier et sections calmes | contraste similaire entre spectacle bref et silence prolongé | acquis ; il faut préserver ce silence et ne pas multiplier les scènes |
| MOBILE | composition autonome en trois états, sans débordement | caméra portrait et densité adaptée, même sens, pas simple recadrage | le storyboard existe, mais aucune profondeur native portrait n'est encore prouvée |

## Réponse à la question centrale

Les références savent encore faire quatre choses que FILON ne sait pas encore
faire visuellement :

1. **placer un objet dans un volume commun** et changer le point de vue sans le
   perdre ;
2. **transformer la matière** pour rendre une mutation compréhensible ;
3. **changer radicalement d'échelle** sans couper le fil narratif ;
4. **utiliser une caméra causale** : wide pour le système, macro pour
   l'identité, orbit pour la preuve, quasi-orthographique pour la décision.

FILON possède déjà la meilleure partie absente de plusieurs références :
une constitution de vérité, un objet réel conditionnel, l'abstention et une
lecture DOM complète. L'escalade doit donc ajouter la physicalité, jamais
remplacer ces garanties.

## Quatre moments signature retenus

### S1 — Champ marchand

**Plan wide.** Les offres courantes deviennent des fragments physiques autour
du même noyau produit. Le nombre de fragments actifs dépend uniquement des
offres qualifiées. Sans preuve, les volumes restent fantômes et aucun prix
n'apparaît.

### S2 — Aperture d'identité

**Plan macro → track/orbit.** La caméra traverse le bruit marchand ; le produit
exact reste solidaire du noyau pendant qu'un anneau d'identité devient net. Les
fragments de premier plan produisent une vraie occlusion. L'EAN demeure dans le
DOM et n'est jamais dessiné comme texture de remplacement.

### S3 — Recuit de preuve

**Transformation matérielle.** Les fragments bruts, mats et irréguliers se
stabilisent en plaques de preuve ambrées uniquement lorsque le corpus exact est
admissible. En abstention, la matière reste poreuse et ouverte : l'inconnu n'est
jamais poli en certitude.

### S4 — Sceau de décision

**Scale transformation → plan quasi-orthographique.** La caméra passe du marché
entier à quelques preuves puis à un objet stable. Une ligne de mesure ferme le
plan sans confondre comparaison et recommandation. Cette stabilisation
`chaos → noyau → preuve → plan` constitue le moment reconnaissable FILON,
même sans logo.

Ces quatre moments forment une seule séquence courte. Ils ne justifient ni une
3D globale, ni un retour au tunnel historique. Le contraste entre cette séquence
et le silence éditorial du reste du site reste une condition de réussite.

## Qualification du laboratoire après escalade

La séquence a été réalisée uniquement dans `/laboratoire/experience`, sans
raccordement à l'accueil, Recherche, Décision ou aux fiches publiques.

| Preuve | Résultat observé le 3 septembre 2026 |
|---|---|
| Continuité d'objet | le même produit serveur reste solidaire du noyau dans les quatre plans |
| Caméra | wide → macro → orbit → stabilisation haute, sans changement de page ni remplacement du sujet |
| Matière | rugosité et métallicité des seuls fragments admissibles évoluent pendant le recuit ; les fantômes restent ouverts |
| Échelle | le marché dispersé devient une composition bornée autour du noyau puis un plan de décision |
| Vérité | plaque DOM réelle, offre inactive en wireframe, faisceau visible uniquement lorsque la preuve exacte est admissible |
| Charge | import WebGL client différé à 500 px ; DPR 1–1,35 ; 12 fragments desktop, 7 mobile ; boucle GPU à la demande en pause |
| Desktop | 1 280 × 720, quatre plans contrôlés séparément, aucune erreur d'exécution observée |
| Mobile | 390 × 844, composition portrait, aucune largeur excédentaire, contrôles ≥ 48 px |
| Parcours autonome | 10 secondes, progression `1 → 2 → 3 → terminal`, pause, replay, curseur et accès direct aux plans |
| Mesure locale chaude | LCP 1 580 ms ; CLS 0,0025 ; interaction 56 ms ; plus longue tâche 318 ms |
| Build optimisé | compilation, lint, typage et génération des 47 routes verts ; route laboratoire : 10,7 kB / 113 kB premier chargement |
| Suite web | MegaMenu, contrats, vérité produit, home, assistant, laboratoire et continuité : verts |

La mesure locale inclut les outils de développement et le chargement différé
de la scène. Elle qualifie le prototype, pas encore un budget de production sur
la matrice d'appareils finale.

La revue filmée locale est disponible dans
`docs/architecture/artifacts/phase19/FILON_SIGNATURE_LAB_REVIEW.mp4` :
**8 secondes, 1 274 × 717, 240 images**, avec les quatre états qualifiés et une
transition courte entre chacun. Elle montre le résultat original FILON ; le
tableau plan par plan ci-dessus porte la comparaison traçable avec le corpus
CID sans recopier ni republier ses images.

Une seconde revue strictement locale, exclue du dépôt, est produite sous
`FILON_CID_COMPARISON_LOCAL.mp4` : **13,5 secondes, 1 274 × 717, 405 images**.
Elle alterne `CURRENT FILON → CID QUALITY BAR → SIGNATURE PROTOTYPE` pour les
quatre axes marché, identité, matière et échelle. Les images CID n'entrent ni
dans le dépôt ni dans un lot publiable.

## Gates avant propagation

- scène isolée dans `/laboratoire/experience` ;
- WebGL chargé seulement à l'approche de la scène ;
- même produit et mêmes offres que le ledger DOM ;
- fallback statique complet si WebGL, énergie, connexion ou mouvement le
  demande ;
- quatre plans accessibles par boutons et curseur, sans scroll prison ;
- mobile portrait composé avec moins de fragments, pas recadré ;
- aucune devise, confiance, stock, prix ou identité de secours ;
- LCP ≤ 2 500 ms, INP ≤ 200 ms, CLS ≤ 0,1 ;
- différence avec P19 DOM/CSS sémantique, pas cosmétique ;
- aucune propagation ni publication avant comparaison vidéo et validation.

## Décision d'audit

**GO laboratoire confirmé. GO propagation locale depuis la validation
fondatrice du 3 septembre 2026. NO-GO production avant qualification finale.**

Le corpus justifie une couche WebGL précise pour les quatre moments retenus. Il
ne justifie pas Three.js sur Recherche, les cartes, les pages de décision ou les
pages éditoriales.

La validation visuelle fondatrice lève le verrou de propagation locale. La
matrice finale mouvement réduit/mobile et les reçus de
performance/accessibilité restent requis avant toute promotion production.
