# FILON — Extension navigateur (prototype)

> Le réflexe malin avant chaque achat.

Prototype **Manifest V3** de l'extension FILON : sur une fiche produit, elle
détecte l'article, compare cashback / reconditionné / codes promo, et affiche
en overlay votre **prix réel le plus bas** — sans quitter la page.

Ce prototype est **autonome et vérifié** : le content script détecte le produit
(JSON-LD `Product`, puis OpenGraph + prix) et injecte l'overlay. La comparaison
est **simulée** dans `content.js` (`compareOffers`) ; en production, cette
fonction appellerait l'API FILON.

## Charger dans Chrome / Edge

1. Ouvrir `chrome://extensions` (ou `edge://extensions`).
2. Activer le **Mode développeur**.
3. **Charger l'extension non empaquetée** → sélectionner ce dossier `filon-extension/`.
4. L'icône FILON apparaît dans la barre d'outils.

> Le content script se déclenche par défaut sur `*.boutique-demo.fr` (le domaine
> de démonstration). Pour l'essayer sur un vrai marchand, ajoutez le domaine dans
> `manifest.json` → `content_scripts.matches` **et** `host_permissions`, puis
> rechargez l'extension. N'élargissez les permissions qu'aux domaines réellement
> pris en charge — c'est une bonne pratique de sécurité et d'audit du store.

## Firefox

Firefox supporte MV3. Charger via `about:debugging` → « Ce Firefox » →
« Charger un module temporaire » → sélectionner `manifest.json`.

## Structure

```
filon-extension/
├── manifest.json        # MV3 : action, background, content_scripts, permissions
├── background.js        # service worker — seed des stats à l'installation
├── content.js           # détection produit + injection de l'overlay + scan
├── content.css          # styles de l'overlay (scopés .filon-x-*, anti-collision)
├── popup.html / .js     # popup barre d'outils : stats + interrupteur actif/inactif
├── _locales/fr/         # chaînes localisées (nom, description)
└── icons/               # 16 / 48 / 128 px
```

## Sécurité & confidentialité

- Permissions minimales : `storage`, `activeTab`, et un `host_permissions`
  restreint (pas de `<all_urls>` sur le content script).
- Aucune donnée de navigation revendue ; l'overlay affiche systématiquement la
  nature affiliée des liens (exigence légale + pilier de marque).
- Le style de l'overlay est préfixé `filon-x-` et posé en `z-index` très haut
  pour éviter toute collision avec la page hôte.

## Prochaines étapes (production)

- Brancher `compareOffers()` sur l'API FILON (taux cashback temps réel,
  matching reconditionné, test de codes promo).
- Résolution des liens affiliés + comptabilisation des économies (popup stats).
- Adaptateurs par marchand pour une détection produit fiable à grande échelle.
- Publication : Chrome Web Store, Edge Add-ons, Firefox AMO (respect des règles
  d'affiliation des extensions, durcies depuis mars 2025).
