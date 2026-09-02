# Phase 13 — Rapport de qualification locale

Date : 2026-09-02

Périmètre : Mobile Barcode v1 et invariants existants de favoris, alertes,
collections et dressing.

## Résultat

**GO local pour P13A–P13E. NO-GO production pour P13F–P13G.**

| Preuve | Résultat |
|---|---|
| Benchmark barcode adversarial | **14/14**, pass rate 1,00 ; **0 faux code invalide accepté** |
| Tests ciblés scanner/API | **29/29** |
| Suite mobile complète | **337 réussis**, 4 intégrations explicitement ignorées, 0 échec |
| TypeScript | **PASS**, 0 erreur |
| ESLint | **PASS**, 0 erreur ; un avertissement de type de module de configuration |
| Lecteur shadow / writer produit / Cron | **absents** |

## Écart corrigé

La version précédente validait seulement la longueur numérique. Elle pouvait :

- envoyer au Core un checksum faux ;
- accepter les remplissages composés d'un seul chiffre ;
- interroger un UPC-A ou un GTIN-14 zéro-préfixé sous une clé différente de la
  clé EAN-13 canonique du backend ;
- accepter une réponse dont l'EAN ne correspondait pas à l'identité demandée.

Le normaliseur mobile applique désormais le même checksum et la même
canonicalisation que `catalog_grouping.normalize_ean`. L'adaptateur réseau
rejette une réponse d'identité contradictoire.

## État des capacités Phase 13

- **Scan** : code et états fail-closed qualifiés localement ; appareil réel non
  encore qualifié.
- **Comparaison instantanée** : lecteur Core existant ; ne rend actionnables que
  les offres fraîches avec devise, stock et preuve explicites.
- **Favoris/collections** : stockage local et synchronisation authentifiée déjà
  couverts par la suite ; aucune valeur de deep-link n'est une preuve.
- **Alertes** : seuil local persistant, synchronisation sérialisée et inscription
  push existantes ; le déclenchement distant reste dépendant du contrôle serveur.
- **Dressing** : fondation locale bornée à 40 pièces, rôles explicites,
  déduplication et assainissement ; ce n'est pas encore le Wardrobe Intelligence
  de Phase 15.

## Limites honnêtes

Ce rapport ne prouve ni la qualité optique de la caméra sur appareils physiques,
ni la délivrabilité push, ni un build EAS/App Store/Play Store, ni une promotion
production. Ces preuves constituent P13F et P13G et restent ouvertes.
