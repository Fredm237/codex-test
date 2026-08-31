# FILON — Phase 1 Product Identity Execution Plan

- Ouverture : **31 août 2026**
- Statut : **FERMÉE — GO**
- Entrée : [PHASE 0 = GO](PHASE_0_FINAL_RECEIPT.md)
- Gate de sortie : **exact-product benchmark passes**
- Immersive : **NO-GO inchangé**

## Objectif

Construire l'identité produit canonique de FILON sans modifier prématurément
les lectures publiques : `Brand → ProductFamily → ProductModel → Variant`,
avec identifiants et provenance explicites. Les shadows de Phase 0 sont le
point de départ, pas une preuve que la Phase 1 est déjà terminée.

## Périmètre

1. Figer le contrat d'identité v1 et les invariants Brand/Family/Model/Variant.
2. Auditer les données Awin réelles par verticale et mesurer identifiants,
   attributs, duplications, collisions et inconnus.
3. Étendre le modèle en migration expand-only, avec rollback et flags off.
4. Construire une projection déterministe et idempotente conservant la
   provenance de chaque identité et attribut.
5. Établir un benchmark exact-product autonome, reproductible et adversarial.
6. Exécuter le backfill d'abord en dry-run, puis sur un lot borné en shadow.
7. Mesurer faux merges, faux splits, couverture et abstention ; corriger sans
   inventer de confiance subjective.
8. Tenir la revue de sortie Phase 1 avant toute promotion de lecteur public.

## Premières verticales

Le mandat recommande de commencer par trois à cinq verticales structurées :

- smartphones ;
- laptops ;
- TV ;
- headphones/audio ;
- appliances.

La sélection finale doit être fondée sur la couverture réelle des données
Awin, pas sur une préférence de démonstration. Fashion reste hors promesse de
production pendant cette phase.

## Gates

| Gate | Exigence |
|---|---|
| Identité exacte | un GTIN valide et non contradictoire peut produire une correspondance exacte |
| Faux merge | aucun conflit d'identifiant ou de variante ne peut être fusionné favorablement |
| Provenance | toute identité et tout attribut portent leur source et leur observation |
| Unknown | l'absence de preuve reste inconnue et n'est jamais transformée en correspondance |
| Idempotence | deux projections du même corpus produisent le même état shadow |
| Réversibilité | migrations expand-only, flags off et rollback documenté |
| Compatibilité | contrats et lectures Core v1 inchangés pendant le shadow |
| Benchmark | le benchmark exact-product versionné passe ses seuils ratifiés |

## Séquence immédiate

1. Baseline réelle et inventaire des champs d'identité Awin.
2. ADR Phase 1 sur les frontières Brand/Family/Model/Variant.
3. Contrats, fixtures adversariales et scorecard exact-product.
4. Migration expand-only et writers shadow.
5. Backfill dry-run borné, rapport de collisions et quarantaine.
6. Benchmark, CI, revue indépendante et reçu Phase 1.

## Avancement

| Lot | État | Preuve |
|---|---|---|
| P1A — baseline réelle | **terminé** | [couverture, collisions et verticales](PHASE_1A_PRODUCT_IDENTITY_BASELINE.md) |
| P1B — frontières d'identité | **terminé** | [ADR-006](ADR-006-PRODUCT-IDENTITY-V1-BOUNDARIES.md) + contrats JSON v1 |
| P1C — benchmark exact-product | **terminé** | [10 565 checks, cinq gates verts](PHASE_1C_EXACT_PRODUCT_BENCHMARK_REPORT.md) |
| P1D — schéma/writers shadow | **qualifié en production** | [migration, assertions et rollback](PHASE_1D_PRODUCT_IDENTITY_SHADOW_REPORT.md), schéma `b3e1a7c4d9f2` |
| P1E — backfill réel borné | **terminé** | [dry-run, application, replay idempotent et totaux PostgreSQL](PHASE_1E_PRODUCT_IDENTITY_BACKFILL_REPORT.md) |
| P1F — qualification des gates | **terminé** | [benchmark, invariants réels et CI](PHASE_1F_PRODUCT_IDENTITY_QUALIFICATION_REPORT.md) |
| P1G — revue de sortie | **terminé — GO** | [reçu final Phase 1](PHASE_1_FINAL_RECEIPT.md) ; Phase 2 ouverte |

Le durcissement SRE post-Phase 0 et la surveillance du premier événement
GitHub `schedule` continuent parallèlement. Ils ne bloquent pas Product
Identity sauf nouvelle preuve d'un risque réel pour l'intégrité ou la
récupérabilité.
