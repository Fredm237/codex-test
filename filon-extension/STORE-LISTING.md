# Dépôt Chrome Web Store — FILON

Tout ce qu'il faut pour publier. Une fois en ligne, on colle l'URL de la fiche
dans `filon-web/lib/config.ts` (`CHROME_STORE_URL`) et **tous** les boutons
« Ajouter à Chrome » du site installent l'extension en un clic.

## Pré-requis (côté toi)

1. Un **compte développeur Chrome Web Store** : https://chrome.google.com/webstore/devconsole — frais **uniques de 5 $**.
2. Vérifier le compte (Google demande parfois une adresse / e-mail pro).

## Fichier à téléverser

- Le **ZIP de l'extension** (dossier `filon-extension/` compressé, `manifest.json` à la racine). Je le régénère à la demande.

## Champs de la fiche

**Nom** : FILON — le vrai prix, avant d'acheter

**Description courte** (132 car. max) :
> FILON repère le produit sur la page et vous emmène au vrai prix le plus bas : marchand, reconditionné, code promo et cashback réunis.

**Description longue** :
> FILON est votre copilote d'achat. Sur une fiche produit (Amazon, bol.com, Coolblue, MediaMarkt, Fnac, Cdiscount, Back Market…), FILON repère l'article et vous emmène en un clic vers l'analyse complète : le meilleur marchand du moment, l'équivalent reconditionné garanti quand il existe, le code promo vérifié et le cashback maximal — réunis en un seul « vrai prix ».
>
> • Gratuit, sans compte obligatoire.
> • Indépendant : aucune marque ne peut acheter un meilleur classement.
> • Respectueux : permissions minimales, aucune télémétrie, aucune revente de données.
>
> FILON ne fabrique aucun chiffre : le vrai prix est calculé sur des données réelles.

**Catégorie** : Shopping
**Langue** : Français
**Éditeur** : FILON

## Visuels demandés par Google

| Élément | Format | Statut |
| --- | --- | --- |
| Icône | 128×128 PNG | ✅ `icons/icon128.png` |
| Petite tuile promo | 440×280 PNG | à générer (je peux le faire) |
| Capture(s) d'écran | 1280×800 ou 640×400 | à faire (popup + overlay sur une fiche) |
| Grande tuile (option) | 920×680 | facultatif |

## Confidentialité (obligatoire)

- **Politique de confidentialité** : URL requise → https://filon.be/confidentialite (déjà en ligne).
- Justification des permissions à cocher :
  - `activeTab` : lire le titre de la page **uniquement quand l'utilisateur clique** sur « Analyser la page ».
  - `storage` : mémoriser la fermeture de l'overlay (12 h) — local, aucune donnée personnelle.
  - `host_permissions` : limités aux marchands supportés, pas d'accès « tous les sites ».
- Déclaration : **aucune donnée collectée / vendue / transférée**.

## Après validation (2–5 jours ouvrés en général)

1. Copier l'URL de la fiche (`https://chromewebstore.google.com/detail/…/<ID>`).
2. La coller dans `filon-web/lib/config.ts` → `CHROME_STORE_URL`.
3. Redéployer : le bouton « Ajouter à Chrome » installe désormais en un clic, partout.
