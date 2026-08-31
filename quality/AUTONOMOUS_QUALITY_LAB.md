# FILON — Autonomous Quality Lab

- Décision fondatrice : 31 août 2026
- Statut : `AUTONOMOUS_QUALITY_LAB`
- Limitation : `NO_EXTERNAL_HUMAN_GROUND_TRUTH`
- Ancienne gate : conservée comme historique, remplacée et non satisfaite
- Effet : P0.2 peut être fermé sur des preuves autonomes ; Immersive reste NO-GO

## Ce que la gate prouve

La gate autonome n'accepte comme vérité bloquante que des résultats dont
l'oracle est calculable sans jugement subjectif : checksum GTIN/EAN,
identifiant global exact, non-fusion d'identifiants différents, rattachement
exact d'une offre, parsing de prix, devise supportée, stock tri-state,
fraîcheur, budget, abstention et inconnues explicites. Le golden set historique
est conservé sous le statut `REGRESSION_GROUND_TRUTH`, jamais sous celui d'une
vérité humaine indépendante.

Le holdout adversarial est généré par
`filon-adversarial-holdout/v1` avec plusieurs seeds versionnées. Il couvre les
identifiants invalides ou contradictoires, un même modèle avec stockage et
couleur différents, les faux rattachements, les budgets dépassés, les mauvaises
devises, le stock absent, les observations périmées et la livraison inconnue.
Le moteur applicatif ne reçoit que les entrées ; les oracles sont calculés par
les invariants du laboratoire.

## Statuts publiés

| Statut | Sens | Bloquant |
|---|---|---:|
| `DETERMINISTICALLY_VERIFIED` | L'oracle est calculable et le moteur concorde | oui en cas d'échec |
| `CROSS_SOURCE_VERIFIED` | Au moins deux sources distinctes concordent | oui si le signal est mal représenté |
| `MODEL_JUDGED` | Jugement auxiliaire audité, jamais ground truth | non par défaut |
| `PROVISIONAL` | Mesure utile mais non indépendamment validée | non |
| `UNRESOLVED` | Contradiction ou ambiguïté laissée ouverte | non si l'abstention est correcte |

La concordance multi-source expose toujours `SOURCE_COUNT`,
`SOURCE_AGREEMENT` et `SOURCE_CONFLICT`. Un consensus n'est jamais promu en
preuve absolue. Un conflit doit rester `UNRESOLVED`; sa résolution silencieuse
fait échouer la gate.

## Juge modèle

Le juge modèle est désactivé pour la gate courante : tous les contrôles
bloquants disposent d'un oracle déterministe. S'il est activé ultérieurement,
le manifeste exige le modèle, sa version, le prompt, l'entrée, la sortie et la
confiance. Son résultat portera `MODEL_JUDGED` et ne deviendra jamais une vérité
cachée.

## Exécution

Depuis `filon-backend` :

```bash
python -m quality_lab.autonomous \
  --manifest ../quality/autonomous-manifest.json \
  --strict \
  --output ../quality-autonomous-report.json
```

La sortie stricte vaut 0 lorsque les gates objectives passent, 1 lorsqu'une
régression objective est détectée et 2 lorsque le manifeste ou l'intégrité du
laboratoire sont invalides. Le rapport contient une identité SHA-256 stable,
les cas, leur base de vérité, les conflits, les limites et le verdict P0.2.

GitHub Actions publie ce rapport avec le reçu historique du laboratoire externe.
Le reçu externe reste `not_ready`; il documente l'absence de ground truth sans
immobiliser le développement.
