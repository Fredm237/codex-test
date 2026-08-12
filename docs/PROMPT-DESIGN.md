# Prompt de direction — FILON

Prompt de référence à coller en tête de toute session qui touche au design de
FILON. Il condense ce qui a été **observé et mesuré**, pas supposé : le compte
Instagram `w.wearebrand` regardé image par image, dix-sept expériences web 3D
capturées après exécution de leur JavaScript, et une série de pièges techniques
payés comptant.

Tout ce qui suit est impératif. Les sections « Ce qui est interdit » et
« Pièges » viennent d'erreurs réellement commises sur ce dépôt.

---

## 1. Le monde

Tu conçois pour **FILON**, copilote d'achat belge francophone. 799 435 offres,
154 marchands partenaires. Sa promesse tient dans le titre de sa page
d'accueil : *« Est-ce vraiment le bon moment pour acheter ? »*

La référence visuelle est le compte Instagram **`w.wearebrand`**, observé
directement. Elle a remplacé phia.com — le blanc pur, la serif de titrage et
les pilules appartiennent à l'ancienne identité et ne reviennent jamais.

Ce que les plans donnent, et qui fonde chaque valeur :

- **Sous-exposition assumée.** Les noirs dominent le cadre. La lumière est rare
  et vient par flaques. On ne peint pas un fond sombre : on peint une obscurité
  que la lumière troue.
- **Béton banché, pas gris bleu.** La matière est chaude, presque taupe, avec
  ses trous de banche visibles. Toute la grise neutre est décalée vers le rouge.
- **Une seule couleur** : l'ambre des spots sur le béton, autour de 2700 K.
- **Le vert vient du vivant** — feuillage tropical en contre-jour. Il remplace
  le turquoise, qui jurait en ambiance chaude.
- **Géométrie orthogonale.** L'architecture est à angles vifs. Rayons de 2 à
  6 px. La pilule a disparu, sauf en pastille — clin d'œil au bandeau de
  sous-titre des Reels, à 10 px.
- **La lumière remplace l'ombre portée.** Sur fond sombre une ombre ne se voit
  pas : le relief vient d'une arête haute qui capte la lumière, et de halos.
- **Une seule grotesque, en bas de casse, point final.** Le mot-signe
  « wearebrand. » ne dit rien d'autre.
- **Alternance franche sombre/clair, écran par écran.** Les sites montrés dans
  les Reels ne sont pas sombres de bout en bout : le burger bascule sur fond
  blanc pour sa vue éclatée, le site de fret enchaîne hero noir, texte sur
  crème, camion sur noir. Le changement de fond découpe le récit.

## 2. Les jetons — ne pas y toucher

Tout vit dans `filon-web/app/tokens.css`, où **chaque valeur est justifiée par
ce qui a été vu**. Tu lis ces jetons, tu n'en inventes pas.

```
Fond            #0e0c0b   béton dans l'ombre, chaud
Surface         #16130f   ·  levée #1e1a16
Texte           #e4ded4   béton en pleine lumière
Ambre           #c89544   cœur de la flaque — SEULE couleur d'accent
Feuillage       #8fb072   gain, économie constatée
Terre cuite     #e59480   alerte — jamais un rouge signal
```

Deux densités, une seule identité :

- **Vitrine** — respiration large, sections de 100 à 160 px, texte en 300.
- **`[data-density="catalogue"]`** — contraste au maximum, surfaces plus
  détachées, espace vertical divisé par deux. Même béton, sous une lampe de
  travail plutôt qu'un spot d'accueil.
- **`[data-tone="light"]`** — le béton en plein soleil. Ce n'est pas « le thème
  clair » : c'est la même matière sous une autre exposition.

Interdiction d'ajouter une couleur, de changer un rayon, de réintroduire une
serif de titrage ou une pilule.

## 3. La technique — le photoréalisme vient du rendu hors ligne

**C'est le point le plus important, et le plus coûteux à réapprendre.**

Un site premium ne calcule pas ses images en temps réel. Il **scrubbe une
séquence rendue hors ligne** : le film est calculé sans contrainte de durée,
découpé en images, et le défilement choisit laquelle dessiner dans un
`<canvas>`. C'est la méthode des pages produit d'Apple.

Demander à la carte graphique du visiteur de fabriquer en seize millisecondes
ce qu'un moteur de rendu met des minutes à produire par image est un combat
perdu d'avance, quel que soit l'éclairage. Deux tentatives en temps réel ont
été construites puis supprimées de ce dépôt pour cette raison.

L'outillage existe et se réutilise :

```bash
python3 .claude/agent/sequence.py film.mp4 --sortie public/seq/<nom> --images 64
python3 .claude/agent/lecteur.py --chapitre "Titre|Suite:public/seq/<nom>:0.0" --sortie page.html
```

Réglages, et leurs raisons : **64 à 72 images** — au-delà de 80 l'œil ne
distingue plus rien au défilement, en deçà de 40 le mouvement redevient
saccadé. **1100 à 1280 px** de large — l'image est recadrée en `cover`.
**Qualité 70 à 72** — le point où l'artefact reste invisible sur une image
sombre, le grain masquant le reste.

Le composant `SequenceScroll` précharge **toutes** ses images avant le premier
rendu : une séquence qui se charge en défilant saute, et le saut se voit.

**WebGL temps réel n'est autorisé que pour l'interaction** — manipuler un
objet, réagir au curseur. Jamais pour produire une image que le visiteur
regarde passivement.

## 4. La grammaire, page par page

### Accueil — la vitrine

Hero plein écran, puis **alternance franche** de chapitres. Un chapitre =
100 vh, une idée, un titre de trois à cinq mots, rien d'autre. La séquence
pilotée au défilement porte le propos central : le prix ne change pas, la
lumière change, et à la fin ce n'est plus la même décision.

Le chiffre géant (`.fx-chapter-figure`) vient du catalogue et se lit à trois
mètres. Il n'est jamais rédigé à la main.

### Catalogue — 799 435 offres

`[data-density="catalogue"]`. Ici l'atmosphère cède : **lisibilité et vitesse
de balayage décident**. Contraste au maximum de la palette, surfaces plus
détachées du fond, espace vertical resserré, chiffres tabulaires.

Pas de séquence, pas de canvas, pas d'effet au défilement : c'est une page
qu'on balaie, pas un film qu'on regarde. La cohérence vient de la palette et
de la géométrie, pas du dispositif.

Les vignettes produit gardent leur plaque claire : les visuels marchands sont
détourés sur blanc, et un fond sombre les casserait.

### Fiche produit

Le produit est le sujet, seul, sous un spot. Autour, les offres des marchands
rangées en liste dense. L'écart de prix est l'information principale — il se
lit avant le reste.

### Pages éditoriales

Ton clair (`[data-tone="light"]`) autorisé, largeur de texte à 65 caractères,
un seul niveau de titre par section. Pas de séquence : le texte se lit, il ne
se fait pas raconter.

## 5. Les éléments

| Élément | Règle |
|---|---|
| Bouton principal | ambre plein, texte `#080706`, rayon 4 px, hauteur 52 px |
| Bouton secondaire | transparent, arête claire, jamais de fond |
| Bouton sur bloc sombre | l'inverse : surface claire, texte sombre |
| Carte | fond surface, arête haute éclairée, ombre ambiante large, rayon 6 px |
| Pastille / filtre | rayon 10 px — le seul arrondi généreux du système |
| Filtre actif | s'allume en ambre plein, texte sombre |
| Champ | rayon 4 px, hauteur 56 px, fond surface, arête forte |
| Surtitre | seule majuscule du système, interlettrage 0,16 em |
| Titre | grotesque en 200-300, interlettrage −0,035 em, jamais de gras |
| Emphase | un cran plus léger + ambre. **Jamais d'italique serif** |
| Mot-signe | bas de casse, point final ambré |
| Séparation | arête éclairée, jamais un trait noir |
| Focus | anneau ambré, jamais retiré |

## 6. Ce qui est interdit

- **Les primitives grises.** Cubes et cylindres en matériau plat ne seront
  jamais premium. Erreur commise deux fois sur ce dépôt.
- **L'objet décoratif au centre d'une page.** Les réussites observées sont des
  **lieux habités** — un paysage avec un abri, un sous-sol avec sa borne
  d'arcade. Ce qui fait la présence, ce sont les traces d'usage.
- **Le monde trop grand.** Une étendue vide coûte en chargement et ne donne
  rien à regarder. Igloo tient dans une vallée, basement dans une pièce.
- **La navbar rescapée** par-dessus une expérience immersive.
- **`ScrollControls`** de drei : il détourne le défilement, casse l'ancrage
  clavier et sort le contenu du DOM. Canvas fixe + DOM qui défile + Lenis.
- **Les dégradés**, le texte en dégradé, le `background-clip: text`. La marque
  est mate.
- **Le noir + néon violet + particules.** Lu comme « futuriste », pas comme
  premium.
- **Les sphères, diamants, or brillant** — ancienne identité, explicitement
  rejetée.
- **La 3D pour la 3D.** Test décisif : si la page est aussi bonne sans, le
  dispositif est mauvais.

## 7. Les données — non négociable

- **Ne jamais fabriquer un chiffre, un marchand ou un exemple.** Une section
  sans données ne s'affiche pas ; elle ne se remplit pas d'un cas inventé pour
  faire tourner une animation. C'est la règle qui structure `lib/proof.ts` et
  chaque composant qui suit.
- **Ne jamais citer un marchand non partenaire.** Fnac, Amazon, Cdiscount,
  Boulanger, Darty n'en sont pas.
- Les chiffres réels utilisables viennent du catalogue : nombre d'offres, de
  marchands, prix minimum et maximum constatés, nombre de marchands par article.

## 8. Accessibilité — mesurée, pas déclarée

- Contraste **4,5:1 minimum**, vérifié au navigateur sur les deux tons.
- Cibles tactiles **44 px** sous `@media (pointer: coarse)`, étendues par
  pseudo-élément pour ne pas déplacer le texte. Seule exception admise : les
  liens en ligne dans un paragraphe.
- Anneau de focus visible sur tout élément interactif, jamais supprimé.
- **`prefers-reduced-motion`** : la séquence ne se monte pas du tout, une image
  fixe et les titres empilés la remplacent. La page reste entière sans elle.
- Un `h1` par page, `alt` sur toute image porteuse de sens, étiquette sur tout
  champ.
- Corps à 16 px minimum sur mobile.

## 9. Pièges techniques — payés comptant

- **`overflow-x: hidden` casse `position: sticky`** pour tous les descendants,
  parce qu'il fait de l'élément un conteneur de défilement. Utiliser
  **`overflow-x: clip`**, qui coupe pareil sans créer ce conteneur. La règle
  fautive vivait dans un bloc « fix mobile » chargé après `globals.css`, donc
  elle écrasait silencieusement la correction faite au bon endroit.
- **Un ancêtre avec `transform`** (Framer Motion) casse aussi le `sticky`.
- **404 ≠ 500.** Une API injoignable ne doit jamais produire un `notFound()` :
  un 404 dit à Google « retire cette page de l'index », un 5xx dit « repasse
  plus tard ». Une panne de base a suffi à faire désindexer tout le catalogue.
- **Le port du proxy est dynamique** : lire `$HTTPS_PROXY`, ne jamais coder un
  port en dur.
- **Le ffmpeg livré avec Playwright est un build minimal** qui refuse un mp4
  ordinaire. Utiliser `imageio-ffmpeg`.
- **`next start` sert les fichiers publics figés au build** : ajouter une image
  dans `public/` exige un rebuild, et ne pas tuer le build en cours.

## 10. Contrôle avant de livrer

Rien n'est « vérifié » sans mesure. Avant de déclarer une page finie :

```bash
cd filon-web && npm run build          # doit compiler
cd filon-backend && python -m pytest -q # 342 tests attendus
```

Puis, au navigateur : contraste sur les deux tons, cibles tactiles sous
pointeur grossier, anneau de focus au clavier, absence de débordement
horizontal, et rendu sous `prefers-reduced-motion`.

Une commande qui rend 0 n'est pas une preuve. Demande-toi toujours : *est-ce
vraiment le résultat attendu, ou seulement l'absence d'erreur ?*
