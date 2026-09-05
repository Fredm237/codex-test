# FILON — Direction cinématographique retenue

Date : 2026-09-05

Statut : **GO fondateur — prototype final-grade autorisé**

## Idée en une phrase

Un produit recherché traverse le bruit du commerce, reste reconnaissable pendant
que FILON sépare le comparable du trompeur, puis le monde devient directement
l'interface qui permet de décider.

## Histoire définitive

### 1. L'entrée

Un ordinateur repose seul sur une table dans un intérieur européen lumineux.
Aucun personnage n'est visible. L'écran contient une recherche FILON et un
produit réel issu de la preuve serveur.

La caméra s'approche et traverse l'écran. L'ordinateur est un portail, pas le
produit vedette.

### 2. Le marché

De l'autre côté apparaît une ville inspirée de Bruxelles : rue, façades,
vitrines et profondeur réelle. Le même produit apparaît chez plusieurs
marchands. Les prix, promotions, variantes et conditions se multiplient.

Le visiteur doit comprendre sans texte technique : le marché offre beaucoup,
mais il ne rend pas les offres automatiquement comparables.

### 3. L'intervention FILON

FILON n'apparaît pas comme un robot, un personnage ou un badge. Son action est
la transformation physique du monde :

- les exemplaires du même produit convergent ;
- les variantes incompatibles sont dirigées ailleurs ;
- les offres non admissibles perdent leur place dans la composition ;
- les preuves fiables gagnent densité, stabilité et lumière ;
- une inconnue reste visible comme inconnue.

Le même produit reste identifiable pendant toute l'opération.

### 4. La décision

Le mouvement ralentit. La ville se calme et se réduit autour du produit exact
et de quelques offres réellement comparables.

Les lignes de rue deviennent les séparateurs du comparateur. Les vitrines
deviennent les surfaces des offres. Le produit 3D et son image DOM se
superposent. Le monde est déjà la fiche FILON : aucun fondu noir, loader ou
changement de page.

## Message compris sans explication

> Vous cherchez. Le marché vous embrouille. FILON vérifie. Vous décidez.

## Produit variable, histoire stable

Le hero n'est jamais codé en dur. Il vient de la recherche ou du groupe produit
réel : chaussure, poussette, ordinateur, meuble, parfum, appareil ménager,
vêtement ou autre verticale. Son image, son échelle et sa mise en scène
s'adaptent ; la grammaire narrative reste la même.

Si aucune preuve produit exacte et fraîche n'est disponible, la scène s'abstient
et invite à lancer une recherche. Aucun prix, marchand, verdict ou produit de
secours n'est fabriqué.

## Storyboard — desktop

| Temps | Plan | Ce qui arrive | Caméra | Copy maximale |
|---|---|---|---|---|
| 0–2,5 s | Intérieur | Ordinateur seul, produit réel dans l'écran. | 50 mm, travelling avant. | « Tout commence par une recherche. » |
| 2,5–4,5 s | Passage | La caméra traverse l'écran ; le produit reste devant elle. | 50→28 mm, accélération courte. | Aucun texte. |
| 4,5–8 s | Ville | Les vitrines et offres se multiplient autour du même produit. | 24 mm wide puis tracking. | « Le marché répond. Tout n'est pas comparable. » |
| 8–11,5 s | Tri | Mauvaises variantes séparées, offres admissibles convergentes. | 85 mm macro puis orbit 35 mm. | « FILON vérifie ce qui correspond vraiment. » |
| 11,5–14 s | Calme | La densité et le mouvement diminuent. | Retour axial, décélération. | Aucun texte. |
| 14–17 s | Interface | Rue, vitrines et produit deviennent la vraie surface Product. | Zénithal orthographique. | « Comparez ce qui peut l'être. » |

## Storyboard — mobile

Le mobile conserve la même causalité avec trois plans : écran-portail, rue
verticale de trois vitrines maximum, puis fiche une colonne. Aucun panoramique
horizontal obligatoire, aucune interaction gyroscopique nécessaire et aucune
occultation prolongée du produit.

## Mouvement réduit

Trois tableaux accessibles : recherche dans l'écran, marché divergent, décision
finale. Le produit garde la même position de référence et l'interface finale
reste immédiatement utilisable.

## Invariants de production

- Recherche, Demander à FILON et Passer restent accessibles pendant le récit.
- Le DOM contient toujours le produit, les offres, la provenance et les actions.
- WebGL est un enrichissement différé, borné et désactivable.
- La ville n'est pas décorative : chaque transformation correspond à une action
  FILON compréhensible.
- Aucun vocabulaire `LABORATOIRE`, `P19`, `PLAN`, `SHADOW` ou moteur n'entre dans
  l'expérience utilisateur finale.
- Aucun lecteur V2 non promu n'est exposé par cette scène.

## Gate suivant

Construire cette histoire une seule fois dans `/laboratoire/experience`, la
qualifier sur desktop, mobile, mouvement réduit, accessibilité et performance,
puis la montrer avant toute propagation à Home, Search ou Product.
