# Extension FILON (Chrome / Edge / navigateurs Chromium)

Le réflexe FILON, directement sur les fiches produit. Sur un marchand supporté,
l'extension **repère le produit** et vous emmène en un clic vers l'analyse réelle
de FILON : meilleur marchand, reconditionné certifié, code promo vérifié et
cashback maximal, réunis en un seul **vrai prix**.

> Principe : l'extension **ne fabrique aucune économie chiffrée**. Elle détecte
> le produit et relie à FILON, où le vrai prix est calculé sur des données
> réelles. Rien n'est collecté en arrière-plan, rien n'est revendu.

## Contenu

| Fichier | Rôle |
| --- | --- |
| `manifest.json` | Manifest V3, marchands supportés, popup, service worker |
| `background.js` | Service worker minimal (ouvre l'accueil à l'installation) |
| `content.js` | Détection produit + overlay (pastille → panneau) |
| `content.css` | Style de l'overlay, namespacé `filon-x` |
| `popup.html` / `popup.js` | Popup de la barre d'outils : recherche + analyse de la page |
| `icons/` | Icônes 16 / 32 / 48 / 128 (+ 256 pour le store) |
| `_locales/fr/` | Libellés du store |

## Marchands supportés (v1)

Amazon (.com.be / .fr / .nl), bol.com, Coolblue (.be / .nl), MediaMarkt,
Krëfel, Vanden Borre, Fnac (.com / .be), Cdiscount, Darty, Boulanger,
Back Market (.fr / .be). D'autres suivront.

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

`activeTab` n'est lu que sur action de l'utilisateur (bouton « Analyser la page »).
Aucun tracking, aucune télémétrie, aucune revente. Le seul appel réseau est
l'ouverture de `filon.be` quand vous cliquez.
