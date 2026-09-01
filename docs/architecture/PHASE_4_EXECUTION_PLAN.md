# FILON — Phase 4 Product Ontology Execution Plan

- Préparation locale : **1er septembre 2026**
- Statut : **OUVERTE — PHASE 3 = GO**
- Gate d'entrée : Phase 3 P3H terminale
- Gate de sortie : **taxonomy / role benchmarks pass**
- Lecteurs publics : **NON PROMUS**
- Immersive : **NO-GO inchangé**

## Objectif

Remplacer progressivement la taxonomie plate comme cerveau produit par une
ontologie sourcée capable de représenter catégories, types, attributs, rôles,
relations et facettes métier. Les règles historiques restent disponibles comme
fallbacks et régressions, sans devenir une identité ni une relation canonique.

## Gates

| Gate | Exigence |
|---|---|
| Rôles | roster fermé, abstention explicite, aucun principal par défaut |
| Relations | cible canonique prouvée ou texte observé non promu |
| Taxonomie | concepts versionnés, mapping legacy auditable |
| Attributs | types, unités, provenance et conflits explicites |
| Facettes | use case, audience, compatibilité, style, matière, saison, occasion, fonction |
| Exactitude | benchmark adversarial taxonomy/role avec intervalles |
| Sécurité | faux rôle principal et fausse compatibilité sous budget strict |
| Compatibilité | aucun endpoint public modifié avant la revue de sortie |

## Séquence

1. P4A — figer le contrat Product Ontology.
2. P4B — auditer la couverture réelle et les rôles legacy.
3. P4C — ratifier les benchmarks taxonomy/role.
4. P4D — écrire les extracteurs et mappings versionnés.
5. P4E — ajouter la persistance expand-only et le writer shadow.
6. P4F — exécuter un replay réel borné puis idempotent.
7. P4G — publier exactitude, couverture, abstention et limitations.
8. P4H — tenir la revue de sortie vers Hybrid Retrieval.

## Avancement

| Lot | État | Preuve attendue |
|---|---|---|
| P4A — contrat | **terminé localement** | ADR-009, schéma, manifest et tests |
| P4B — baseline réelle | **agrégats préparés ; audit borné à compléter** | couverture catégories/rôles/relations/attributs |
| P4C — benchmark | **terminé localement** | 18 442 cas v1.1, oracle ratifié, legacy `UNSAFE` |
| P4D — extracteurs | **qualifié localement** | [extracteur fail-closed : 18 442 cas PASS](PHASE_4D_PRODUCT_ONTOLOGY_EXTRACTOR_REPORT.md) |
| P4E — schéma/writer | **terminé localement** | [migration `e6b4d8f0a2c5`, writer sec et idempotent](PHASE_4E_PRODUCT_ONTOLOGY_SHADOW_REPORT.md) |
| P4F — replay | à faire | lot production borné et idempotent |
| P4G — qualification | à faire | taxonomy/role gates terminales |
| P4H — revue | à faire | reçu Phase 4 et décision Hybrid Retrieval |

Phase 3 est terminale avec le verdict GO. Cette ouverture n'autorise encore ni
writer Product Ontology, ni replay production, ni promotion d'un lecteur
public avant les gates P4E à P4H.
