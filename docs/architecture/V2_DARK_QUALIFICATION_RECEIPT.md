# FILON — Reçu de qualification V2 DARK

- Qualification : **SHADOW et DARK qualifiés pour un canary fermé `ABSTAIN` uniquement**
- Campagne : `sha256:1f96acc4650db96c92d1878c084ff91e8eb14b00b18de541fe98913fba46088d`
- Révision déployée : `3fb33d5a776511ca8da3c16876715aa5fa3cc79c`
- Déploiement Railway actif : `4c4fed4d-f355-4b5a-8211-e86c4258e555`
- Schéma : `f9c7d1e3a5b8`
- Évidence canonique : `docs/architecture/V2_DARK_QUALIFICATION_EVIDENCE.json`

## État public

Le frontend Phase 19 est public. Le backend V2 est actif en mode `dark` : les
writers shadow P0/P1–P10 sont ON, le lecteur DARK observe sans influencer les
réponses, et Core V1 reste l'unique source servie aux utilisateurs. Les
lecteurs canary et public V2 sont OFF.

Les sondes `live`, `ready` et `health` répondent HTTP 200. PostgreSQL et Redis
sont `ok`. Aucun lease V2 n'est actif.

## Preuve SHADOW

La campagne possède 30 fenêtres `progression` distinctes, terminales,
contiguës et non concurrentes. Le curseur `smartphones` avance de `0` à `129`,
sans échec ni interruption. Le p95 des seules fenêtres de progression est de
28 282 ms, sous la politique mesurée de 30 000 ms.

L'apply `4` et son replay exact `5` partagent l'identité
`sha256:7d701379fec01f8eb218b95f1f728ef6d15ae13c85987986fdbc9f0e65c5a07b`.
Le replay n'a ni avancé le curseur ni créé une seconde fenêtre réelle.

## Preuve DARK

Trente requêtes de qualification ont traversé le vrai chemin de production
`/api/advise`. Elles ne sont pas présentées comme du trafic humain organique.
Les 30 observations sont éligibles et complètes ; aucune n'est invalide et
aucun texte de requête n'est retenu. V2 n'a influencé aucune réponse V1.

Le seul type réellement observé et sûr est `ABSTAIN`. `BUY_NOW` et `WAIT`
restent explicitement hors périmètre.

## Preuve de retour V1

Le mode a été ramené de `dark` à `shadow`, puis une requête a obtenu HTTP 200.
Le nombre d'observations DARK est resté exactement à 30, démontrant que le
lecteur DARK ne s'exécutait plus et que V1 restait servi. Le mode `dark` a
ensuite été rétabli par le déploiement actif
`4c4fed4d-f355-4b5a-8211-e86c4258e555`, avec les lecteurs canary/public OFF.

## Preuves externes

Le run GitHub Actions Phase 19.5 `33915302430` est terminal et vert. Il couvre
notamment la tête Alembic unique, la migration PostgreSQL additive/réversible,
les benchmarks hérités, les invariants fail-closed, la collision de scheduler,
l'interruption stale explicite, la reprise de la fenêtre et des checkpoints,
le routage DARK non influent et les refus de promotion sans preuves.

Le run `main` `33917900695` et le moniteur planifié `33915260578` sont également
terminaux et verts.

## Frontière de promotion

Ce reçu ne déclare ni CANARY ni PUBLIC. Il constitue l'artefact immuable à
enregistrer dans le registre append-only. Après résolution de toutes les
références, le gate peut autoriser uniquement une cohorte fermée `ABSTAIN`.
Core V1 demeure le fallback intégral. La promotion de `BUY_NOW` ou `WAIT` exige
des observations propres et n'est pas couverte par ce reçu.
