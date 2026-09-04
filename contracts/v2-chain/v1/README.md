# V2 Chain online reader v1

Ce contrat décrit la première sortie canary qualifiable de la chaîne atomique
P5 → P10. La version `v1` autorise uniquement `ABSTAIN` : aucun produit, offre,
classement, probabilité ou conseil BUY/WAIT n'est servi tant que son type de
réponse n'a pas franchi ses propres observations et gates.

La requête n'est jamais renvoyée ni conservée. Seul son digest SHA-256 permet de
relier les six étapes. Chaque étape doit fournir son digest de résultat. Le
routeur canary conserve Core v1 comme réponse atomique de repli en cas d'erreur,
d'incomplétude ou de type non qualifié.

Le reçu canary séparé mesure la source effectivement servie et les latences des
deux lecteurs. Il ne contient ni requête, ni digest de sujet, ni liste de
candidats. Une réponse V2 exige une chaîne et une provenance complètes ; tout
autre état conserve Core v1 avec un motif de fallback neutre.

Le contrat `v2-canary-eligibility-decision/v1` ferme le périmètre avant tout
appel au lecteur V2. Verticale, locale et type de décision doivent appartenir
à une politique explicitement digestée ; les dépendances doivent être
admissibles, les données fraîches, les inconnues critiques et violations de
contraintes absentes, la confiance suffisante lorsqu'elle est requise et le
rollback disponible. Tout échec sert Core v1 sans appeler V2.

Le contrat `v2-shadow-qualification/v1` est le reçu d'entrée en canary. Il
dérive ses compteurs du journal d'exécution et du lecteur sombre, déduplique
les replays identiques, refuse les trous de curseur et lie chaque preuve
externe à un digest SHA-256. L'exemple autorise seulement `ABSTAIN` ; les types
non observés restent explicitement OFF.

Le contrat `v2-public-qualification/v1` ferme la seconde promotion. Il exige
un reçu SHADOW → CANARY autorisé, un échantillon apparié minimal, un support
minimal pour chaque type demandé, zéro fallback V2, une provenance complète et
un p95 de latence V2 non supérieur à Core. Les preuves d'exploitation et de
rollback sont elles aussi liées par digest.

Le contrat `v2-runtime-authorization/v1` est la dernière frontière avant une
lecture promue. Le déploiement désigne un reçu append-only exact ; le runtime
revérifie en base ses gates, ses preuves, les types autorisés et, en mode
`public`, la filiation avec le reçu canary source. Une configuration seule,
un reçu `HOLD`, un digest absent ou une partition de types incomplète échoue
fermé avant toute lecture V2.

Le contrat `v2-promotion-command-receipt/v1` décrit la sortie neutre de la
commande privée qui calcule puis persiste ces reçus. Le dry-run ne retourne
aucun identifiant de ligne ; l'apply et son replay identique retournent la
ligne append-only créée ou retrouvée. Aucun payload brut ne fait partie du
contrat.

Le contrat `v2-promotion-proof-persistence/v1` décrit une référence de preuve
externe enregistrée avant qualification. Le digest lie la portée exacte
(campagne shadow ou gate canary), le type de preuve, un localisateur
opérationnel sûr, le digest de l'artefact, la version du vérificateur, le
verdict et l'instant. Les gates résolvent ces lignes en base ; un digest absent,
rejeté, d'un autre type ou d'une autre portée reste faux. Aucun contenu brut
n'est persisté.

Le contrat `v2-shadow-schedule-receipt/v1` borne l'interface du Cron privé et
de sa commande de récupération. Il distingue explicitement une ingestion
catalogue active, un lease V2 actif, un lease terminé `interrupted`, une
fenêtre fraîche, une fenêtre due et un succès. Le heartbeat n'apparaît que
pour un lease actif. Une reprise identifie le run interrompu dont elle conserve
l'instant, la borne et les checkpoints ; un échec demande une intervention.
Le reçu affirme toujours `raw_payload_retained=false`.
