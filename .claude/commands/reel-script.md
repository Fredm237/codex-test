---
description: Écrit un script de Reel pour FILON — hook, corps, appel à l'action, à partir d'un chiffre réel du catalogue
argument-hint: "[sujet] [--niche instagram|tiktok] [--langue fr|nl|en]"
allowed-tools:
  - Bash(curl -s *)
  - Read
  - Grep
  - Glob
---

# Script de Reel — FILON

Écris un script de Reel prêt à tourner. Le sujet est `$ARGUMENTS` ; s'il est
vide, choisis l'angle le plus fort parmi les chiffres du catalogue.

## D'abord, va chercher un chiffre vrai

Un Reel qui promet une économie sans la mesurer est un Reel qu'on ne peut pas
tenir, et FILON se vend précisément sur l'inverse. Interroge le catalogue avant
d'écrire une ligne :

```
curl -s "$FILON_API/api/catalog/stats"
curl -s "$FILON_API/api/catalog/pulse"
curl -s "$FILON_API/api/catalog/merchants"
```

Si l'API ne répond pas, dis-le et arrête-toi. **N'invente aucun chiffre, aucune
marque, aucun pourcentage.** Un script inventé finit en ligne, et une promesse
fausse coûte plus cher qu'un Reel de moins.

Ne cite que des marchands réellement partenaires — ceux que `/merchants`
renvoie. Fnac, Amazon, Cdiscount et Boulanger n'en sont pas.

## Ce que le script doit contenir

**Le hook — 3 premières secondes.** Il porte 90 % du résultat. Un chiffre
précis ou une tension concrète, jamais une question rhétorique
(« Vous voulez économiser ? » est mort à l'écrit comme à l'oral). Écris-en
**trois**, classés, et dis lequel tu recommandes et pourquoi.

**Le corps — 15 à 30 s.** Une seule idée. Le plan visuel à chaque phrase :
ce qu'on voit, pas seulement ce qu'on entend. Si une phrase n'a pas d'image,
elle n'a pas sa place.

**La chute — 3 à 5 s.** Ce que le spectateur fait maintenant, et une seule
chose. Le commentaire déclencheur si le Reel passe par une automatisation DM.

**Le texte à l'écran**, découpé plan par plan, court : ça se lit en 1,5 s.

**La légende**, avec la mention légale d'affiliation. FILON est gratuit pour
l'utilisateur et rémunéré par les marchands — le dire est une obligation, et
c'est aussi l'argument.

## La langue

FILON parle français, néerlandais et anglais. Par défaut le français de
Belgique. Avec `--langue nl` ou `--langue en`, écris **dans** la langue, ne
traduis pas : un hook traduit ne fonctionne jamais. Les montants restent en
euros, le format belge (`1 234,50 €`).

## Ce qu'il ne faut pas faire

- Pas de « astuce que personne ne connaît », pas de « les marques détestent ».
  FILON se positionne haut de gamme ; le ton racoleur détruit ce positionnement
  plus vite qu'il ne gagne des vues.
- Pas de superlatif invérifiable. « Le moins cher du marché » est une promesse
  juridique, pas une accroche.
- Pas de captures d'un site concurrent.

## Rends

Le script en clair, prêt à lire, avec la durée de chaque plan et le total. Puis
en une ligne : quel chiffre du catalogue tu as utilisé, et à quelle date tu l'as
lu — pour qu'on sache quand il faudra le vérifier à nouveau.
