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
> Votre copilote d'achat indépendant. Obtenez l'analyse complète des prix, du reconditionné et des codes promo sur chaque produit.

**Description longue** :
> FILON est votre copilote d'achat indépendant, conçu pour vous aider à trouver le meilleur prix avant de finaliser votre commande. 
> 
> Lorsque vous consultez un produit sur vos boutiques en ligne préférées, FILON identifie l'article et rassemble pour vous toutes les offres disponibles sur le marché. En un seul clic, accédez à une analyse complète : le marchand le plus compétitif du moment, l'équivalent reconditionné garanti, les codes promotionnels vérifiés et le cashback disponible. Tous ces éléments sont calculés pour vous donner un seul indicateur clair : le vrai prix.
>
> Une expérience haut de gamme et transparente :
> • Entièrement gratuit et sans création de compte obligatoire.
> • Totalement indépendant : notre algorithme ne peut être influencé par aucun paiement ou placement sponsorisé.
> • Respect strict de la vie privée : aucune télémétrie, aucune création de profil publicitaire et aucune revente de vos données personnelles.
>
> FILON ne se base pas sur des estimations, mais sur l'historique réel des prix. Ne surpayez plus jamais vos achats en ligne.

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
