# FILON — pack d’agrégation OpenMetrics

Ce dossier prépare un scrape multi-réplica et un dashboard versionné sans
prétendre qu’ils sont déployés. Il ne contient ni secret, ni cible de
production, ni règle de pager, ni SLO. Tant que `targets/filon.json` reste
`[]`, Prometheus ne scrape rien.

## Contenu

- `prometheus/prometheus.yml` : scrape HTTPS authentifié, borné et sans query
  string ;
- `prometheus/rules/filon.rules.yml` : rollups de taux multi-réplica sur cinq
  minutes ;
- `prometheus/targets/filon.json` : inventaire vide fail-closed ;
- `schemas/prometheus-target-inventory.schema.json` : contrat fermé de
  l’inventaire ;
- `tools/target_inventory.py` : compilateur atomique de cet inventaire ;
- `schemas/prometheus-activation-receipt.schema.json` : contrat du reçu de
  preuve expurgé ;
- `tools/verify_prometheus.py` : vérificateur HTTPS de l’activation réelle ;
- `grafana/filon-core-observability.json` : dashboard classique importable,
  sans alerte ni seuil de santé.

Le modèle de dashboard classique reste importable par Grafana ; le datasource
Prometheus est choisi à l’import au moyen de la variable `DS_PROMETHEUS`.

## Montage attendu

Le collecteur doit voir les fichiers aux chemins exacts utilisés par la
configuration :

```text
/etc/prometheus/prometheus.yml
/etc/prometheus/rules/filon.rules.yml
/etc/prometheus/targets/filon.json
/run/secrets/filon_metrics_export_token
```

Le dernier fichier contient uniquement la valeur de
`METRICS_EXPORT_TOKEN`, sans préfixe `Bearer`, avec des permissions limitées au
compte du collecteur. Le token n’entre jamais dans Git, une URL, un label ou un
fichier de service discovery.

## Inventaire obligatoire des réplicas

Le service discovery doit écrire atomiquement un groupe par réplica. Exemple
documentaire, à remplacer par les noms internes réellement observés :

```json
[
  {
    "targets": ["replica-a.internal.example:443"],
    "labels": {
      "environment": "production",
      "cluster": "filon-eu",
      "replica": "replica-a"
    }
  }
]
```

Ne jamais mettre l’URL du load balancer dans cet inventaire : des scrapes
successifs pourraient atteindre des processus différents et rendre les
compteurs locaux incohérents. Le nombre de séries `up` doit être comparé au
nombre de réplicas déclaré par la plateforme. Une cible sans les trois labels
`environment`, `cluster` et `replica` est rejetée. Le collecteur conserve
uniquement les labels fermés du contrat ; tout label métrique nouveau est
supprimé jusqu’à une revue explicite du pack.

L’inventaire observé doit rester hors Git, puis être compilé avec le nombre
de réplicas lu sur la plateforme :

```bash
python -m observability.tools.target_inventory \
  /run/filon/observed-targets.json \
  /etc/prometheus/targets/filon.json \
  --expected-replicas 3
```

La commande refuse les URL, IP littérales, champs supplémentaires, labels
libres, doublons, groupes multi-cibles et inventaires partiels. Elle n’imprime
que le nombre de groupes et l’empreinte SHA-256 du contenu canonique, jamais
les hôtes internes. Un rejet laisse le fichier actif inchangé. L’état
désactivé exige `--allow-empty` au lieu d’un nombre attendu ; cette option
refuse symétriquement tout inventaire non vide.

## Validation avant activation

Le pack cible Prometheus **3.13.2 LTS**. Depuis une installation de cette
version :

```bash
promtool check config /etc/prometheus/prometheus.yml
promtool check rules /etc/prometheus/rules/filon.rules.yml
promtool test rules /etc/prometheus/rules/filon.rules.test.yml
```

Puis vérifier, sur un environnement autorisé :

1. un scrape avec le secret du coffre répond `200`, sans query string ;
2. un secret absent ou erroné échoue ;
3. chaque réplica possède une série `up` distincte ;
4. un redémarrage est traité comme un reset de compteur, jamais comme une
   guérison ;
5. les rollups portent uniquement `environment`, `cluster` et, pour le
   pipeline, `stage` ;
6. le dashboard n’affiche les percentiles locaux que par `instance` ; il ne
   calcule aucun percentile distribué fictif ;
7. la rétention, l’accès au datasource, le canal de notification et le
   rollback sont testés et consignés.

Conserver dans la preuve de déploiement le nombre de réplicas observé, le
fingerprint produit par le compilateur et le nombre de séries `up`. Une
empreinte locale sans ces deux comptes concordants ne prouve pas l’activation.

Une fois Prometheus accessible par un endpoint HTTPS authentifié, produire le
reçu de preuve avec un token de lecture dédié stocké uniquement dans
`PROMETHEUS_VERIFY_TOKEN` :

```bash
python -m observability.tools.verify_prometheus \
  --url https://prometheus.internal.example \
  --environment production \
  --cluster filon-eu \
  --expected-replicas 3 \
  --report /run/filon/prometheus-activation-receipt.json
```

Ce token protège l’API du collecteur et reste distinct du
`METRICS_EXPORT_TOKEN` lu par le collecteur pour scraper FILON. Le vérificateur
refuse les redirections, URL non HTTPS ou porteuses de credentials, mauvaises
versions, roster de règles modifié, cibles dupliquées/en panne/anciennes et
rollups sans série. Le reçu contient les comptes, le roster et une empreinte
des identités, jamais les noms de réplicas, instances, URL ou tokens. Il ne
prouve ni Grafana, ni le pager, ni la rétention, qui gardent leurs validations
propres.

Les ratios du dashboard sont descriptifs. Aucun seuil provisoire de
`LOCAL_ALERT_POLICY.md` n’est promu en règle distante avant trafic
représentatif, ratification et test du canal/pager.

## Rollback

Retirer le job `filon-backend`, les règles et le dashboard du collecteur, puis
recharger sa configuration. Cette opération ne modifie ni l’application, ni la
base, ni les migrations. Garder l’export applicatif désactivé en supprimant
`METRICS_EXPORT_TOKEN` si aucun collecteur approuvé ne le consomme.
