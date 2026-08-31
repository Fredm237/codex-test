# FILON — KEEP / REFACTOR / REWRITE / ARCHIVE

Cette matrice est une décision de trajectoire, pas une autorisation de suppression immédiate. **ARCHIVE** signifie : retirer du chemin actif après preuve d'absence d'appelants, conserver l'historique Git et prévoir un rollback. **DELETE** n'est autorisé qu'après une période d'observation et une décision enregistrée.

## KEEP — conserver et renforcer

| Actif | Pourquoi il a de la valeur | Renforcement obligatoire |
|---|---|---|
| Ingestion Awin, validation EAN, `merchants`, `catalog_sync_runs` | Source partenaire réelle et traçabilité de synchronisation déjà présentes | Raw payload immuable, replay, quarantaine, freshness et erreurs typées |
| `offers` et `price_snapshots` | Offer Graph partiel et historique réel | Money décimal, stock tri-state, shipping unknown, provenance champ par champ |
| `intelligence_product_facts`, `relations`, `traces`, `feedback`, `benchmarks` | Bonne base pour evidence, explication et apprentissage contrôlé | Relier à Observation/ContractVersion, imposer l'éligibilité des claims |
| Abstention sans cartes fictives dans `services/recommend.py` | Le repli `_synth` retourne désormais une absence explicite, pas une offre inventée | Renommer en `verified_absence`, supprimer le vocabulaire ambigu et tester tous les clients |
| Health checks, cache, feature flags | Fondations opérationnelles utiles | SLO, métriques par étape, clés de cache versionnées, fail-closed |
| `filon-web` | Surface canonique cohérente avec le mandat | Consommer des contrats générés et afficher les inconnus sans les embellir |
| `filon-extension` | Surface légère qui redirige vers le produit canonique | Tests d'intégration, permissions minimales, contexte sourcé |
| Orchestrateur `.claude/agent` | Mémoire versionnée et exigence de preuve | Remplacer la mission obsolète par le programme Phase 0 |

## REFACTOR — préserver le comportement, changer les frontières

| Actif | Problème | Découpage cible | Compatibilité / rollback |
|---|---|---|---|
| `api/routes/catalog.py` | Route monolithique : lecture, admin, jobs et maintenance | `catalog/query`, `catalog/admin`, `ingestion/jobs`, services applicatifs | Conserver les URLs v1 via façades ; bascule endpoint par endpoint |
| Search (`search.py`, `catalog_search.py`, `relevance.py`) | Rappel, contraintes, règles de cas et ranking entremêlés | Candidate Generator, Constraint Engine, Ranker, Evidence Assembler | Shadow run et comparaison de top-k avant bascule |
| Décision (`services/decision.py`, `verdict.py`, `recommend.py`) | Plusieurs sorties et sémantiques de verdict | Decision Engine commun et explainable | Adaptateurs v1 ; ancien moteur activable par feature flag |
| Intelligence générale / Fashion | Duplique intention, catalogue et décision | Client du core avec plug-in de domaine borné | Feature flags restent OFF jusqu'aux gates core |
| Taxonomie | Gros fichier procédural et correctifs par marchand | Service versionné, règles déclaratives et modèles évalués | Exécuter v1/v2 en parallèle ; ne publier que les écarts qualifiés |
| Web et mobile | Types et defaults écrits à la main | SDK généré depuis contrats versionnés | Conserver l'ancien client une release ; comparer les payloads |
| Serveur mobile | BFF utile mais contient un second backend | Auth/Profile/collections seulement, aucune vérité produit | Proxy progressif vers core ; double lecture instrumentée |
| CI GitHub | Uniquement backend et paths filtrés | Required checks multi-surfaces + quality lab | D'abord non bloquant, puis required après stabilité |

## REWRITE — remplacer avec migration explicite

| Actif / concept | Pourquoi le refactor ne suffit pas | Remplacement | Migration sûre |
|---|---|---|---|
| Identité `catalog_products` fondée sur EAN | Ne représente ni Brand, Family, Model, Variant ni identifiants multiples | Product Graph canonique et Identity Resolution | Nouvelles tables, backfill, liens shadow, revue des merges, double lecture |
| Valeurs money en float | Erreurs d'arrondi et contrat non monétaire | `Money(amount_decimal, currency)` | Colonnes parallèles, conversion contrôlée, checksum, cutover |
| Defaults `delivery_cost=0.0`, `in_stock=True` | Transforment l'absence de preuve en promesse | Types `Unknown/Observed` et champs nullables sans défaut positif | Nouveau contrat v2, adaptateur v1 fail-closed, tests de non-invention |
| `create_all` + migration SQL au startup | Migrations non auditables et erreurs ignorées | Alembic et job de migration séparé du runtime | Baseline du schéma, migrations expand/contract, sauvegarde et downgrade testé |
| Contrats Pydantic/dataclass/TS concurrents | Sémantique divergente entre surfaces | Registre de contrats versionné + SDK générés | Compatibility suite et fenêtre de dépréciation |
| Profile utilisateur fragmenté | PostgreSQL historique, MySQL mobile et stockage local sans propriétaire unique | Profile Service commun et consent-aware | Inventaire des données, mapping d'identité, double écriture, réconciliation |
| Règles de qualité fondées sur quelques cas | 14 cas golden ne mesurent pas le graphe ni le ranking | Quality Lab indépendant et datasets versionnés | Commencer en shadow ; rendre bloquant seulement après baseline stable |

## ARCHIVE — sortir du chemin actif

| Actif | Justification | Précondition | Rollback |
|---|---|---|---|
| `filon-site` | Ancien site statique, aucune donnée canonique, séquences et claims non vérifiables | Vérifier DNS, Vercel et liens entrants ; capturer une archive | Tag Git + artefact statique |
| SmartWave Quant Lab à la racine | Produit distinct qui brouille build, dépendances et ownership | Confirmer absence de job/déploiement ; identifier son dépôt cible | Branche/tag d'archive avant extraction |
| `agents/*` métier historique | Décision/recherche en double | Graphe des imports à zéro et parity du Decision Engine | Feature flag et restauration du package pendant une release |
| SerpAPI dans le parcours catalogue | Donnée non partenaire incompatible avec la promesse vérifiée | Confirmer aucun endpoint produit dépendant ; test fail-closed | Conserver adaptateur isolé, désactivé, une release |
| Documents d'audit datés utilisés comme instructions | Sources historiques devenues contradictoires | Nouvel index d'architecture adopté | Historique Git |

## DELETE — aucun élément autorisé en Phase 0

La Phase 0 ne supprime ni table, ni route, ni dossier produit. Une suppression future exige : preuve d'absence d'appelants, migration terminée, période d'observation, rollback documenté et ADR accepté.

## Ordre des dépendances

```text
contrats v1 figés
  ├─→ Quality Lab et datasets
  ├─→ migrations Alembic
  └─→ Observation/Evidence
          └─→ Product + Variant Graph shadow
                  └─→ retrieval/ranking/decision unifiés
                          └─→ clients générés
                                  └─→ archives et suppressions
```
