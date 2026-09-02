# FILON — Phase 12A Extension Baseline

- Date : **2 septembre 2026**
- Branche locale : **`codex/filon-phase-12-extension`**
- Base empilée : **Phase 11F `941dbca`**
- Production : **inchangée**

## Current state

La fondation est bien Manifest V3, avec un service worker minimal, `activeTab`,
`storage` et des permissions hôtes bornées aux marchands déclarés. Avant Phase
12, le script détectait surtout un titre, affichait une surcouche puis ouvrait
une recherche FILON. Il ne capturait pas de contrat produit structuré et ne
pouvait pas ouvrir une fiche exacte par identifiant.

## Evidence

- Manifest V3 conservé ;
- aucun moteur de décision, ranking ou BUY/WAIT dans l'extension ;
- aucune télémétrie et aucune transmission automatique ;
- Core API déjà propriétaire des fiches produit exactes par EAN/GTIN ;
- CI existante vérifie contrat et syntaxe, désormais étendue au benchmark P12.

## Root causes

1. l'extraction JSON-LD ne conservait que `name` ;
2. SKU, MPN, GTIN, prix, devise, disponibilité et variante étaient perdus ;
3. une page avec GTIN exact retombait sur une recherche textuelle ;
4. aucun contrat ne bornait les données qui pourraient un jour rejoindre le
   Core ;
5. aucun benchmark ne mesurait l'abstention sur identifiant, prix ou URL
   dangereux.

## Before / after

| Mesure | Avant | Après P12A/P12B local |
|---|---:|---:|
| Champs produit structurés | 1 (`title`) | 12 champs bornés |
| Navigation par GTIN exact | non | oui, après action explicite |
| URL sans requête/fragment | non contractualisé | obligatoire |
| Prix sans devise accepté | non mesuré | 0/2 cas adversariaux |
| GTIN invalide accepté | non mesuré | 0/1 |
| Transmission automatique | 0 | 0 |
| Benchmark | absent | 12/12 |

## Qualification locale

- contrat et extracteur Extension : **2 suites vertes** ;
- benchmark adversarial : **12/12**, rappel GTIN exact 1,00, zéro
  identifiant invalide accepté, zéro prix non supporté accepté, zéro URL privée
  conservée et zéro transmission automatique ;
- projection et résolution Core : **17/17**, dont déterminisme, allowlist
  JSON-LD, horloge fail-closed, replay append-only sans doublon, GTIN exact,
  devise unique, fraîcheur et comparaison multi-marchands ;
- régression backend complète : **2 599 réussis, 3 ignorés** dans le bac à
  sable ; le seul test refusé par l'interdiction d'ouvrir un port loopback a
  ensuite réussi **1/1** hors de cette restriction. Aucun échec applicatif ne
  subsiste.

## Known limitations

1. Le corpus est synthétique et ne constitue pas une ground truth humaine
   externe.
2. L'observation structurée reste locale : aucun POST vers le Core n'est
   raccordé sans consentement nominatif sur le payload et sa destination.
3. La fiche FILON exacte peut encore répondre `unknown` si le Core ne possède
   pas ce GTIN ou aucune offre courante comparable.
4. Le zip historique du store n'est pas régénéré avant la qualification
   complète de la source.
5. Le résolveur exact Core est testé mais reste sans route HTTP : il ne peut
   recevoir aucun payload tant que le gate de consentement réseau est fermé.

## GO / NO-GO

- **P12A audit : GO local**.
- **P12B contrat et extraction : GO local**.
- **Projection et comparaison Core exactes : GO local, non raccordées au
  réseau**.
- **Constructeur package store : GO local ; archive finale non publiée**.
- **Transport d'observation vers le Core : NO-GO en attente d'autorisation
  explicite**.
- **Phase 12 production : NO-GO**.
