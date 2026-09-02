# Extension FILON (Chrome / Edge / navigateurs Chromium)

Le réflexe FILON, directement sur les fiches produit. Sur un marchand supporté,
l'extension **repère le produit** et vous emmène en un clic vers l'analyse
FILON : offres indexées, historique disponible, alternatives et avantages
documentés. Le périmètre et les inconnues restent visibles.

> Principe : l'extension **ne fabrique aucune économie chiffrée**. Elle détecte
> le produit et relie à FILON, où les prix observés sont présentés avec leur
> source et leur fraîcheur. Aucune donnée n'est transmise automatiquement
> depuis les pages marchandes.

## Contenu

| Fichier | Rôle |
| --- | --- |
| `manifest.json` | Manifest V3, marchands supportés, popup, service worker |
| `background.js` | Service worker minimal (ouvre l'accueil à l'installation) |
| `product-observation.js` | Extraction locale URL/merchant/identifiants/offre/JSON-LD |
| `content.js` | Détection produit + overlay (pastille → panneau) |
| `content.css` | Style de l'overlay, namespacé `filon-x` |
| `popup.html` / `popup.js` | Popup de la barre d'outils : recherche + analyse de la page |
| `icons/` | Icônes 16 / 32 / 48 / 128 (+ 256 pour le store) |
| `_locales/fr/` | Libellés du store |

## Pages prises en charge (v1)

Les domaines autorisés sont déclarés dans `manifest.json`. Cette autorisation
technique permet la détection d'une fiche ; elle ne signifie ni partenariat ni
couverture exhaustive du catalogue du site concerné.

## Installer en local (mode développeur)

1. Ouvrir `chrome://extensions`.
2. Activer **Mode développeur** (en haut à droite).
3. **Charger l'extension non empaquetée** → sélectionner le dossier `filon-extension/`.
4. Épingler FILON, puis ouvrir une fiche produit sur un marchand supporté.

## Publication (Chrome Web Store)

- Icône 128×128 fournie (`icons/icon128.png`), visuel 256 pour la fiche.
- Description, capture d'écran et politique de confidentialité à joindre au dépôt.
- Permissions minimales : `activeTab`, `storage` + `host_permissions` limités aux
  marchands supportés (aucun accès « tous les sites »).

## Confidentialité

Le script de contenu extrait localement les champs Product JSON-LD autorisés
afin d'afficher l'overlay. `activeTab` sert au bouton « Analyser la page » de
la popup. Aucun tracking ni aucune télémétrie n'est implémenté dans
l'extension. Aucune observation structurée n'est transmise en arrière-plan.

Après une action explicite, un GTIN valide est placé dans le chemin de la fiche
FILON exacte ; à défaut, seul le titre borné est ajouté à l'URL de recherche.
L'URL marchande, son prix, son stock, son SKU, son MPN et son JSON-LD restent
locaux. L'accueil FILON s'ouvre aussi lors de l'installation. La politique de
confidentialité du site s'applique alors.
