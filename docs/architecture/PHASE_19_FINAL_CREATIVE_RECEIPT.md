# FILON — Phase 19 Final Creative Receipt

- Date : **4 septembre 2026**
- Branche : **`codex/filon-immersive-production`**
- Candidat local assemblé : **`3e8c08a`**
- Dernier candidat Preview publié : **`19658bfe3846fe336cd9345d6c6ea5fe7658ddf5`**
- Preview immuable : **`https://codex-test-ik4bmrd5m-teamfilon.vercel.app/`**
- Indexation : **interdite** (`x-robots-tag: noindex`)
- Décision : **GO ASSEMBLAGE LOCAL / VALIDATION PREVIEW REQUISE / NO-GO PRODUCTION**

## 1. Final creative receipt

La direction **B — chorégraphie de preuve** est le langage propriétaire retenu.
FILON n'est pas traité comme une collection de pages animées : le même produit
traverse physiquement `market → identity → proof → decision`, tandis que le
DOM conserve la vérité, les contrôles et l'accessibilité.

Les quatre moments signature sont exécutés dans le laboratoire :

1. **Champ marchand** — plan large et offres physiques autour du produit exact ;
2. **Aperture d'identité** — macro, profondeur et continuité du même produit ;
3. **Recuit de preuve** — seuls les fragments admissibles changent de matière ;
4. **Sceau de décision** — resserrement d'échelle et stabilisation du plan.

La différence avec la fondation DOM/CSS est sémantique : la caméra choisit le
niveau de lecture, l'occlusion matérialise le bruit marchand et le changement de
matière distingue une offre brute d'une preuve admissible. La 3D peut être
retirée sans perdre les faits, mais pas sans perdre cette explication spatiale.

## 2. Final visual QA

| Surface | Desktop | Mobile 390 × 844 | Vérité / continuité |
|---|---|---|---|
| Home | quatre plans réellement exécutés et objet continu | composition portrait autonome | unknown conservé si preuve absente |
| Laboratoire | wide → macro → orbit → plan | trois états bornés, 7 fragments | produit et offres issus du ledger DOM |
| Recherche | flux SSE terminal et passage vers preuve | aucune largeur excédentaire | aucune carte sans résultat terminal réel |
| Catalogue / Marchands / Rayon | espace `market` continu | titres et filtres accessibles | aucun fallback marchand ou offre |
| Produit EAN | produit exact et offres comparables | canvas différé, objet et offres lisibles | même EAN, devise et marchands |
| Offre historique | paysage prix-temps réel | curseur et tableau non recouverts | observations invalides exclues |
| Score / Cashback / Codes / Reconditionné | silence éditorial `decision` | composition sans recadrage cassé | aucune recommandation shadow |
| Intelligence / Méthode / Transparence / Sécurité | chambre `proof` cohérente | aucune largeur excédentaire | registres explicites |
| Outfit Studio | espace `compose` | table interactive protégée | données locales et gardes existantes |

La matrice mobile transversale couvre aussi Blog et Contact. Toutes les routes
observées tiennent dans un document de **384 px** pour un viewport de **390 px**.
Marchands et Rayon possèdent localement une unique zone principale.

### FINAL_MOBILE_QA

Le parcours assemblé a été rejoué sur un viewport **390 × 844** : Home,
Recherche, Catalogue, fiche produit EAN, preuve transactionnelle, Score et
Outfit Studio. Chaque surface tient dans **384 px** de document, sans largeur
excédentaire, sans label de laboratoire et sans canvas imposé sur les surfaces
de densité faible. La fiche produit active un unique canvas différé ; Recherche,
Catalogue, Score et Outfit Studio restent DOM/CSS.

### Preuves vidéo à vitesse réelle

Deux captures locales, exclues du dépôt, matérialisent le parcours assemblé :

- `FILON_PHASE19_FINAL_DESKTOP.mp4` — **22,4 s**, **1 280 × 720**, 224 images ;
- `FILON_PHASE19_FINAL_MOBILE.mp4` — **19,0 s**, **390 × 844**, 190 images.

Elles parcourent `Home → Search → Catalogue → Product → Proof → Decision`.
L'orientation a été contrôlée après encodage sur les deux fichiers : aucun plan
n'est retourné. Les coupes inter-routes servent uniquement la revue ; les
caméras Home et Produit restent rendues par le moteur réel.

Ces captures documentent le premier assemblage `f4856ae`. Le remplacement de
l'ancien objet catalogue par la sélection éditoriale dynamique `1ba8656` est
qualifié directement dans le navigateur ; une prochaine capture Preview devra
utiliser le candidat exact `3e8c08a`, qui ajoute la réécriture publique.

## 3. Final performance receipt

Mesures du build de production local au niveau de la scène montée :

| Profil | LCP | CLS | INP | Longue tâche immersive | Débordement |
|---|---:|---:|---:|---:|---:|
| mobile 390 × 844 | 700 ms | 0 | non exposé | 0 ms | 0 px |
| desktop 1 280 × 720 | 700 ms | 0 | 184 ms | 0 ms | 0 px |

- home : **121 kB** de premier chargement ;
- laboratoire : **118 kB** de premier chargement ;
- graphe Three.js différé, DPR borné et rendu à la demande ;
- aucun chargement du tunnel historique de 1 200 images ;
- build Next.js : **47 routes** ;
- suite web, TypeScript et build : verts.

Les Core Web Vitals terrain restent un gate du canary. Aucune valeur locale
n'est présentée comme une mesure terrain de production.

## 4. Final accessibility receipt

- canvas `aria-hidden` et non interactif ;
- texte, preuves, prix, états et actions conservés dans le DOM ;
- sortie clavier commune au shell, à la home et au laboratoire ;
- transfert de focus vers une destination `tabIndex=-1` ;
- contrôles du laboratoire accessibles par boutons et curseur ;
- cibles tactiles d'au moins 48 px dans la composition mobile ;
- `prefers-reduced-motion`, faible capacité ou échec WebGL : même histoire en
  composition statique ;
- perte du contexte GPU détectée sur le canvas actif : restauration navigateur
  autorisée, boucle 3D démontée et retour immédiat au récit DOM qualifié ;
- aucun scroll prison et aucun contenu critique retardé par la scène.

Le clic clavier du lien transformé hors écran n'a pas pu être synthétisé de
manière fiable par l'outil navigateur. Son comportement est verrouillé par le
code, les tests et le build ; ce point devra être rejoué sur le canary avec un
navigateur assistif réel.

## 5. Truth and fail-closed receipt

- **0** produit, offre, marchand, prix, devise, stock ou verdict synthétique ;
- produit exact conservé seulement si son identité est prouvée ;
- offres visibles seulement si prix, devise, stock et fraîcheur sont admissibles ;
- unknown et abstention sont des sorties finales légitimes ;
- aucun lecteur shadow, writer ou flag métier activé par Phase 19 ;
- la recherche locale attend le terminal serveur sans fabriquer de réponse ;
- les références de modèle exactes sont bornées avant pagination dans le
  candidat backend local.

Qualification backend locale : **2 643 tests passent**, **3 sont ignorés** ;
le test de transport OTLP qui ouvre un port loopback passe isolément dans
l'environnement autorisé.

## 6. CID reference gap report

Le gap initial `caméra fixe / profondeur simulée / matière inchangée` est fermé
sur la Home et la fiche Produit, en plus du laboratoire. Le
contraste entre **cinéma bref** et **silence éditorial** reste volontaire :
Recherche et Décision ne deviennent pas des films.

Le produit phare n'est plus déterminé par le seul volume marchand, qui pouvait
mettre durablement un pneu en avant. La Home choisit désormais, parmi des
familles réelles technologie/fashion, un produit illustré, non accessoire,
comparé par au moins deux marchands et présentant un écart de prix réel. La
sélection tourne quotidiennement sans EAN figé. L'image originale reste la
preuve DOM ; sa copie WebGL est admise uniquement depuis une courte liste de
CDN publics, avec type image et taille maximale de 512 kB. Tout échec conserve
le dossier produit lisible et replie seulement le canvas.

La Home suit désormais une hiérarchie de lecture grand public : bénéfice
immédiat, recherche, prix, puis explication. Les termes internes tels que
`périmètre`, `identité exacte`, `données live` et `devise supportée` ont été
remplacés par des formulations concrètes dans les trois langues. Les règles
fail-closed restent inchangées derrière cette simplification.

Le gap encore ouvert est opérationnel, pas créatif : le candidat local le plus
récent, incluant le repli sur perte du contexte GPU, n'est pas encore une
Preview publiée et les Core Web Vitals terrain du futur canary ne sont pas
disponibles.

## 7. État de publication exact

La Preview publique non indexée est **Ready** au commit distant `19658bf`. Le
candidat local est au commit `3e8c08a` et contient les corrections ultérieures
de structure HTML, terminaison SSE, focus clavier, qualification performance,
bornage backend, séparation stricte entre laboratoire et surfaces finales et
contraste explicite des offres et du panneau de preuve sur le dossier sombre.
Il retire également le rail de storyboard de la Home et neutralise ses
identifiants publics : l'utilisateur vit les quatre plans sans instrumentation
`P19`, `PLAN`, `LABORATOIRE` ni légende de démonstration.

Ces commits locaux ne sont pas inclus dans l'autorisation nominative précédente,
limitée aux cinq commits `9801f1f..b961303` et à leurs seize fichiers. Ils ne
sont donc ni poussés, ni déployés. La branche distante a en outre une histoire
de republication différente ; elle ne doit pas être écrasée par un push forcé.

## 8. Canary plan

Le passage Preview → canary exige simultanément :

1. publication sans secret du candidat exact et construction Vercel terminale ;
2. `noindex` et protection maintenus pendant la qualification ;
3. matrice desktop/mobile sur les routes critiques, sans erreur navigateur ;
4. recherche réelle terminée avant le budget client ;
5. clavier, mouvement réduit, échec WebGL et navigation sans JavaScript testés ;
6. LCP ≤ 2,5 s, INP ≤ 200 ms, CLS ≤ 0,1 au p75 du trafic canary ;
7. aucune longue tâche immersive > 200 ms et aucune boucle GPU hors écran ;
8. **0** divergence entre ledger DOM et scène ;
9. aucune activation de reader/writer shadow ;
10. validation visuelle finale sur vitesse normale.

## 9. Rollback plan

- conserver le déploiement Vercel stable précédent ;
- promouvoir le nouveau build par référence immuable, jamais en écrasant le
  déploiement de repli ;
- en cas de régression, repointer le trafic vers le déploiement stable ;
- l'échec ou la désactivation WebGL laisse le DOM complet utilisable ;
- aucune migration destructive ni modification de données n'est requise par
  l'expérience visuelle ;
- le bornage backend reste un lot séparable et peut être retiré sans toucher à
  la scène.

## 10. Go / No-Go

**GO ASSEMBLAGE LOCAL** : direction créative, continuité produit, caméra,
matière, mobile, performance locale, accessibilité structurelle, fail-closed et
parcours assemblé sont qualifiés sur le candidat exact `3e8c08a`. Les vidéos
existantes restent le reçu du candidat précédent et doivent être renouvelées
sur ce commit avant la prochaine validation Preview.

**VALIDATION PREVIEW REQUISE** : conformément au mandat, le dernier candidat
local n'est pas publié avant revue des vidéos assemblées. **NO-GO PRODUCTION** :
la matrice canary n'est pas rejouée sur ce commit exact et les mesures terrain
p75 ne sont pas acquises. Aucun autre blocker créatif ou d'intégrité n'est
ouvert.

## 11. Frontière laboratoire / expérience finale

Le laboratoire est désormais une surface de construction et de qualification,
pas une route du produit final. Son accès est ouvert par défaut uniquement en
développement et sur les Preview Vercel. En build de production, sans
autorisation explicite, `/laboratoire/experience` répond **404**. Les en-têtes
`noindex` restent actifs lorsqu'il est ouvert pour une revue.

Les primitives réutilisables `R3F / Three.js` ont quitté le dossier
`components/immersive-lab` pour
`components/experience/signature`. La Home et le dossier Produit consomment ce
moteur de production neutre ; le laboratoire ne fait plus que l'orchestrer pour
les essais. Les caméras perspective et orthographique, la continuité du même
produit, l'orbite de preuve, les changements de matière, la lumière, le brouillard
et la composition finale sont conservés.

Les marqueurs `FILON / PLAN`, `FILON / MARCHÉ`, `FILON / IDENTITÉ`,
`FILON / DÉCISION`, `FILON / COMPOSER` et la terminologie de démonstration ont
été retirés des surfaces utilisateur. Un test transversal interdit leur
réapparition et interdit toute dépendance d'une surface de production vers le
dossier laboratoire.

Qualification locale du candidat de séparation :

- suite web complète : **verte** ;
- TypeScript : **vert** ;
- build Next.js production et Preview : **verts**, **47 routes** ;
- serveur issu du build production : Home **200**, laboratoire **404** ;
- serveur issu du build Preview : Home **200**, laboratoire **200** ;
- navigateur sans WebGL : tableau statique visible et aucun canvas actif ;
- perte de contexte simulée : un seul repli, restauration autorisée et listener
  supprimé au démontage ;
- `git diff --check` : **vert**.

Cette séparation est locale et n'est pas comprise dans la Preview publiée. Elle
n'autorise ni fusion, ni déploiement production.

## 12. Direction publique daylight — 4 septembre 2026

Le candidat local `3e8c08a` retire le dernier langage visuel de démonstration
des surfaces publiques. La première visite ouvre désormais FILON en lumière
éditoriale ; le sombre reste un choix explicite. Le système emploie trois
matières fonctionnelles : ivoire pour chercher et lire, sauge pour expliquer la
preuve, argile pour concentrer la décision. Le footer utilise un brun minéral,
pas un noir neutre.

La passe couvre Home, Search, Catalogue, Produit, Score/Cashback, Marchands,
Catégories, Composer et les pages éditoriales partagées. Le canvas Three.js,
son brouillard, sa grille, ses volumes, ses lumières et son fallback statique
ont été recalibrés dans le même espace clair : il ne s'agit pas d'un habillage
CSS placé devant une scène encore noire.

Search ne joue plus huit étapes préécrites. Pendant la vraie requête, il affiche
uniquement « FILON cherche dans le catalogue… » et précise que les résultats
n'apparaîtront qu'après vérification. Le flux SSE, son terminal honnête et son
abstention fail-closed restent inchangés. Un test interdit la réintroduction de
la fausse checklist.

Qualification locale du candidat : suite web complète verte, TypeScript vert,
build Next.js de 47 routes vert. La génération statique a utilisé ses replis
fail-closed lorsque Railway était inaccessible depuis le sandbox. La revue
visuelle desktop a couvert Home, Search (repos et requête active), Catalogue,
Produit WebGL, Score, Marchands, Outfit Studio et À propos ; leurs headers et
surfaces principales restent lisibles sans fond noir imposé.

Cette qualification est locale. Elle n'autorise ni publication, ni nouvelle
Preview, ni fusion, ni déploiement production.
