# FILON — Phase 11 local qualification report

- Date : **1er septembre 2026**
- Branche locale : **`codex/filon-phase-11-web-experience`**
- Point de reprise P11A/P11B/P11C : **`f65ea5e`**
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
| Inspection mobile | PENDING | media queries présentes ; contrôle visuel dédié à produire |
| Lighthouse/a11y automatisé | PENDING | focus, labels et reduced-motion présents ; audit outillé à produire |

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
   autoplay. Son coût doit entrer dans l'audit performance P11F.
4. Une qualification mobile visuelle et un audit automatisé accessibilité /
   performance restent nécessaires avant P11G.

## Conclusion locale

**P11A à P11E : QUALIFIÉS LOCALEMENT.**

Ce rapport n'est ni un reçu de production ni une autorisation de publication.
P11F doit fermer les contrôles mobile, accessibilité et performance avant toute
promotion P11G.
