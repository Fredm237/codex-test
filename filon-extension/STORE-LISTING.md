# FILON — Chrome Web Store Listing

---

## Identité

| Champ | Valeur |
|-------|--------|
| Nom | FILON — le vrai prix, avant d'acheter |
| Nom court | FILON |
| Catégorie | Shopping |
| Langue principale | Français |
| Éditeur | FILON |
| Version | 1.0.0 |

---

## Description courte

> Votre copilote d'achat indépendant. Obtenez l'analyse complète des prix, du reconditionné et des codes promo sur chaque produit.

---

## Description longue

FILON est votre copilote d'achat indépendant, conçu pour vous aider à trouver le meilleur prix avant de finaliser votre commande.

Lorsque vous consultez un produit sur vos boutiques en ligne préférées, FILON identifie l'article et rassemble pour vous toutes les offres disponibles sur le marché. En un seul clic, accédez à une analyse complète : le marchand le plus compétitif du moment, l'équivalent reconditionné garanti, les codes promotionnels vérifiés et le cashback disponible. Tous ces éléments sont calculés pour vous donner un seul indicateur clair : le vrai prix.

**Une expérience haut de gamme et transparente :**

— Entièrement gratuit et sans création de compte obligatoire.
— Totalement indépendant : notre algorithme ne peut être influencé par aucun paiement ou placement sponsorisé.
— Respect strict de la vie privée : aucune télémétrie, aucune création de profil publicitaire et aucune revente de vos données personnelles.

FILON ne se base pas sur des estimations, mais sur l'historique réel des prix. Ne surpayez plus jamais vos achats en ligne.

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
| `activeTab` | Lire le titre et l'URL de la page uniquement lorsque l'utilisateur clique sur « Analyser ». Aucune lecture automatique. |
| `storage` | Mémoriser la préférence de fermeture de l'overlay (12 heures). Stockage local uniquement, aucune donnée personnelle. |
| `host_permissions` | Limité aux sites marchands supportés. Aucun accès à l'ensemble de la navigation. |

**Déclaration de données** : aucune donnée collectée, vendue ou transférée à des tiers.

---

## Publication

1. Compresser le dossier `filon-extension/` en ZIP (manifest.json à la racine).
2. Téléverser sur le [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole).
3. Renseigner les champs ci-dessus.
4. Après validation, copier l'URL de la fiche dans `filon-web/lib/config.ts` → `CHROME_STORE_URL`.

---

*FILON — Designed in Bruxelles.*
