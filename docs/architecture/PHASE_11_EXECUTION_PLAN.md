# FILON — Phase 11 Web Experience Execution Plan

- Ouverture : **1er septembre 2026**
- Gate d'entrée : **Phase 10 = GO**
- Statut : **P11A à P11F QUALIFIÉS LOCALEMENT**
- Client canonique : **`filon-web`**
- Lecteurs shadow : **OFF**
- Immersive : **NO-GO inchangé**

## Objectif

Rendre la chaîne Product Intelligence compréhensible dans le client web sans
transformer une preuve partielle en promesse. L'expérience doit être simple,
rapide, accessible et premium uniquement lorsque la hiérarchie visuelle aide la
décision.

## Baseline

La home active avant Phase 11 importait `ImmersiveExperience` : 320 frames
desktop, 192 frames mobile et un scroll pouvant atteindre 1 000 hauteurs
d'écran. Elle ne matérialisait pas les composants de décision requis et
contredisait la gate Immersive encore fermée.

Les fiches produit et le catalogue possèdent déjà de solides frontières de
vérité : devise explicite, preuve courante, fraîcheur, stock tri-state,
comparaison monodevise et CTA marchand fail-closed. Phase 11 doit conserver ces
invariants et les rendre lisibles, sans raccorder les tables shadow.

Le corpus visuel fourni dans les deux dossiers `CID filon` a été dédupliqué et
analysé dans `PHASE_11A_CID_REFERENCE_AUDIT.md`. Phase 11 reprend son objet
central, sa palette chaude et sa hiérarchie éditoriale, mais pas son scroll
spectacle ni sa dépendance à la 3D.

## Lots et gates

| Lot | Livrable | Gate |
|---|---|---|
| P11A | baseline et frontière Core UX / Immersive | aucun asset immersif dans le graphe de la home |
| P11B | primitives de décision web | unknown, preuve, contraintes et raisons accessibles |
| P11C | home evidence-first | comprendre la proposition et agir sans scroll forcé |
| P11D | fiches produit | identité, offres, historique et inconnues cohérents |
| P11E | assistant | intention, contraintes et abstention lisibles |
| P11F | performance/accessibilité | build, typecheck, tests vérité, budgets et parcours clavier |
| P11G | production | CI, déploiement, sondes et reçu terminal |

## Invariants

1. Aucun lecteur public BUY/WAIT, Confidence ou shadow n'est activé.
2. Aucun prix n'est rendu sans montant positif, devise supportée et preuve
   courante.
3. Une comparaison exige le même produit, la même devise et au moins deux
   offres admissibles.
4. Une donnée absente s'affiche comme inconnue ; elle ne devient jamais zéro,
   disponible ou favorable.
5. La recherche principale possède un label, fonctionne au clavier et conserve
   la requête dans l'URL.
6. Aucun canvas, film, séquence d'images ou dépendance Three.js n'entre dans le
   graphe de la home Phase 11.
7. Les fichiers immersifs historiques ne sont ni supprimés ni présentés comme
   une expérience qualifiée.

## Sortie P11A/P11B

- `WebExperience` remplace la home immersive ;
- huit primitives de décision sont disponibles ;
- le seul exemple chiffré vient de `getProof` et reste masqué si la preuve n'est
  pas comparable ;
- FR/NL/EN sont conservés ;
- reduced-motion et focus clavier sont explicites ;
- aucun flag ou contrat backend ne change.

## Qualification locale P11C

- corpus CID : **2 dossiers / 13 vidéos uniques** ;
- tests web : **verts**, y compris vérité produit, unknown et achat fail-closed ;
- typecheck : **vert** ;
- build Next.js production : **vert, 42 pages** ;
- route `/` : **5,33 kB**, premier chargement **114 kB** ;
- inspection visuelle : hiérarchie serif, objet central, palette crème/noir/orange
  et header lisible avant/après scroll ;
- exemple catalogue indisponible lors de l'inspection : rendu **unknown** honnête,
  sans image, prix ou recommandation de substitution.

## Qualification locale P11D/P11E

- catalogue réel : **1 528 583 offres** observées pendant la qualification ;
- fiche offre `72493` : montant et stock courants rendus, historique trop récent,
  confiance non calibrée et champs manquants explicitement exposés ;
- après expiration de la preuve, la même fiche est retombée sur **prix ou
  disponibilité à vérifier**, sans conserver le CTA marchand ;
- les deux routes produit annoncent désormais leur surface claire au header,
  dont le contraste est stable avant et après scroll ;
- assistant réel : l'indisponibilité amont produit une abstention terminale,
  jamais une carte synthétique ;
- les cartes assistant n'utilisent plus `rank` ni `buy` : elles annoncent
  seulement une offre avec prix, devise, disponibilité et fraîcheur courants ;
- Product Ranking, BUY/WAIT, Confidence et autres lecteurs shadow restent OFF.

## Qualification locale P11F

- six suites web : **vertes**, dont les gardes de vérité historiques ;
- typecheck : **vert** ;
- build Next.js production : **vert, 42 pages** ;
- route `/` : **5,33 kB**, premier chargement **114 kB** ;
- inspections à **320 × 720**, **390 × 844** et **1 440 × 900** : aucun
  débordement horizontal ;
- DOM rendu : un `main`, un `h1`, une recherche, zéro champ visible sans nom,
  zéro bouton visible sans nom et zéro image sans `alt` ;
- cibles critiques : **44 px minimum** ;
- navigation mobile et langue : association contrôle/panneau, fermeture
  `Échap`, exclusion des options masquées du parcours clavier et restitution
  du focus ;
- reduced-motion explicite et aucune animation porteuse d'information.

P11G doit encore apporter la preuve terminale de publication, CI, déploiement,
sondes et invariants de production. Il ne doit activer aucun lecteur shadow.

Aucun résultat local n'autorise à lui seul une promotion publique ou production.
