# Contrôle de production — Page Marchands

**Date :** 13 août 2026 (Europe/Bruxelles)

## Constats

La route publique `https://www.filon.be/marchands/?deploy=32de19c` est accessible et affiche immédiatement la grille des partenaires. Le rendu comprend le champ de recherche, les filtres de régions et **207 partenaires**. Aucun texte de chargement persistant n’est présent dans la réponse HTML ni dans le rendu navigateur.

La réponse directe du backend Railway sur `/api/catalog/merchants?limit=500` renvoie **200**, 207 éléments et environ 40,8 kB de données. La première mesure réseau a relevé 3,10 s ; la page précharge donc désormais ces données côté serveur et les revalide au maximum une fois par heure. En cas d’indisponibilité ponctuelle lors du rendu serveur, le navigateur conserve une seconde tentative et affiche un skeleton accessible plutôt qu’un message brut.

## Déploiement contrôlé

- Commit : `32de19c` — `feat: précharger les marchands partenaires`
- Build local : réussi.
- Réponse HTML de production : liste des 207 partenaires rendue côté serveur.
- Contrôle visuel de production : grille, recherche et filtres visibles.

## Cache des frames immersives

Le commit `26651cc` est également actif. Les frames `/seq/hero/*` sont conservées par le CDN (`s-maxage=31536000`) tout en étant revalidées par le navigateur (`max-age=0`) afin d’éviter qu’une future séquence reste bloquée dans un cache local.

## FAQ — contrôle éditorial et déploiement

Un audit de la FAQ a relevé plusieurs formulations absolues qui n’étaient pas suffisamment étayées : recommandation présentée comme une décision à la place de l’utilisateur, reconditionné systématiquement certifié et garanti, calendrier d’extension et d’application trop affirmatif, ainsi qu’une explication imprécise du cashback. Le commit `5887eb8` remplace ces réponses en français, néerlandais et anglais par des formulations qui reflètent le fonctionnement réel : comparaison à partir des informations du catalogue, décision finale laissée à l’utilisateur, conditions dépendantes de chaque marchand et extension Chrome en attente de publication.

La page `https://www.filon.be/faq/?deploy=5887eb8` a été contrôlée dans le navigateur de production. La version française servie contient les réponses corrigées, dont l’accès gratuit sans formule payante actuelle, l’affichage conditionnel du cashback, la vérification des conditions de chaque offre reconditionnée et le statut exact de l’extension.

## À propos — contrôle éditorial et déploiement

La page À propos comportait des garanties non vérifiables, notamment « ne jamais payer le prix fort », une réponse « en une seconde » et une promesse de payer moins. Le commit `bcce918` conserve l’ambition de marque mais la formule comme une aide à la comparaison : informations disponibles réunies dans une vue, prix affiché, cashback et codes promo uniquement lorsqu’ils sont renseignés, décision laissée à l’utilisateur.

La page `https://www.filon.be/a-propos/?deploy=bcce918` a été vérifiée dans le navigateur de production. Le nouveau positionnement « Choose better, before you buy » est visible en anglais, la hiérarchie visuelle reste intacte, et le CTA est désormais « Check FILON before deciding on your next purchase ».

## Intelligence — contrôle éditorial et déploiement

L’audit de la page Intelligence a écarté des capacités qui ne sont pas garanties par le produit actuel : prédiction d’un prix plancher, recommandation automatique d’attendre ou d’acheter, estimation de fiabilité et de durée de vie, synthèse de milliers d’avis et meilleur choix universel. Le commit `3292864` décrit désormais les signaux effectivement présentés lorsque disponibles : prix affiché, contexte ou score avec ses limites, marchand, cashback, codes promo et autres offres correspondant à la recherche.

La page `https://www.filon.be/intelligence/?deploy=3292864` a été vérifiée dans le navigateur de production. La version française visible explique explicitement que la disponibilité varie selon l’offre et que la vérification finale reste entre les mains de l’utilisateur.

## Blog — contrôle de contenu et de rendu

La liste du blog contient six guides et comparatifs, chacun relié à une page dédiée. Les visuels WebP existent localement en 1600 × 893 et répondent correctement en production avec un statut 200. La première capture du navigateur a montré des zones de visuel vides pendant le chargement différé ; un second contrôle après chargement a confirmé que les images sont bien rendues dans les cartes.

Les accroches du blog restent à auditer article par article avant toute promesse chiffrée ou affirmation de résultat. Aucun contenu n’a été modifié dans cette étape, car les articles éditoriaux doivent être vérifiés à partir de leurs sources avant révision.

## Guides cashback et reconditionné — contrôle éditorial et déploiement

Le guide cashback a été revu dans le commit `5b3b2dd`. Les fourchettes de taux et délais non sourcées ont été remplacées par des conditions vérifiables par offre : taux affiché, produits éligibles, compatibilité d’un code, validation et règles de versement. Le mécanisme de commission et de suivi s’appuie sur les explications publiques d’Awin et d’Affilae ; les blocages de suivi par des paramètres de confidentialité ou bloqueurs de contenu sont documentés par ShopBack.[1][2][3]

Le guide reconditionné a été revu dans le commit `e8261f8`. Les pourcentages de décote, garantie universelle de 12–24 mois et économie globale de 45–50 % ont été supprimés. L’article présente désormais des critères de vérification par offre — état, batterie, accessoires, garantie, retour, livraison — et rappelle que les grades ne sont pas standardisés.

Les deux routes de production ont été vérifiées visuellement : `https://www.filon.be/blog/cashback-comment-ca-marche/?deploy=5b3b2dd` et `https://www.filon.be/blog/neuf-vs-reconditionne-economie-reelle/?deploy=e8261f8`. Les tableaux et CTAs révisés s’affichent correctement.

## Références

[1] [Awin — What is affiliate marketing?](https://www.awin.com/us/affiliate-marketing/what-is-affiliate-marketing)

[2] [Affilae — Cashback in affiliate marketing](https://affilae.com/en/cashback-in-affiliate-marketing/)

[3] [ShopBack — Disable Ad Blockers for Cashback Tracking](https://support.shopback.ph/hc/en-us/articles/38835760768659-Disable-Ad-Blockers-for-Cashback-Tracking)

## Guide Black Friday — contrôle éditorial et déploiement

Le guide Black Friday a été corrigé dans les commits `07897df` et `df9c3d3`. Il ne présente plus le Black Friday comme le meilleur moment garanti de l’année pour la tech, ni FILON comme un moteur capable de trancher automatiquement qu’une offre est « vraie ». L’historique de prix est désormais décrit comme un indicateur parmi d’autres, seulement lorsqu’il est disponible ; le contenu renvoie aux détails de l’offre, aux frais, aux conditions du marchand et aux avantages signalés.

La route de production `https://www.filon.be/blog/black-friday-sans-se-faire-avoir/?deploy=df9c3d3` sert la dernière version. Le contrôle de réponse a confirmé que les nouvelles formulations sont présentes dans le rendu produit.

## Guide ordinateur portable — contrôle éditorial et déploiement

Les commits `febc28f` et `d7296cd` ont supprimé les budgets présentés comme universels, la décote reconditionnée chiffrée et la promesse que FILON proposerait « les meilleurs choix », le « vrai prix » ou le « bon moment ». Les repères matériels sont maintenant reliés aux besoins de logiciels et aux usages, sans seuil présenté comme valable pour tout le monde.

La route `https://www.filon.be/blog/choisir-ordinateur-portable/?deploy=d7296cd` a été contrôlée dans le navigateur de production. Les tableaux par usage sont affichés correctement et la page indique bien que FILON recherche les offres du catalogue et présente les informations disponibles, avec une vérification de l’offre par l’utilisateur avant commande.

## Comparatif cashback — contrôle éditorial et déploiement

Le commit `95d3ec3` retire les taux illustratifs non sourcés, les rendements doublés et les promesses selon lesquelles FILON automatiserait une comparaison de toutes les applications. Le contenu précise maintenant que FILON consulte son propre catalogue, affiche prix, cashback, code et score seulement lorsqu’ils sont renseignés, et demande la vérification des conditions du marchand.

La page `https://www.filon.be/blog/quelle-app-cashback-paie-le-plus/?deploy=95d3ec3` a été vérifiée dans le navigateur de production. Le tableau reste lisible et le positionnement de FILON est désormais cohérent avec son périmètre réel.

## Guide du moment d’achat — contrôle éditorial et déploiement

Le commit `79c3c9a` transforme le calendrier d’achat en repères de vérification : les saisons, changements de gamme et promotions ne sont plus présentés comme des baisses garanties. L’historique est décrit comme un contexte optionnel et FILON ne donne plus une instruction d’acheter ou d’attendre.

La route `https://www.filon.be/blog/quand-acheter-moins-cher/?deploy=79c3c9a` a été vérifiée dans le navigateur de production. Le tableau « Periods to watch » et l’appel à comparer les offres disponibles sont correctement rendus.

## Validation transversale finale

Les quatorze routes contrôlées — accueil, catalogue, assistant, marchands, FAQ, À propos, Intelligence, index du blog et six guides révisés — ont toutes répondu en HTTP `200`. Le backend Railway a également répondu `200` sur `/health/live`, `/health/ready` et `/api/catalog/merchants?limit=1` pendant le contrôle.

Le cache CDN des images de la séquence immersive sert `cache-control: public, max-age=0, s-maxage=31536000, stale-while-revalidate=86400` : le navigateur revalide les modifications visuelles tandis que le CDN peut conserver les frames un an.

La navigation desktop a été vérifiée après hydratation : « Catalogue » est un lien direct distinct et le bouton adjacent ouvre correctement le méga-menu, avec les catégories et le lien vers le catalogue complet. Cette interaction a été contrôlée dans le navigateur sur une page de production.
