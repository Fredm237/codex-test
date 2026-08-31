# FILON — Chrome Web Store Listing

---

## Identité

| Champ | Valeur |
|-------|--------|
| Nom | FILON — les offres observées |
| Nom court | FILON |
| Catégorie | Shopping |
| Langue principale | Français |
| Éditeur | FILON |
| Version | 1.0.0 |

---

## Description courte

> Comparez les offres indexées et voyez les prix observés, l'historique disponible et les avantages documentés.

---

## Description longue

FILON est un copilote d'achat conçu pour vous aider à comparer les offres
indexées avant de finaliser votre commande.

Lorsque vous consultez une fiche prise en charge, FILON repère le nom du
produit et ouvre une recherche sur filon.be. L'analyse peut présenter les prix
observés chez les marchands indexés, une alternative reconditionnée, une
promotion ou un cashback lorsque ces données existent. Le prix, la
disponibilité et les conditions restent à confirmer chez le marchand.

**Une expérience haut de gamme et transparente :**

— Accès public actuellement à 0 € et sans création de compte obligatoire.
— Transparence : les offres affichées indiquent leur marchand et leur
périmètre de comparaison.
— Vie privée : aucune télémétrie ni profil publicitaire n'est implémenté dans l'extension ; aucune donnée n'est transmise automatiquement depuis les pages marchandes.

Lorsque l'historique contient assez de relevés, FILON le montre avec sa durée
et sa fraîcheur. Sinon, l'absence de preuve reste visible.

---

## Visuels

| Élément | Format | Fichier |
|---------|--------|---------|
| Icône | 128 × 128 PNG | `icons/icon128.png` |
| Tuile promotionnelle | 440 × 280 PNG | `store/promo-tile-440x280.png` |
| Capture d'écran 1 | 1280 × 800 PNG | `store/screenshot-1-1280x800.png` |
| Capture d'écran 2 | 1280 × 800 PNG | `store/screenshot-2-1280x800.png` |
| Bannière marquee | 1400 × 560 PNG | `store/marquee-1400x560.png` |

---

## Confidentialité et permissions

**Politique de confidentialité** : https://filon.be/confidentialite

| Permission | Justification |
|------------|---------------|
| `activeTab` | Lire le titre de l'onglet actif lorsque l'utilisateur clique sur « Analyser » dans la popup. |
| `storage` | Mémoriser la préférence de fermeture de l'overlay (12 heures). Stockage local uniquement, aucune donnée personnelle. |
| `host_permissions` | Détecter localement le nom d'un produit et afficher l'overlay sur les domaines supportés. Aucun accès à l'ensemble de la navigation. |

**Déclaration de données** : l'extension ne transmet aucune donnée automatiquement. Après une action de l'utilisateur, le nom du produit est inclus dans l'URL de recherche ouverte sur `filon.be` ; la politique de confidentialité du site s'applique. La préférence de fermeture reste dans le stockage local du navigateur.

---

## Publication

1. Compresser le dossier `filon-extension/` en ZIP (manifest.json à la racine).
2. Téléverser sur le [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole).
3. Renseigner les champs ci-dessus.
4. Après validation, copier l'URL de la fiche dans `filon-web/lib/config.ts` → `CHROME_STORE_URL`.

---

*FILON — Designed in Bruxelles.*
