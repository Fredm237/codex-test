# FILON — POST_PHASE_0_HARDENING

- Créé le : **31 août 2026**
- Statut : **backlog non bloquant pour Phase 1**
- Autorité : [décision de timebox Phase 0](PHASE_0_TIMEBOX_AND_EXIT_DECISION.md)

Ces travaux améliorent l'exploitation, mais leur absence ne rend pas Product
Identity dangereux avec les volumes et l'architecture actuels.

| Travail | Valeur | Condition de reprise | Gate Phase 1 |
|---|---|---|---|
| Déployer Prometheus multi-réplica | Agrégation et historique métrique | Deuxième réplica ou besoin d'historique durable | Non |
| Importer et enrichir Grafana | Diagnostic visuel | Exploitation régulière par une équipe | Non |
| Déployer un backend OTLP | Traces interservices conservées | Plusieurs services métier ou incident non explicable par logs | Non |
| Définir la rétention avancée | Maîtrise coût/audit | Volumes et obligations réelles mesurés | Non |
| Ajouter un pager secondaire | Redondance de notification | Astreinte ou équipe d'exploitation formalisée | Non |
| Générer du trafic représentatif | Calibration et SLO | Parcours Phase 1 stables et trafic disponible | Non |
| Ratifier des SLO | Engagement de service | Baseline représentative disponible | Non |
| Optimiser coût et débit d'ingestion | Réduction durée/coût | Après checkpoints fiables et mesures terminales | Non, sauf menace de capacité/intégrité |
| Infrastructure hyperscale | Capacité future | Charge observée qui la justifie | Non |
| Exercices périodiques de notification/restauration | Assurance opérationnelle continue | Cadence post-lancement | Non après le premier restore déjà qualifié |

Chaque item peut redevenir bloquant uniquement avec une preuve nouvelle qu'il
menace directement l'intégrité ou la récupérabilité. Une préférence technique
ou une amélioration possible ne suffit pas.
