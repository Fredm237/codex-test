# FILON — durcissement final du contrat catalogue v1

- Date : **30 août 2026**
- Lot : **P0.1 / contrat public catalogue et Assistant**
- Statut : **qualifié localement ; aucun changement de schéma ni de données**
- Décision : **GO technique pour ce lot ; NO-GO global inchangé**

## Objet

Ce lot ferme deux limites encore consignées dans le registre de Phase 0 :

1. les dates SQL UTC naïves ne doivent jamais sortir sans fuseau dans le
   contrat HTTP ;
2. l'Assistant ne doit pas construire une seconde variante d'URL catalogue.

Il ne change ni le TTL provisoire de 72 heures, ni les règles d'éligibilité,
ni les données, ni les migrations, ni les flags de production.

## Contrat temporel

`format_utc_timestamp` constitue désormais l'unique frontière entre les
colonnes historiques `DateTime` UTC naïves et les réponses publiques. Il
interprète ces colonnes comme UTC, convertit tout offset explicite vers UTC et
rend toujours une chaîne ISO 8601 portant `+00:00`.

La règle couvre :

- le dernier relevé de `/api/catalog/pulse` ;
- `observed_at` dans les listes, rails, offres et produits ;
- chaque point de l'historique de prix ;
- les dates du sitemap produits ;
- le journal public des synchronisations catalogue ;
- `generated_at` du relief des prix.

Cette sortie respecte enfin le `format: date-time` des schémas
`contracts/v1`, qui exige un instant RFC 3339 non ambigu. Le stockage SQL reste
inchangé pour conserver la compatibilité asyncpg.

## URL canonique Assistant/catalogue

La logique conversationnelle de choix du rayon vit maintenant dans
`filon-web/lib/catalogue-assistant-url.ts`. Elle ne concatène plus de query
string : elle appelle le constructeur `href` du catalogue pour le chemin,
l'ordre des paramètres, leur encodage et le rejet des filtres interdits.

La même fonction alimente les deux sorties de l'Assistant :

- l'état « aucune offre vérifiée » ;
- une carte sans lien marchand public sûr.

Il n'existe donc plus de divergence entre un retour sémantique et un retour de
carte pour une même demande.

## Preuves

- backend ciblé : **29/29** ;
- web : **17/17**, contrats v1, claims publics et vérité produit verts ;
- TypeScript : **vert** ;
- build Next.js : **42 routes**, vert ;
- backend complet : **2 119 réussis, 2 ignorés** en 74,16 s ;
- `git diff --check` et compilation Python : exigés avant intégration.

Les tests prouvent les dates SQL naïves, les offsets non UTC, les sorties
Pulse, produits, sitemap et synchronisation. Les URL connues et libres sont
comparées directement à la sortie du constructeur canonique du catalogue.

## Limites

Ce lot ne transforme pas le TTL 72 heures en SLO, ne qualifie aucun benchmark
humain et n'active aucun shadow Product Graph. Les datasets Quality restent à
zéro cas humain ; Redis, agrégateur, traces et pager de production restent
hors de sa portée.
