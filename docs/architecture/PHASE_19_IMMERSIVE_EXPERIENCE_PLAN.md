# FILON — Phase 19 Immersive Experience

- Date : **3 septembre 2026**
- Branche de travail : **`codex/filon-immersive-production`**
- Base : **`main` à `e48529bfde73c958f15ae00e1eaff953d382fedc`**
- Mandat source : **FILON — Immersive Experience Production Bible**
- État : **P19A–E qualifiés ; direction WebGL validée par le fondateur ; home et dossier produit exact raccordés localement, sans publication production**
- Règle : **aucune publication ni activation production sans qualification du parcours complet**

## 1. État exact du mandat

Le socle web evidence-first de Phase 11 est publié, testé et déployé. Le mandat
immersif complet n'est pas encore promu. Sur la branche locale Phase 19,
`WebExperience` exécute désormais la caméra R3F/Three.js qualifiée tandis que
le DOM reste la source de vérité. Aucun ancien tunnel vidéo ni aucune séquence
de 1 200 images n'est raccordé.

| Étape du mandat | État | Preuve ou sortie attendue |
|---|---|---|
| 1. Audit du système visuel | **PASS** | audit CID Phase 11A et tokens Phase 11 |
| 2. Audit de l'implémentation immersive | **PASS P19A** | inventaire technique et dette ci-dessous |
| 3. Benchmark 2024–2026 | **PASS documentaire** | références et enseignements ci-dessous |
| 4. Creative brief | **PASS documentaire** | promesse, histoire et règles ci-dessous |
| 5. Trois directions radicales | **PASS documentaire** | directions A, B et C ci-dessous |
| 6. Storyboards | **PASS documentaire** | storyboards conceptuels ci-dessous |
| 7. Matrice de faisabilité | **PASS documentaire** | matrice et budgets ci-dessous |
| 8. Prototype caméra | **PASS local** | P19B, quatre plans continus |
| 9. Prototype transition | **PASS local** | P19C, signal → résolution → comparaison |
| 10. Prototype produit exact | **PASS local** | P19D, preuve exacte fail-closed |
| 11. Prototype mobile | **PASS local** | P19E, trois états autonomes |
| 12. Revues visuelle/performance/a11y | **PASS local partiel** | build de production, desktop, fallback et budgets verts ; nouvelle Preview mobile et mesure terrain encore requises |
| 13. Choix du langage final | **PASS** | B — chorégraphie de preuve |
| 14. Expérience complète | **EN COURS / NON PUBLIÉE** | noyau inter-routes, home et dossier exact locaux ; canary final encore interdit |

## 2. Audit de l'existant

### Surface publique qualifiée

- home : rendu serveur de la preuve, puis expérience client légère ;
- budget Phase 11 mesuré : route **5,33 kB**, premier chargement **114 kB** ;
- unknown explicite lorsque la comparaison exacte ne peut pas être prouvée ;
- recherche accessible immédiatement, sans attendre une animation ;
- lecteurs BUY/WAIT, ranking et confidence toujours absents du graphe public ;
- garde CI explicite interdisant l'immersion sur la home tant que la gate reste
  fermée.

### Surface immersive historique non raccordée

- `components/cinematic` : moteur de timeline et rendu canvas sur séquence ;
- `components/filon/ImmersiveExperience.tsx` : ancien rendu canvas ;
- `OrbViewer3D.tsx` : React Three Fiber, Drei et Three.js ;
- `SequenceScroll.tsx` : défilement pilotant une séquence d'images ;
- dépendances déjà présentes : Three.js, React Three Fiber, Drei,
  Framer Motion et Lenis ;
- médias : environ **154 Mo** sous `public/cinematic`, **40 Mo** sous
  `public/seq/hero`, **41 Mo** sous `public/film`, **9,6 Mo** sous
  `public/video` et **796 Ko** sous `public/3d` ;
- la scène `interior-city` référence **1 200 frames**, huit plans et une hauteur
  de **3 000 vh** sur desktop comme mobile.

### Verdict d'audit

Le code historique constitue un laboratoire, pas une expérience prête pour la
production. Ses points réutilisables sont le modèle de plans, l'interpolation
de timeline, le fallback statique et le principe d'un overlay DOM. Ses points
à ne pas raccorder tels quels sont le tunnel de 3 000 vh, le coût média, le
mobile identique au desktop, le chargement massif de frames et l'absence de
preuve produit au centre de chaque plan.

## 3. Benchmark 2024–2026

Les références servent de seuil de craft, jamais de modèle à copier.

| Référence | Signal observé | Ce que FILON retient | Ce que FILON refuse |
|---|---|---|---|
| [PUMA Velocity 2 Experience](https://www.awwwards.com/inspiration/high-fidelity-3d-scrolling-experience) | produit 3D, défilement, explication de caractéristiques et passage vers la fiche | un produit exact reste le sujet de la caméra | 3D purement décorative ou sans preuve |
| [Cash App Brand Guidelines — Product](https://www.awwwards.com/inspiration/cash-app-product-section-cash-app-brand-guidelines) | alternance de sections produit, 3D, illustrations et identité | transitions de matière cohérentes avec la marque | collage de techniques sans fonction |
| [KODE Immersive](https://www.awwwards.com/inspiration/easter-egg-kode-immersive) | continuité desktop/mobile, préchargement, landing et micro-interactions | une grammaire de mouvement cohérente de bout en bout | curseur gadget et effets sans utilité |
| [The Best You by Klook / Unseen](https://www.awwwards.com/unseenstudio/?library=true&previewmode=true) | expérience interactive récompensée en juin 2025 | progression narrative courte et participation utile | quiz qui retarde artificiellement la valeur |
| [Just Kibbeh](https://www.awwwards.com/sites/just-kibbeh) | narration e-commerce pilotée par le scroll et détails produit | transformer le scroll en révélation de faits | histoire de marque plus forte que le produit |
| [Smartbiotic Ice Cream](https://www.awwwards.com/sites/smartbiotic-ice-cream) | produit réaliste, déclinaisons desktop/mobile | priorité à la matière et au cadrage du produit | vidéo lourde comme seule expérience |

Les contraintes techniques sont fondées sur les seuils Core Web Vitals
officiels : LCP ≤ 2,5 s, INP ≤ 200 ms et CLS ≤ 0,1 au 75e percentile. Le code
immersif sera chargé à la demande conformément au guide de lazy loading Next.js.
React Three Fiber permet un rendu à la demande et une qualité adaptative ; le
fallback réduit doit respecter `prefers-reduced-motion`. `saveData` est utilisé
comme signal supplémentaire mais jamais comme unique moyen de détection, car
sa disponibilité navigateur est limitée.

Références techniques :

- [seuils Core Web Vitals](https://web.dev/articles/defining-core-web-vitals-thresholds) ;
- [lazy loading Next.js](https://nextjs.org/docs/app/guides/lazy-loading) ;
- [performance React Three Fiber](https://r3f.docs.pmnd.rs/advanced/scaling-performance) ;
- [`prefers-reduced-motion`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion) ;
- [`saveData`](https://developer.mozilla.org/en-US/docs/Web/API/NetworkInformation/saveData).

## 4. Creative brief

### Promesse

**FILON transforme le chaos marchand en décision vérifiable.**

### Histoire à comprendre sans document explicatif

1. le marché est fragmenté ;
2. FILON rassemble uniquement ce qui est comparable ;
3. FILON expose les preuves et conserve les inconnues ;
4. une décision claire émerge ;
5. la prochaine action est la recherche.

### Moment distinctif recherché

Un même produit apparaît au milieu d'une multitude d'offres incompatibles.
Les offres non prouvées restent opaques ou s'écartent. Les preuves compatibles
s'alignent physiquement autour de l'objet. La caméra cesse de bouger au moment
où l'interface de décision devient nette. La stabilité visuelle matérialise la
confiance, pas une particule ou un halo « IA ».

### Invariants

- un prix n'apparaît jamais sans devise supportée ;
- une offre non fraîche ou indisponible ne prend jamais une forme favorable ;
- l'unknown est une composition finale légitime ;
- le champ de recherche est accessible sans attendre la fin du chapitre ;
- le DOM porte le texte, les contrôles, le focus et la sémantique ;
- WebGL/canvas porte seulement la matière, la profondeur et les transitions ;
- aucun lecteur shadow n'est raccordé par le travail visuel ;
- le mode réduit transmet exactement la même histoire sans mouvement spatial.

## 5. Trois directions radicalement différentes

### Direction A — Le marché se met au point

**Concept.** Une chambre optique monumentale observe un produit exact. Le
commerce commence comme un plan flou et chromatiquement aberrant. Les preuves
agissent comme des lentilles : identité, fraîcheur, stock et devise ramènent
progressivement l'image au point.

- palette : ivoire chaud, encre noire, orange FILON, reflets verre fumé ;
- typographie : serif éditoriale monumentale + sans-serif de laboratoire ;
- matière : verre optique, papier, métal satiné ;
- lumière : faisceau latéral chaud, ombres nettes après vérification ;
- caméra : macro lente, rack focus, travelling très court ;
- mouvement : dispersion → alignement → immobilité ;
- home : une mise au point de 10–16 secondes ;
- produit : l'objet devient net tandis que les offres se calent dans le plan
  focal ;
- recherche : la requête agit comme la bague de mise au point.

### Direction B — La table des preuves

**Concept.** FILON est une table de décision physique. Produit, étiquettes de
prix, lignes d'historique et sceaux de preuve arrivent comme des pièces
éditoriales tangibles. Les éléments incompatibles n'entrent pas dans la grille.

- palette : crème, orange minéral, brun cacao, vert preuve très retenu ;
- typographie : grand titre éditorial + chiffres monospacés ;
- matière : papier épais, émail, aluminium anodisé, ombre naturelle ;
- lumière : studio zénithal, aucune brillance « sci-fi » ;
- caméra : vue oblique puis bascule orthographique ;
- mouvement : glissement, pli, empilement, aimantation ;
- home : le chaos de cartes devient une composition exacte ;
- produit : dossier produit manipulable, preuves en périphérie ;
- recherche : le texte saisi découpe et réordonne la table.

### Direction C — Le relief de décision

**Concept.** Les offres deviennent un relief topographique abstrait dérivé de
données réelles. Les hauteurs représentent des écarts observés, les coupures
les incompatibilités, les lignes continues les preuves partageables. FILON
aplatit le relief jusqu'à un plan de décision lisible.

- palette : encre profonde, ambre, sable, accent blanc chaud ;
- typographie : sans-serif condensée spatiale + serif uniquement au verdict ;
- matière : terrain mat, lignes gravées, lumière rasante ;
- lumière : sombre au chaos, claire au plan de décision ;
- caméra : survol topographique puis plongée verticale ;
- mouvement : relief → coupe → plan ;
- home : traversée courte d'un paysage de prix ;
- produit : le produit émerge d'une coupe où chaque strate est une preuve ;
- recherche : transition géographique vers le dossier exact.

## 6. Storyboards conceptuels

### A — Le marché se met au point

| Plan | But/message | Cadre, lumière et mouvement | DOM, entrée/sortie, interaction |
|---|---|---|---|
| A1 · 0–3 s | montrer la confusion | macro produit flou, halos d'offres, caméra fixe | « Le même produit ? » ; apparition douce |
| A2 · 3–7 s | identifier | lentille latérale, silhouettes incompatibles rejetées | label `IDENTITÉ` ; scroll/touch avance |
| A3 · 7–11 s | vérifier | verre s'aligne, prix admissibles deviennent nets | badges frais/stock/devise dans le DOM |
| A4 · 11–14 s | décider | arrêt caméra, produit et écart observé nets | carte de preuve réelle ou unknown |
| A5 · 14–16 s | agir | recul de 4 %, champ de recherche prend le focus visuel | transition vers recherche sans focus forcé |

### B — La table des preuves

| Plan | But/message | Cadre, lumière et mouvement | DOM, entrée/sortie, interaction |
|---|---|---|---|
| B1 · 0–3 s | matérialiser le marché | vue oblique, cartes dispersées, lumière studio | « Des offres. Pas encore une comparaison. » |
| B2 · 3–7 s | séparer l'incomparable | les cartes invalides glissent hors grille | raisons visibles, jamais masquées par le canvas |
| B3 · 7–11 s | rapprocher les preuves | cartes valides s'aimantent au produit | devise et marchand restent lisibles |
| B4 · 11–14 s | rendre la décision | bascule orthographique, grille parfaitement stable | dossier exact/unknown comme état final |
| B5 · 14–16 s | ouvrir le parcours | la grille se transforme en formulaire | saisie et navigation DOM natives |

### C — Le relief de décision

| Plan | But/message | Cadre, lumière et mouvement | DOM, entrée/sortie, interaction |
|---|---|---|---|
| C1 · 0–3 s | montrer l'écart | survol sombre d'un relief de prix | bornes observées uniquement si prouvées |
| C2 · 3–7 s | révéler les ruptures | coupe latérale, failles = données incompatibles | légende accessible hors WebGL |
| C3 · 7–11 s | filtrer | lignes prouvées convergent, terrain s'aplatit | statut de chaque filtre dans le DOM |
| C4 · 11–14 s | conclure | plongée verticale, plan orange/ivoire | décision/abstention lisible sans mouvement |
| C5 · 14–16 s | rechercher | le plan devient surface de recherche | continuité de couleur vers `/recherche` |

Le storyboard de production sera choisi seulement après comparaison des trois
prototypes de langage. Les durées ci-dessus sont des plages narratives, pas un
autoplay bloquant : le contenu reste pilotable et skippable.

## 7. Matrice de faisabilité et architecture cible

| Besoin | Technique privilégiée | Fallback | Risque | Gate |
|---|---|---|---|---|
| objet exact | image catalogue détourée ou GLB validé | image `contain` | source produit insuffisante | aucune substitution synthétique |
| profondeur | CSS 3D puis R3F seulement si nécessaire | composition 2D | coût GPU | qualité adaptative et rendu à la demande |
| caméra | timeline bornée 10–20 s | coupes statiques | vertige, scroll prison | skip + reduced motion |
| données | preuve serveur Phase 11 | unknown explicite | donnée stale | mêmes gardes de vérité que la home |
| transition DOM/WebGL | overlay DOM stable au-dessus du canvas | DOM seul | focus perdu | ordre DOM et focus inchangés |
| médias | chargement par plan, AVIF/WebP/GLB | poster | 205 Mo historiques | aucun préchargement massif |
| mobile | storyboard propre, plans plus courts | affiche éditoriale | chauffe/batterie | test sur viewport et appareil contraint |
| mesure | Web Vitals + PerformanceObserver + traces | logs navigateur | moyenne trompeuse | p75 terrain après canary |

### Frontière technique

1. la home serveur continue de calculer `proof` ;
2. le HTML utile et le formulaire sont rendus immédiatement ;
3. un client boundary isolé décide entre poster, CSS 3D ou WebGL ;
4. l'immersion n'est chargée qu'après le contenu critique et jamais pour
   `prefers-reduced-motion`, données réduites ou capacité insuffisante ;
5. les états visuels reçoivent un modèle de vue déjà fail-closed ;
6. le canvas est `aria-hidden` et ne devient jamais la source de vérité ;
7. une erreur ou un abandon décharge l'immersion sans affecter le parcours.

## 8. Prototypes à construire avant la home

### P19B — Caméra et transition spatiale

- une route laboratoire non indexée ;
- un plan final-grade de 10–15 secondes ;
- compare Direction A et Direction C ;
- prouve lumière, matière, caméra, typographie, reduced-motion et skip.

### P19C — Transformation produit/données

- compare Direction A et Direction B ;
- utilise un modèle de preuve figé explicitement synthétique ou un produit réel
  admissible ;
- montre successivement exact, incomplet et unknown ;
- aucune couleur ou position ne peut transformer un état inconnu en recommandation.

### P19D — Dossier produit exact

- cible un produit réel admissible, Sony WH-1000XM6 Black si le catalogue le
  prouve, sinon le premier produit exact satisfaisant les mêmes gates ;
- identité, offres, historique et preuves sont visibles dans le DOM ;
- l'immersion enrichit la compréhension sans cacher la provenance.

### P19E — Mobile

- storyboard autonome, pas recadrage du desktop ;
- maximum trois états visuels et une transition structurante ;
- tactile, orientation, clavier virtuel, faible mémoire et reduced-motion testés.

## 9. Critères objectifs de passage

Un prototype ne passe que si tous les critères applicables sont prouvés :

### Vérité et fonction

- **0** prix, devise, stock, fraîcheur ou recommandation inventé ;
- **100 %** des états incomplets aboutissent à unknown/abstention ;
- recherche utilisable avant chargement de l'immersion ;
- même décision et mêmes preuves avec animation complète, mode réduit et canvas
  désactivé ;
- aucun lecteur shadow activé par le prototype.

### Accessibilité

- navigation clavier complète et focus visible ;
- skip accessible en un seul arrêt clavier ;
- aucune information uniquement portée par couleur, profondeur ou mouvement ;
- mode réduit sans travelling, zoom profond ou parallaxe ;
- texte et contrôles restent du DOM sémantique.

### Performance

- LCP ≤ **2,5 s**, INP ≤ **200 ms**, CLS ≤ **0,1** sur le profil de test ;
- aucune longue tâche > **200 ms** provoquée par l'initialisation immersive ;
- boucle de rendu inactive quand la scène est immobile ou hors écran ;
- zéro téléchargement de la séquence historique de 1 200 frames sur la home ;
- budget média initial du chapitre ≤ **2 Mo** mobile et ≤ **4 Mo** desktop ;
- budget JavaScript initial de la home inchangé ; chunk immersif différé et
  mesuré séparément ;
- dégradation automatique si la cadence soutenue descend sous **45 fps** ;
- fallback statique si elle reste sous **30 fps** après dégradation.

### Qualité créative

- histoire comprise : chaos → preuve → décision → recherche ;
- un moment FILON identifiable sans logo ;
- la 3D ou la profondeur explique une relation commerciale ;
- transition intentionnelle entre univers, sans simple fondu de page ;
- desktop et mobile paraissent conçus, pas respectivement complet et amputé ;
- revue sur vidéo à vitesse réelle, jamais par captures seules.

## 10. Ordre d'exécution fermé

1. construire P19B sur route laboratoire ;
2. mesurer et corriger P19B ;
3. construire P19C avec états exact/incomplet/unknown ;
4. construire P19D sur une preuve produit admissible ;
5. construire P19E en mobile-first ;
6. capturer vidéos, traces de performance et audit accessibilité ;
7. comparer A/B/C avec la même grille mesurable ;
8. choisir un seul langage visuel ;
9. remplacer la gate CI « aucun immersif » par une gate « immersif isolé,
   différé, accessible et fail-closed » ;
10. seulement ensuite intégrer un chapitre de 10–20 secondes à la home ;
11. canary borné, mesure terrain, puis décision de généralisation.

## Décision P19A

**GO pour les prototypes isolés. NO-GO pour le raccordement à la home.**

La direction par défaut à prototyper est **B — La table des preuves**, car elle
matérialise les relations produit/offre/preuve avec le moins de dépendance à une
3D lourde. **A — Le marché se met au point** sera le contre-prototype spatial.
**C — Le relief de décision** reste le concept le plus distinctif mais doit
d'abord prouver que l'abstraction ne nuit pas à la compréhension.

## Qualification des prototypes — 2 septembre 2026

Le laboratoire isolé `/laboratoire/experience` matérialise désormais les quatre
preuves attendues avant tout raccordement public :

- **P19B** : un plan continu de quatre shots — chaos, identité, marché,
  décision — avec objet produit conservé entre les mondes et sortie clavier ;
- **P19C** : une transition signal → résolution → comparaison, contrôlable sans
  scroll, dont les données textuelles ne changent jamais avec l'animation ;
- **P19D** : une fiche exacte choisie dynamiquement dans le catalogue. Lors de
  la qualification, l'EAN `4717622052664` disposait de cinq offres courantes,
  quatre marchands comparables, une plage EUR homogène et des observations
  fraîches. Le détail produit, et non l'agrégat de liste, est la frontière de
  preuve ;
- **P19E** : une composition mobile autonome, bornée à trois états — signal,
  preuve, action — avec cibles tactiles de 48 px et sans débordement horizontal
  à 390 px.

Les scénarios de repli ont été conservés : sans identité exacte, pluralité
marchande, devise homogène ou fraîcheur, le produit, le prix et l'action
marchande restent inconnus. Aucun lecteur shadow n'est raccordé.

Qualification observée :

- suite web complète verte ;
- TypeScript vert ;
- build Next.js production vert ;
- home inchangée à **5,33 kB / 114 kB First Load JS** ;
- laboratoire final à **7,8 kB / 110 kB First Load JS**, sonde comprise ;
- rendu desktop et 390 px vérifié, sans erreur navigateur ;
- états interactifs `0 → 1 → 2` vérifiés ;
- zéro canvas, zéro vidéo et zéro frame de l'ancien tunnel chargés ;
- sonde locale LCP/CLS/interaction/tâche longue/transfert intégrée au
  laboratoire pour la qualification finale reproductible.

## Langage retenu

La direction retenue est **B — La table des preuves**, étendue en
**chorégraphie de preuve**. Ce n'est pas une succession de sections et ce n'est
pas une esthétique de cartes : le site devient une continuité de plans où le
même objet passe du marché à son identité, de son identité à ses preuves, puis
de ses preuves à l'action.

La chambre optique de A et le relief de C ne deviennent pas des directions
parallèles. Ils restent deux outils du langage B : mise au point pour qualifier
l'identité, relief seulement lorsqu'une structure de prix ou de temps le
justifie. Cette convergence évite un produit visuellement fragmenté.

La clarification fondatrice du 2 septembre est contraignante : **le livrable
final est toute l'expérience FILON**, pas une homepage spectaculaire posée sur
un site conventionnel. Le chapitre home sera le premier déploiement du système,
pas sa limite. Catalogue, recherche, produit, Fashion, Wardrobe, Stylist,
Composer et Personal Commerce devront employer la même grammaire de plans,
d'objets continus et de preuves, avec leurs modes efficaces DOM toujours
disponibles.

## Gate après qualification visuelle

**GO créatif pour B / chorégraphie de preuve.**

Le raccordement local à la home était conditionné aux métriques produites par la
sonde sur le build de production : LCP ≤ 2,5 s, interaction ≤ 200 ms, CLS ≤ 0,1
et aucune tâche longue > 200 ms. Ces seuils ont été franchis localement. La
publication reste distincte : elle exige la qualification du plan home et ne
vaut pas généralisation aux autres surfaces.

### Mesure locale de production — 3 septembre 2026

La précharge globale des huit fichiers TTF Outfit/Inter a été supprimée, puis
les huit graisses statiques ont été remplacées dans le graphe par deux fontes
variables WOFF2 locales : Inter **47 Ko** et Outfit **31 Ko**. Cette correction
concerne toutes les routes, ne dépend d'aucun fournisseur au runtime et laisse le
navigateur charger uniquement les familles rencontrées. Sur la route laboratoire,
le transfert initial observé est passé de **1 166 Ko à 522 Ko**. La home et le
laboratoire restent respectivement à **5,33 kB / 114 kB** et **7,8 kB / 110 kB**
de JavaScript.

Après fermeture des anciennes prévisualisations qui saturaient l'hôte, une
origine locale neuve et un cache vide ont produit la mesure représentative :

| Profil observé | LCP | CLS | tâche longue max. | transfert |
|---|---:|---:|---:|---:|
| origine neuve, cache froid | 1 636 ms | 0,0006 | 0 ms | 522 Ko |
| après interaction produit exact | 1 636 ms | 0,0006 | 100 ms | 540 Ko |
| cache chaud | 728 ms | 0 | 60 ms | 18 Ko |

L'interaction produit exacte mesurée est de **152 ms**. Le LCP reste le `h1` et
la plus grande ressource transférée est désormais Fraunces WOFF2 à **80 Ko**.
Les mesures initiales obtenues alors que plus de quinze onglets de qualification
et plusieurs serveurs étaient encore actifs ont été conservées comme diagnostic
de contention, mais exclues de la décision : elles n'étaient pas reproductibles
après nettoyage de l'hôte.

**Verdict : GO performance local pour préparer le premier plan home.** Ce verdict
n'est ni une publication ni une généralisation : la mesure terrain et le canary
restent nécessaires avant promotion publique complète.

### Noyau de continuité inter-routes

Le premier élément de l'expérience complète est désormais implémenté localement
dans le shell partagé. Une navigation n'est plus traitée comme un fondu générique :
elle recadre la même table de décision et expose un chapitre sémantique stable.

| Chapitre | Routes couvertes | Fonction dans l'expérience |
|---|---|---|
| `signal` | home et éditorial général | formuler le besoin |
| `market` | recherche, catalogue, catégories, marchands | traverser le marché |
| `identity` | produit et produits exacts | conserver le même objet |
| `proof` | intelligence, méthode, transparence, sécurité | ouvrir les preuves |
| `decision` | score, cashback, codes promo, reconditionné | rendre le compromis lisible |
| `compose` | Outfit Studio et futures surfaces de création | assembler une solution |

Le balayage de matière est `aria-hidden`, ne capte aucun événement, disparaît
avec `prefers-reduced-motion` et n'impose ni canvas ni moteur 3D. Les passages
`market` et `proof` ont été vérifiés dans le navigateur sans débordement
horizontal. Ce noyau ne suffit pas à déclarer l'expérience complète : il fournit
la continuité sur laquelle chaque surface doit maintenant écrire son propre plan.

### Premier plan home local

La home est désormais le premier chapitre réel de la chorégraphie de preuve,
et non une page conventionnelle décorée par une scène. Son défilement pilote
quatre plans continus : chaos marchand, identité, comparabilité, décision. Le
même objet de preuve et le même formulaire restent dans le cadre ; le contenu
ne se transforme pas en succession de sections.

La branche qualifiée ne disposait pas d'un produit comparable admissible lors du
build. Le parcours observé rend donc quatre états honnêtes — identité à
démontrer, offres non comparables, conservation de l'inconnue — sans image,
prix ou décision de substitution. Le formulaire est utilisable à tout moment,
un lien d'évitement sort du chapitre et `prefers-reduced-motion` ou `saveData`
réduit la séquence à son état final.

Qualification locale du plan :

- build Next.js complet : **47 pages**, home à **6,56 kB / 115 kB First Load JS** ;
- delta par rapport au socle Phase 11 : **+1,23 kB** sur la route et **+1 kB** au
  premier chargement partagé ;
- quatre plans et état unknown vérifiés sur desktop ;
- composition dédiée vérifiée à **390 × 844 px**, sans débordement horizontal ;
- zéro canvas, zéro vidéo, zéro frame historique et zéro lecteur shadow ajouté ;
- recherche, navigation clavier, sortie du chapitre et mode réduit conservés.

### Espace marché Recherche → Catalogue

Recherche et Catalogue forment désormais deux plans consécutifs du même espace
marchand. Le plan `FILON / MARCHÉ 01` place la requête au centre d'un champ de
preuve sombre : source marchande, identité et devise restent trois dimensions
visibles du marché, jamais des ornements. Les états `idle`, `thinking`,
`results` et `failed` modifient ce même plan sans changer de décor ni masquer la
provenance. L'ancien poster photographique et son interface de film ont été
retirés de cette surface.

Le plan `FILON / MARCHÉ 02` reprend la même géométrie dans le Catalogue et la
fait passer vers une table éditoriale claire. Les rayons, filtres, tris, URLs,
offres rendues côté serveur et messages d'indisponibilité restent inchangés.
Quand l'API ne répond pas, Recherche conserve une abstention explicite et ne
fabrique ni offre, ni classement, ni conseil.

Qualification locale de la continuité :

- build Next.js complet vert : **47 pages**, Recherche à **9,79 kB / 164 kB**
  et Catalogue à **4,88 kB / 160 kB First Load JS** ;
- desktop et **390 × 844 px** vérifiés sur les deux plans, sans débordement
  horizontal ;
- état d'échec réel de Recherche vérifié : aucune recommandation de substitution ;
- libellés de marché localisés en français, néerlandais et anglais ;
- zéro canvas, zéro WebGL, zéro vidéo et zéro lecteur shadow ajouté.

### Registre Marchands → zoom Rayon `market`

Le marché ne s'arrête plus à Recherche et Catalogue. Marchands devient son
registre filtrable : recherche, régions, compteur et enseignes forment une
grille continue sur le même plan sombre. Un rayon devient ensuite un zoom de ce
même espace avec une coordonnée localisée, son volume indexé, ses sous-rayons et
ses offres. Les cartes produit restent les composants de vérité partagés ; leur
prix, fraîcheur, disponibilité et CTA conservent leurs gardes existantes.

La liste Marchands garde son deuxième essai client lorsque le préchargement
serveur est indisponible, puis affiche un état d'erreur explicite. Le rayon ne
fabrique aucune offre lorsque sa requête échoue. Les monogrammes marchands ne
remplacent qu'un logo absent et ne constituent pas une donnée métier.

Qualification automatique locale :

- suite web complète et TypeScript verts ;
- build Next.js complet vert : Marchands à **2,03 kB / 152 kB** et Rayon à
  **1,35 kB / 156 kB First Load JS** ;
- le build a rencontré une résolution DNS Railway indisponible et a conservé
  les replis existants sans générer de marchands ou d'offres fictifs ;
- registre marchand, états vide/indisponible, coordonnée Rayon et reduced-motion
  verrouillés par test ;
- aucun reader shadow, classement, recommandation ou média ajouté.

La revue visuelle desktop/mobile reste à rejouer ; aucune validation visuelle
n'est déclarée tant que la politique du navigateur refuse l'origine locale.

### Dossier produit exact `identity → proof`

La route `/produits/[ean]` conserve le produit comme même acteur entre le plan
marché et le plan de preuve. L'image catalogue devient une pièce physique de la
table, reliée au dossier par un axe de lecture. Le titre éditorial, l'EAN, le
nombre d'offres comparables actuelles et le nombre de marchands comparés restent
des éléments DOM visibles ; ils ne sont jamais encodés uniquement dans la
profondeur ou le mouvement.

Quand aucune comparaison monodevise actuelle n'est prouvée, les deux agrégats
sont rendus `Inconnu` au lieu de `0`. Le prix, le CTA marchand, le verdict et le
panneau de décision conservent leurs gardes existantes. La scène n'active aucun
reader shadow et n'ajoute aucun produit, prix ou marchand de substitution.

Qualification automatique locale :

- suite web complète et TypeScript verts ;
- build Next.js complet vert : **43 pages statiques générées**, fiche exacte à
  **7,37 kB / 162 kB First Load JS** ;
- présence explicite de la frontière `data-product-evidence="exact"`, des
  coordonnées de preuve et des trois traductions vérifiée par test ;
- composition responsive dédiée à 860 px et 560 px, mouvement d'arrivée supprimé
  avec `prefers-reduced-motion` ;
- un unique canvas différé, zéro vidéo, zéro média historique et zéro lecteur
  shadow ajouté.

La revue de production locale desktop confirme le produit réel dans le dossier
minéral, six offres comparables, cinq marchands et aucun débordement horizontal.
La revue mobile de la nouvelle couche WebGL reste à produire sur la prochaine
Preview ; elle n'est pas transformée en preuve positive.

### Offre observée historique `/produit/[id]`

L'ancienne URL d'offre rejoint le même plan `identity → proof` que le dossier
EAN, tout en annonçant explicitement un périmètre `offer`. L'image devient le
même objet physique, puis le dossier conserve dans le DOM le prix observé, le
marchand, l'état achetable ou inconnu, le verdict, la décision, le lien éventuel
vers le produit groupé et l'historique comparable.

Cette harmonisation ne transforme jamais une offre unique en comparaison. Le
marqueur achetable est dérivé de la garde `canBuy`, le CTA conserve cette même
garde, et les calculs de fraîcheur, devise et historique restent inchangés.

Qualification automatique locale :

- suite web complète et TypeScript verts ;
- build Next.js complet vert : offre historique à **5,83 kB / 159 kB First
  Load JS**, soit **+0,07 kB** de balisage sémantique et aucun delta partagé ;
- périmètre `offer`, dossier DOM, garde achetable, historique et reduced-motion
  verrouillés par test ;
- aucun fallback de prix, reader shadow ou donnée synthétique ajouté.

La revue visuelle desktop/mobile reste à rejouer avec celle du dossier exact.

### Chambre Score → Cashback `proof → decision`

Score et Cashback ne sont plus deux pages éditoriales sans continuité. Elles
partagent une chambre de décision sombre, une ligne de preuve et le même passage
vers des registres lisibles. Le Score montre ses cinq signaux comme un registre
pondéré qui converge vers les 100 points mesurables ; ce total décrit le calcul
documenté et n'est pas un score produit inventé. Cashback prolonge le plan par
trois seuils textuels — source indexée, conditions, versement — avant toute
action.

La vidéo de pièce tournante du hero Cashback a été retirée. Aucun mouvement ne
simule un avantage et aucun taux n'est généré : la page rappelle toujours que le
cumul, l'éligibilité et le versement sont conditionnels. FAQ, métadonnées,
breadcrumb JSON-LD et CTA de recherche restent présents.

Qualification automatique locale :

- suite web complète, tests de claims et TypeScript verts ;
- build Next.js complet vert : Score à **589 B / 109 kB** et Cashback à
  **515 B / 151 kB First Load JS** ;
- les deux routes exposent leur plan sémantique `decision` et partagent la même
  surface ;
- la suppression de la vidéo décorative, le registre DOM des cinq signaux, les
  trois seuils Cashback et le mode réduit sont verrouillés par test ;
- zéro lecteur shadow, zéro taux, zéro recommandation et zéro donnée de
  substitution ajoutés.

Comme pour le dossier produit, la revue visuelle desktop/mobile reste à rejouer
quand l'origine locale sera de nouveau admise par le navigateur de qualification.

### Table Outfit Studio `intent → evidence → compose`

La seule surface publique actuelle du chapitre `compose`, Outfit Studio, quitte
sa présentation de formulaire posé sur un fond illustratif. L'intention, les
offres vérifiées et la solution bornée deviennent trois stations d'un même plan,
puis le formulaire s'ouvre comme une table de travail. Les six modes, la saisie,
les exemples, l'abstention, les inconnues et les résultats utilisent toujours le
même composant et les mêmes contrats de validation.

Le changement reste strictement visuel et sémantique : le statut du module, les
requêtes réseau, la vérification d'offre fraîche, la devise, le total connu, les
liens marchands et le retour utilisateur sont inchangés. Aucune surface Fashion,
Wardrobe, Stylist, Composer ou Personal Commerce non publiée n'a été rendue
publique ni raccordée à un lecteur shadow par ce travail.

Qualification automatique locale :

- suite web complète et TypeScript verts ;
- build Next.js complet vert : Outfit Studio à **8,27 kB / 116 kB First Load
  JS**, soit **+0,25 kB** sur la route et aucun accroissement du premier
  chargement partagé par rapport à l'étape précédente ;
- plan `compose`, chemin DOM en trois stations, isolation de la table et
  suppression du mouvement en mode réduit verrouillés par test ;
- tous les états fail-closed historiques restent couverts par la suite de vérité.

La table Outfit Studio a été rejouée à **390 × 844** : plan `compose`,
chemin en trois stations et absence de débordement horizontal confirmés. Le
titre de document a aussi été normalisé pour ne plus doubler `FILON`.

### Chambre partagée `proof`

Les routes Intelligence, Comment ça marche, Transparence et Sécurité sont
maintenant quatre coupes du même espace de preuve. Leur hero est un plan sombre
commun, les informations deviennent des registres bordés au lieu de cartes
indépendantes, la méthode suit la même géométrie et la sortie vers Recherche
reprend l'orange de décision.

Cette propagation est portée par le chapitre sémantique déjà résolu dans le
shell partagé. Elle ne duplique pas les quatre pages et ne change ni leurs textes,
ni leurs métadonnées, ni leurs liens, ni leurs politiques. Les contenus restent
accessibles comme HTML ordinaire ; la géométrie ajoutée est purement CSS.

Qualification automatique locale :

- suite web complète et TypeScript verts ;
- build Next.js complet vert : Intelligence, Transparence et Sécurité à
  **186 B / 150 kB**, Comment ça marche à **2,4 kB / 153 kB First Load JS** ;
- hero, registres, étapes et reduced-motion de la chambre `proof` verrouillés
  par test ;
- aucun JavaScript, média, reader shadow ou donnée métier ajouté.

Le plan Score a été rejoué à **390 × 844** : hero, instrument de preuve,
registre DOM et largeur de page sont conformes. Les autres coupes de la chambre
restent couvertes par code, build et invariants, sans être déclarées revues par
capture.

### Utilitaires Codes promo → Reconditionné `decision`

Codes promo et Reconditionné prolongent désormais la chambre de décision au
lieu de retomber dans un gabarit éditorial générique. Le hero devient un plan de
contrôle sombre, les trois critères forment un registre continu, la FAQ reste
dans la même géométrie et la sortie orange mène à la recherche. La photographie
du reconditionné est traitée comme un objet observé ; Codes promo conserve un
plan sans média plutôt que de fabriquer une preuve visuelle.

La propagation est limitée aux routes du chapitre `decision` qui possèdent le
hero éditorial partagé. Score et Cashback gardent donc leur chambre spécialisée.
Les textes, conditions, inconnues, métadonnées, breadcrumb JSON-LD et liens sont
inchangés : aucune validité de code, garantie, économie ou éligibilité n'est
inventée.

Qualification automatique locale :

- suite web complète et TypeScript verts ;
- build Next.js complet vert : Codes promo et Reconditionné à **517 B / 151 kB
  First Load JS** chacun ;
- hero de décision, registre à trois contrôles, FAQ et reduced-motion verrouillés
  par test ;
- aucun JavaScript, média supplémentaire, reader shadow ou donnée métier ajouté.

Codes promo a été rejoué à **1440 × 900** puis **390 × 844** : hero,
copie de prudence, continuité du chapitre et absence de débordement horizontal
confirmés. Reconditionné reste couvert par le même gabarit et les tests, sans
revue par capture revendiquée.

### Champ éditorial et lecture longue `signal`

Toutes les routes publiques encore classées `signal` sont désormais raccordées
à une même matière éditoriale : À propos, Aide, Blog, Carrières, Contact,
Extension, FAQ, Partenaires, Presse, Tarifs et les contrats publics. Le hero est
un plan sombre commun ; les sections deviennent des coupes franches, les listes
d'information des registres et la sortie une transition orange. Aucun contenu
ne dépend de cette géométrie pour être compris.

L'index Blog devient une séquence de dossiers plutôt qu'une grille de cartes.
Ses six articles prolongent le même champ par une ouverture sombre puis un corps
papier conçu pour la lecture longue. Les pages légales gardent une largeur
bornée, une typographie calme et tous leurs titres, liens et dates. Le formulaire
Contact conserve exactement son transport et ses états ; seul son plan visuel
est raccordé.

Qualification automatique locale :

- suite web complète, TypeScript et build Next.js **47 pages** verts ;
- routes éditoriales principales à **180–518 B / 150–151 kB**, Contact à
  **2,05 kB / 152 kB**, articles à **329 B / 108 kB First Load JS** ;
- les quatorze entrées à hero partagé, l'index Blog, la lecture longue, les
  contrats, les formulaires et reduced-motion sont verrouillés par test ;
- aucune route, donnée métier, requête, vidéo, canvas, WebGL ou reader shadow
  ajouté.

Le Blog a été rejoué à **390 × 844**. Cette passe a révélé qu'un
`Reveal` englobant un registre très long pouvait rester invisible au premier
viewport : son seuil est maintenant adaptatif, plafonné à 96 px visibles, tout
en conservant le ratio historique de 16 % pour les blocs courts. La première
image et le premier dossier apparaissent désormais sous le hero sans premier
geste artificiel ; le mouvement réduit reste inchangé.

### Sortie globale `continue`

Le pied de page devient le dernier plan de l'expérience plutôt qu'un appendice
institutionnel. La newsletter ouvre la scène, les quinze chemins publics forment
un registre navigable, les contrats restent distincts et les limites d'accès et
d'affiliation restent visibles. La coordonnée de sortie est localisée en
français, néerlandais et anglais.

Le composant et le transport Newsletter sont inchangés. La composition reste
responsive en trois, deux puis une colonne ; toutes les cibles tactiles gardent
au moins 44 px et les transitions sont neutralisées en mouvement réduit.

Qualification automatique locale :

- suite web complète, TypeScript et build Next.js **47 pages** verts ;
- aucun delta JavaScript de route ou de premier chargement ;
- continuité de sortie, registre de liens, newsletter et reduced-motion
  verrouillés par test ;
- mentions légales, transparence, affiliation et actions existantes conservées.

La sortie globale a été rejouée à **390 × 844** sur le parcours Score :
registre de 22 liens, formulaire Newsletter, mentions et continuité jusqu'au CTA
persistant visibles, sans débordement horizontal.

### Propagation fermée à exécuter

1. **PASS local** — rendre conforme le LCP du plan initial ;
2. **PASS local** — transformer la home en plan `signal → identité`, avec un
   delta JavaScript borné et mesuré ;
3. **PASS local** — faire de recherche + catalogue un même espace `market`, avec
   la requête comme objet continu ;
4. **PASS code/build ; revue visuelle EAN/offre à rejouer avec donnée locale** — raccorder le dossier EAN et
   l'offre historique au chapitre `identity → proof`, en conservant EAN,
   marchands, dates, périmètre exact et unknown dans le DOM ;
5. **PASS code/build ; Score mobile revu, Cashback à rejouer** — raccorder score/cashback aux
   plans `proof → decision`, sans activer de lecteur shadow ;
6. **PASS code/build pour la surface publique Outfit Studio ; autres readers
   volontairement non activés** — raccorder Fashion, Wardrobe, Stylist, Composer
   et Personal Commerce au chapitre `compose` uniquement lorsqu'une surface
   publique autorisée existe, avec leur mode efficace toujours disponible ;
7. **PASS code/build ; Codes promo desktop/mobile, Marchands mobile, Blog mobile
   et sortie mobile revus** — raccorder Marchands, Rayon,
   les quatorze routes éditoriales, les six guides et la sortie globale aux
   chapitres `market`, `signal` et `continue` ;
8. **PASS automatique pour tests, TypeScript, build, budgets et invariants de
   vérité ; PARTIAL visuel sans débordement sur les vues rejouées** — rejouer clavier, desktop et mobile dans le
   navigateur de qualification avant canary public.

## Validation créative et début de propagation finale — 3 septembre 2026

La Preview Vercel non indexée du laboratoire a été revue par le fondateur. La
direction a été explicitement validée comme prometteuse et la gate « laboratoire
uniquement » est levée. Cette validation autorise la poursuite de l'intégration
locale ; elle ne constitue ni une fusion ni une activation production.

La première propagation emploie la séquence caméra réelle dans le plan home
existant. Elle conserve le HTML de preuve complet et ajoute le volume comme une
couche facultative :

- import R3F/Three.js client différé après le contenu critique ;
- refus automatique sur mouvement réduit, économie de données, réseau 2G,
  mémoire déclarée inférieure à 4 Go ou absence WebGL ;
- frontière d'erreur locale : un échec du moteur restaure le plan DOM/CSS sans
  affecter la recherche ;
- progression continue de la caméra à partir de la timeline du chapitre, et non
  quatre remplacements d'écran ;
- composition portrait dédiée sous 820 px ;
- produit exact choisi depuis une fiche détaillée courante ; si cette preuve ne
  franchit pas les gates, le volume représente honnêtement l'abstention ;
- le noyau générique sphérique du laboratoire est remplacé par un dossier
  minéral rectangulaire, cohérent avec la table de preuves et l'identité FILON.

Qualification initiale : suite web et TypeScript verts ; build complet de 47
routes vert ; home à **8,42 kB / 117 kB First Load JS**, le moteur 3D restant
dans un chunk différé. La revue locale a confirmé les plans 01, 03 et 04, la
continuité de l'abstention et l'absence d'erreur navigateur. La qualification
avec un produit exact, la matrice mobile et les mesures de performance de la
nouvelle intégration restent à produire avant nouvelle Preview finale.

Le deuxième raccordement local porte la continuité `identity → proof` sur le
dossier EAN. Lorsqu'une image et une comparaison courante existent réellement,
le même dossier minéral effectue une mise au point macro puis un orbit court ;
le nombre de plaques actives vient exclusivement des offres qualifiées. Cette
scène ne se charge qu'après le contenu critique et s'arrête après **3,8 s**.
Sans image, comparaison, capacité WebGL ou mouvement autorisé, aucun canvas
n'est monté et l'image DOM originale reste visible. Le moteur de capacité,
l'arrêt sur erreur et la composition mobile sont mutualisés avec la home plutôt
que réimplémentés par route.

Après revue fondatrice de la Preview, l'objet générique a été définitivement
écarté : l'image catalogue devient une texture de la matière WebGL et reste le
même acteur entre la home et le dossier EAN. La frontière d'erreur conserve
l'image DOM en secours. La suite web complète, TypeScript et le build propre
sont verts ; le build final mesure la home à **8,5 kB / 117 kB** et le dossier
exact à **7,37 kB / 162 kB First Load JS**. Les plans `CHAOS` et `DÉCISION`,
l'état `unknown`, le produit exact et la console du build local ont été revus
sur desktop. La nouvelle Preview mobile/non indexée reste le prochain gate ;
aucune promotion production n'est autorisée par cette qualification locale.

Le graphe dynamique de la scène représente environ **237 Ko gzip** répartis en
cinq chunks et n'entre pas dans le premier chargement des routes. Son montage
reste retardé de 1,5 à 1,8 seconde, borné à un seul canvas par surface et absent
des profils contraints. Le budget initial de **2 Mo mobile / 4 Mo desktop** est
donc respecté avec une marge nette ; cette mesure de bundle ne remplace pas les
Core Web Vitals terrain de la Preview.

### Qualification caméra déclarative et garde 45/30 fps — 3 septembre 2026

La caméra finale n'est plus une collection de mutations dépendantes du taux de
rafraîchissement. Les quatre plans `market → identity → proof → decision`, leurs
projections, cibles, focales et trajectoires sont déclarés dans un même système.
Le mouvement emploie un amortissement temporel ; les transitions CSS partagent
les tokens cinématique, mécanique et doux de FILON.

Le runtime mesure désormais une fenêtre WebGL réellement animée. Sous **45 fps**,
il réduit d'abord DPR, ombres et fragments ; si la fenêtre suivante reste sous
**30 fps**, la scène se ferme et rend le tableau DOM/CSS. Un onglet masqué ne
peut pas déclencher artificiellement cette fermeture. Les boucles de la scène
signature et du dossier produit s'arrêtent aussi dès que leur surface quitte
l'écran ; la reprise conserve la progression déjà atteinte.

La qualification locale avec la preuve serveur courante a confirmé :

- desktop **1 280 × 720** et portrait **390 × 844** : un canvas, qualité `full`,
  aucune largeur excédentaire ;
- produit exact NANKANG, **EAN 4717622052664**, **6 offres / 5 marchands** : même
  texture produit dans le laboratoire et le dossier EAN ;
- correction d'un arrêt d'orbite sur la tranche : le dossier exact revient sur
  un cadrage frontal lisible avant de s'immobiliser ;
- profil desktop volontairement contraint : dégradation automatique `full →
  degraded` observée, fenêtre d'initialisation immersive mesurée à **0 ms** de
  tâche longue, puis arrêt coopératif confirmé hors écran (`Pause → Rejouer`) ;
- suite web et TypeScript verts ; build réel de **47 routes** vert ; home
  **8,76 kB / 117 kB**, laboratoire **11,4 kB / 114 kB**, dossier exact
  **7,62 kB / 162 kB** au premier chargement.

Les avertissements de cache sitemap au-delà de 2 Mo restent antérieurs et sans
rapport avec le graphe immersif. Cette qualification demeure un candidat Preview
non indexé ; elle n'autorise ni fusion ni promotion production.
