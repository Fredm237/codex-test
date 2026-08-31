# FILON — preuve isolée de l'évaluateur local d'alertes

- Date : 29 août 2026
- Politique : `local-alert-policy-v1`
- Commit testé : `8b6be85d1f45f228ef8ff87603873a73f54a1042`
Statut : **GO pour le moteur de décision local ; NO-GO pour une alerte de production**

## Périmètre prouvé

Le commit ajoute des fenêtres FIFO en mémoire sur les 512 derniers événements
HTTP, recommandations et étapes pipeline, puis une instance canonique
`evaluate_local_alerts()` qui évalue cinq règles provisoires. Il n'ajoute aucun
endpoint, ordonnanceur, exporteur, dashboard, sink réseau ou pager.

Les garanties couvertes sont :

- trois états seulement : `insufficient_data`, `not_firing_provisional` et
  `firing`, sans `healthy` ni `ok` ;
- seuils fermés, minima d'échantillon et hystérésis inclusive ;
- position `(generation, events_seen)`, reset distinct, replay ancien rejeté et
  conflit au même point fail-closed ;
- correction unique d'un agrégat invalide au même watermark, sans permettre à
  une position plus ancienne de résoudre le latch ;
- exclusions `cancelled` sans faux non-déclenchement quand elles dominent, tout
  en conservant une violation manifeste ;
- silence limité à une heure, raisons fermées, offset UTC réel, expiration sur
  observation neuve et horloge monotone contre les appels retardés ;
- déduplication par l'instance longue durée, ratios assez précis pour ne pas
  contredire visuellement les seuils ;
- cardinalité HTTP bornée, statuts invalides fail-closed et latences invalides
  rejetées avant toute mutation ;
- aucun rappel d'objet fourni par l'appelant sous les verrous d'état ;
- aucune requête, route, IP, entête, identifiant, payload, offre, exception, URL
  ou secret dans les entrées et sorties de l'évaluateur.

## Protocole isolé

1. Création d'un worktree Git détaché au commit exact ci-dessus.
2. Contrôle d'un `git status --short` vide et du SHA avant exécution.
3. Exécution sous Python 3.12.13 des tests alertes, observabilité et middleware.
4. Exécution de toute la suite backend dans ce même checkout détaché.
5. Trois relectures indépendantes, en lecture seule, des contrats, de la
   concurrence, de la confidentialité et des cas adversariaux.

## Résultats

- ciblé : **78 réussis, 0 échec** ;
- backend complet : **1 294 réussis, 0 échec**, en 157,78 s ;
- avertissements : 7 usages historiques de `datetime.utcnow()` dans le pulse
  catalogue et ses tests, hors changement de ce lot ;
- relectures : aucun bloquant ni défaut P2 restant après les corrections ;
- `git diff --check` : propre.

Les fichiers locaux appartenant à l'utilisateur (`filon-backend/README.md`,
`app/api/routes/catalog.py`, les trois fichiers MegaMenu/SearchAssistant, ainsi
que `.python-version` et `pyproject.toml`) sont restés hors du commit et hors de
la preuve revendiquée.

## Limites et sortie

Cette preuve ne mesure ni trafic représentatif, ni fenêtre temporelle, ni
agrégation multi-réplica. Elle ne ratifie aucun SLO et ne prouve aucune livraison
de notification. Le passage à une alerte opérationnelle exige encore :

1. un ordonnanceur ou appelant local contrôlé de l'instance canonique ;
2. des événements horodatés et une agrégation multi-réplica approuvée ;
3. un trafic représentatif pour ratifier ou remplacer les seuils provisoires ;
4. un export authentifié, un canal, un owner et une politique d'escalade ;
5. un exercice non productif de trigger, déduplication, silence, expiration,
   résolution et rollback.

Le lot ne comporte ni migration ni stockage. Revenir au parent `6c269ce` retire
les fenêtres et le moteur local sans toucher la readiness existante.
