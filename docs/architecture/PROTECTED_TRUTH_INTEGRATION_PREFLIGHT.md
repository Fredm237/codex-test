# FILON — prévalidation de l’intégration protégée « vérité prix »

- Date de coupure : **29 août 2026**
- Branche locale : `codex/filon-phase-0-core`
- Référence locale non protégée : `56de1cf`
- Statut : **prévalidation verte, intégration non autorisée, NO-GO**

## Décision

Les primitives et consommateurs non protégés sont versionnés. Les changements
nécessaires dans les fichiers appartenant déjà à l’utilisateur ont été rejoués
dans une copie isolée du dépôt, jamais dans le worktree réel. Cette simulation
est verte, mais elle ne constitue ni une autorisation de modifier ces fichiers,
ni un commit, ni une publication GitHub.

## Socle déjà versionné

| Commit | Portée | Contrat obtenu |
|---|---|---|
| `e152ed0` | backend + web | Normalisation de devise, preuve SQL comparable et formatage monétaire sans repli |
| `4e5755d` | cartes et rails web | Aucun montant ni rail sans prix, devise, stock et relevé courant concordants |
| `56de1cf` | fiches offre et produit | Aucun prix brut non attesté sur les vues détaillées |

Ces commits ne contiennent aucun des fichiers protégés listés ci-dessous.

## Lot protégé simulé

### `filon-backend/app/api/routes/catalog.py`

- seuils SQL écrits en UTC naïf, compatibles avec les colonnes `DateTime`
  existantes et `asyncpg` ;
- Pulse, Highlights et Relief limités aux prix positifs, devises supportées et
  états de stock explicitement comparables ;
- clé de cache Relief versionnée avec le contrat de vérité prix ;
- cartes, grilles, fiches offre et produits EAN alimentées par le rapprochement
  groupé `Offer` ↔ `PriceSnapshot` ;
- montant, devise et stock masqués sans correspondance exacte ou relevé frais ;
- historique explicitement monodevise avec `in_stock=true` par point ;
- aucun minimum, maximum, ordre ou verdict à travers plusieurs devises.

### `filon-web/components/editorial/SearchAssistant.tsx`

- montant et devise normalisés sans symbole de secours ;
- recommandation refusée sans `evidence_current=true`, relevé frais et stock
  positif ;
- URL marchande externe limitée à une cible HTTPS publique sûre ; sinon, seul
  le parcours catalogue interne reste disponible ;
- résultat vide ou non réel présenté comme une abstention, jamais comme une
  recommandation FILON.

### MegaMenu

`filon-web/components/editorial/MegaMenu.tsx` et
`filon-web/scripts/test-megamenu.mjs` doivent être intégrés ensemble. Leur état
local actuel rétablit les 17 tests, mais aucun des deux fichiers ne doit être
pris séparément.

## Preuves de la copie isolée

- backend complet : **1 928 réussis, 1 ignoré**, 120,82 s ;
- sous-ensemble catalogue renforcé : **120/120** ;
- web : **17/17** tests MegaMenu, contrats v1, claims et vérité produit ;
- TypeScript : succès ;
- build Next.js production : succès, **42 pages** générées ;
- aucune migration, aucune écriture de données et aucun appel de production.

La simulation ajoute notamment des régressions pour : relevé absent ou
périmé, prix courant muté sans snapshot correspondant, devise manquante,
stock inconnu, historique multidevise, produit EAN multidevise et Assistant
sans preuve courante.

## Autorisations exactes encore requises

L’intégration reste interdite tant que l’utilisateur n’a pas donné les accords
explicites suivants :

> J’autorise la modification et l’intégration de
> `filon-backend/app/api/routes/catalog.py` et
> `filon-web/components/editorial/SearchAssistant.tsx` pour supprimer les
> fallbacks de devise, rendre les agrégats et cartes fail-closed, en conservant
> mes changements existants.

> J’autorise la modification et l’intégration conjointe de
> `filon-web/components/editorial/MegaMenu.tsx` et
> `filon-web/scripts/test-megamenu.mjs`, en conservant mes changements
> existants, afin de rétablir la suite web complète.

La publication distante exige séparément :

> J’autorise le push public de la branche `codex/filon-phase-0-core` vers
> `Fredm237/codex-test`.

Les accords génériques, l’autorisation d’aider ou le mode automatique ne
remplacent aucun de ces consentements ciblés.

## Intégration et rollback prévus

Après autorisation, les deux lots protégés seront appliqués en conservant les
diffs existants, validés à nouveau sur le worktree, puis enregistrés dans des
commits atomiques séparés. Le rollback est un revert de commit ; aucune donnée
ni migration n’est impliquée. Le push, les runs CI distants et la protection de
`main` restent des gates distinctes.

Même après cette intégration, le verdict Phase 1 restera **NO-GO** tant que les
sept datasets Quality Lab conservent zéro cas humain et que la production, la
CI distante et la protection de branche ne sont pas qualifiées.
