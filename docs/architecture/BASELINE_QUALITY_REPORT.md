# FILON — Baseline Quality Report

Date : 28 août 2026
Référence : `Fredm237/codex-test` / `main` / `57724c72e77c50ca54aaf64338f838dda3be2747`
Dernier contrôle ajouté : 29 août 2026

## 1. Conditions de mesure

La copie locale contenait avant l'audit sept changements utilisateur non commités : cinq fichiers modifiés et deux fichiers backend non suivis. Ils ont été conservés et ne font pas partie de ce dossier. Les résultats locaux décrivent donc **la copie de travail basée sur le commit de référence**, pas un checkout immaculé du commit.

La vieille virtualenv backend utilisait Python 3.9 et provoquait 37 erreurs de collecte sur des syntaxes/types nécessitant une version récente. Ce n'est pas classé comme régression produit : la mesure officielle a été reprise dans un environnement temporaire Python 3.12.13, conforme au workflow et au `pyproject.toml` local.

Les sections 2 à 15 conservent les mesures historiques au moment où elles ont
été prises. La qualification distante courante est consignée en section 16 ;
elle ne réécrit pas les résultats antérieurs.

## 2. Résultats reproductibles

| Surface | Contrôle | Résultat | Durée / détails | Statut |
|---|---|---|---|---|
| Backend local | Suite Pytest complète, Python 3.12.13 | **1 186 réussis**, 0 échec | 81,15 s ; 4 warnings `datetime.utcnow()` | VERT technique |
| Backend GitHub | Workflow « Qualité catalogue backend » | **1 186 réussis**, 0 échec | 48,50 s ; 7 warnings, run du commit backend `368e8134…` | VERT mais pas sur le HEAD mobile actuel |
| Web | `npm test` | **17 réussis**, 0 échec | Tests MegaMenu seulement | VERT, couverture étroite |
| Web | Build production Next.js | Build et typecheck réussis, 42 routes générées | Plusieurs `ENOTFOUND` vers l'API Railway pendant la génération statique ; exit 0 via fallbacks | ORANGE |
| Mobile | Vitest complet | **110 réussis, 4 échoués, 1 ignoré** | 50 fichiers, 115 tests, 24,63 s | ROUGE |
| Mobile | TypeScript `--noEmit` | 0 erreur | Contrôle terminé sans sortie | VERT technique |
| Mobile | ESLint | **2 erreurs, 25 warnings** | Deux appels conditionnels de hook React ; 15 warnings auto-corrigeables | ROUGE |
| Extension | Syntaxe JS + manifeste Manifest V3 | 3 fichiers JS valides, manifeste version 1.0.0 lisible | Aucun test fonctionnel | ORANGE |

### Analyse des quatre échecs mobile

| Test | Cause observée | Classement | Action Phase 0 |
|---|---|---|---|
| `expo-authentication.test.ts` | `EXPO_TOKEN` absent | Configuration externe | Séparer tests unitaires et smoke tests secrets ; skip explicite et justifié |
| `eas-project-link.test.ts` | identifiant EAS absent | Configuration externe | Contrat de configuration validé au démarrage/CI dédiée |
| `eas-project-id.test.ts` | `EXPO_PUBLIC_EAS_PROJECT_ID` vide | Configuration externe | Même traitement ; ne pas appeler le réseau dans la suite hermétique |
| `filon-occasion-reminders.test.ts` | attendu `18:00`, résultat ISO UTC `16:00` en Europe/Brussels | Défaut de test/fuseau réel | Spécifier timezone et comparer des instants, pas une heure locale encodée |

Le build web qui réussit malgré une API inaccessible prouve une bonne dégradation d'affichage, mais ne valide ni les contrats live ni la fraîcheur des données. Il doit rester vert tout en déclenchant un contrôle contractuel séparé et visible.

Le lint mobile détecte deux violations réelles de l'ordre des hooks React dans `follow-up-timeline.tsx` et `intent-decision-timeline.tsx`, plus 25 warnings. Le typecheck seul ne peut pas détecter ce défaut d'exécution.

## 3. Ce que les 1 186 tests backend ne mesurent pas

Le volume de tests est élevé, mais il est dominé par des régressions de taxonomie et des cas marchands. Le fichier golden `tests/data/golden_catalog_v1.json` contient seulement **14 cas**. Il vérifie des catégories/offer kinds et quelques attentes sémantiques ; il ne fournit pas une mesure indépendante des points suivants :

- précision/rappel de l'Entity Resolution ;
- taux de faux merge et faux split par catégorie, langue et marchand ;
- exactitude Variant (taille, couleur, capacité, bundle, état) ;
- attachement d'une offre à la bonne variante ;
- recall@k, NDCG@k et hard negatives de retrieval ;
- violation de contraintes dans les résultats ;
- calibration des confidences et taux d'abstention correct ;
- couverture et fraîcheur de l'evidence par claim ;
- latences P50/P95/P99 par étape et sous charge ;
- dérive des données ou comparaison train/dev/test.

Conclusion : **vert technique, qualité produit inconnue**. Aucun pourcentage de qualité produit ne peut être annoncé à partir de la suite actuelle.

## 4. Invariants observés à la baseline, puis suivis

| Invariant du mandat | Observation | Sévérité |
|---|---|---|
| Unknown est une valeur de premier rang | À la baseline, les valeurs absentes de livraison et de stock recevaient des défauts positifs. Le Core, le catalogue, l'Assistant et les clients mobiles/web sont désormais intégrés fail-closed sur preuve, fraîcheur, devise et stock | Critique à la baseline ; invariant technique acquis dans `4a95a42` et `90246b2`, qualité métier encore non mesurée |
| Money n'est jamais un float naïf | Prix/coûts en `Float`/`number` dans DB et contrats | Critique |
| Toute décision s'appuie sur evidence | L'Assistant exige le marqueur explicite et revalide ses cartes depuis `1a167dc` ; le backend catalogue protégé ne satisfait pas encore tout le contrat client | Critique |
| Un Product Graph canonique existe | `catalog_products` est un regroupement EAN, sans Family/Model/Variant | Critique |
| Migrations explicites | `create_all` et SQL ad hoc au démarrage, échec parfois ignoré | Critique |
| Un seul cerveau produit | Search/decision/contracts dupliqués backend, intelligence et mobile | Élevée |
| CI protège toutes les surfaces | Un workflow backend seulement, filtré par paths | Élevée |
| Branche principale gouvernée | `main` observée non protégée sur GitHub | Élevée |
| Tests clients hermétiques | Trois tests mobile requièrent configuration/réseau | Moyenne |
| Temps et fuseaux explicites | Un test rappel casse selon la représentation UTC | Moyenne |

## 5. État GitHub observé

- Le dépôt public accessible sous `Fredm237` est `Fredm237/codex-test` ; `filon-web` y est le frontend canonique.
- `main` n'est pas protégée.
- Le workflow unique ne se déclenche que pour `filon-backend/**` ou son propre fichier ; les changements web, mobile, extension, contrats transverses et migrations hors chemin ne sont pas couverts.
- La PR brouillon #384 durcit CORS et schémas du serveur mobile, mais ne résout pas la duplication du backend ; elle doit être rebasée sur les décisions de frontière avant merge.
- La PR #96, encore ouverte et ancienne, contient un audit backend qui doit être classé comme historique ou revalidé ; elle ne peut pas servir de baseline actuelle.
- Un statut Vercel réussi est visible, mais ne remplace pas les quality gates.

## 6. Registre de risques initial

| Risque | Probabilité | Impact | Signal précoce | Mitigation Phase 0 |
|---|---|---|---|---|
| Faux merge produit/variante | Élevée | Critique | Prix incompatibles dans un groupe, attributs contradictoires | Dataset hard-negative, merge conservatif, revue et shadow |
| Claim positif issu d'un unknown | Avéré à la baseline ; régression couverte localement | Critique | Total livré, économie ou stock positif sans source | Contrat fail-closed, tests d'invariant et holdout indépendant à constituer |
| Migration DB non récupérable | Élevée | Critique | SQL au startup, divergence de schéma | Alembic, backup, upgrade/downgrade CI |
| Régression client non détectée | Élevée | Élevé | Merge mobile/web sans workflow | Matrice CI et checks requis |
| Build web masque API cassée | Avéré | Élevé | `ENOTFOUND` avec exit 0 | Smoke contractuel séparé, métrique freshness visible |
| Dette de règles taxonomie croissante | Élevée | Élevé | Nouveau fichier/cas par marchand | Quality Lab indépendant et règles versionnées |
| Second cerveau mobile diverge | Élevée | Élevé | Types/defaults et DB propres | Ownership explicite, SDK commun, BFF borné |
| Secrets requis dans tests unitaires | Avéré | Moyen | Suite rouge hors environnement privilégié | Séparer unit/integration/smoke et documenter prérequis |

## 7. Verdict des gates actuelles

| Gate | État | Motif |
|---|---|---|
| Build / tests de base | VERT LOCAL | Backend propre : 1 795 tests ; web propre : typecheck, gates bornés et build ; mobile : 166 tests, 4 smoke skips, typecheck vert, ESLint 0/15. Le `npm test` web complet reste borné à la copie de travail ; aucune preuve CI distante |
| Product Graph | ROUGE | Absent |
| Variant Graph | ROUGE | Absent |
| Offer Graph | ORANGE | Contrats clients durcis, mais backend catalogue protégé non intégré et qualification réelle des observations incomplète |
| Retrieval | ROUGE | Pas de benchmark indépendant |
| Evidence | ORANGE | Éligibilité explicite imposée dans les clients (`evidence_current`, `observed_at` ≤ 72 h), mais production et backend catalogue non qualifiés |
| Decision | ROUGE | Moteurs concurrents et calibration inconnue |
| Core UX | ORANGE | Web/mobile fail-closed et validations locales vertes, mais contrat catalogue protégé et données live non validés de bout en bout |
| Gouvernance livraison | ROUGE | Main non protégée, CI partielle |
| Immersive / 3D | BLOQUÉ | Gate d'entrée explicitement non satisfaite |

**Décision : NO-GO hors Phase 0.**

## 8. Contrôle après P0.b — contrats et unknown

Mesure du 28 août 2026 après introduction de `contracts/v1` :

| Contrôle | Résultat |
|---|---|
| Backend complet | **1 191 réussis**, 0 échec, 4 warnings |
| Backend contractuel ciblé | 20 réussis, 0 échec |
| Web | 17 tests application + compatibility contract réussis ; build 42 routes réussi avec les mêmes `ENOTFOUND` Railway |
| Mobile contractuel ciblé | 12 réussis, 0 échec |
| Mobile complet | **111 réussis, 4 échoués, 1 ignoré** : exactement les quatre écarts de baseline, aucune nouvelle régression |
| Mobile typecheck | Réussi |
| Mobile lint | Toujours 2 erreurs et 25 warnings préexistants |
| Extension | Contrat v1 et syntaxe des trois scripts réussis |

Corrections d'invariant livrées : `delivery_cost` et `in_stock` ont `None` comme défaut ; le comparateur exige désormais `in_stock is True` ; une livraison inconnue n'est plus annoncée « tout compris » ; le web distingue les trois états ; le catalogue de démonstration ne peut plus servir de réponse API, même sans base configurée.

Le gate global reste rouge : Product/Variant Graph, Quality Lab, migrations et CI complète ne sont pas encore livrés, et les écarts mobile de baseline restent ouverts.

## 9. Contrôle après préparation de P0.g — CI multi-surfaces

Les écarts mobile de la baseline ont été reclassés et corrigés sans supprimer les contrôles :

- **112 tests réussis, 4 ignorés explicitement**, 0 échec ;
- les quatre tests ignorés sont des smoke tests qui exigent OAuth/EAS ou une session externe configurée ;
- le rappel d'occasion compare désormais une heure locale, indépendamment du fuseau de la machine ;
- typecheck réussi ; lint à **0 erreur, 25 warnings** après correction de l'ordre des hooks React.

Le workflow local `.github/workflows/backend-catalog-quality.yml` exécute désormais backend + contrats + Quality Lab, web tests/build, mobile types/lint/tests et extension contrat/manifeste/syntaxe. Il ne contacte pas le backend de production pendant le build web. Ce workflow n'est pas encore un check GitHub observé ni requis : aucun push et aucune modification de protection de branche n'ont été faits.

À cette étape, la suite backend incluant le Quality Lab et les nouveaux invariants de contrat comptait **1 199 tests réussis**, 0 échec et 4 warnings de date déjà connus.

## 10. Contrôle après P0.d/P0.e et durcissement P0.c

Mesure du 28 août 2026 :

| Contrôle | Résultat |
|---|---|
| Backend complet | **1 221 réussis**, 0 échec, 4 warnings préexistants |
| Quality Lab + Observation + migrations | **26 réussis**, 0 échec |
| Quality Lab seul | **9 réussis**, 0 échec |
| Readiness stricte | `not_ready`, code 1 attendu |
| Datasets indépendants | 0 cas sur les cinq jeux requis |
| Bootstrap historique | 14 cas, 27/27 assertions, non éligible |

Le laboratoire valide les JSON Schemas, retire les sorties moteur des packs
aveugles, exige deux annotateurs distincts, refuse les désaccords et détecte
un gold final altéré. Ces preuves valident le dispositif de mesure, pas la
qualité du futur Product Graph. Le verdict produit reste NO-GO.

## 11. Contrôle du commit isolé Phase 0

Le commit `ad19e7d` a été rejoué dans un worktree détaché, sans les
changements locaux préexistants exclus de la branche :

| Surface | Résultat isolé |
|---|---|
| Backend | **1 221 réussis**, 0 échec, 7 warnings de date préexistants |
| Web build | Build de production vert, 42 routes |
| Web tests | **12 réussis, 5 échecs MegaMenu préexistants sur `main`** |
| Mobile typecheck | Vert |
| Mobile tests | **112 réussis, 4 smoke skips** |
| Mobile lint | 25 warnings connus ; le run isolé rencontre en plus un faux positif de casse lié au `node_modules` partagé par symlink |
| Extension | Contrat v1 vert |

Le workflow ne masque pas les cinq régressions MegaMenu : sa première
exécution distante doit rester rouge tant que leur correctif n'est pas intégré
dans une PR distincte ou explicitement ajouté à la revue. La protection de
`main` ne sera activée qu'après stabilisation de tous les checks.

## 12. Contrôle du 29 août 2026 — vérité offre et intégrité Quality

Ce contrôle porte sur les commits locaux `5ee87f2` (scorecard de lancement
fail-closed), `45e7768` (intégrité CLI/CI) et `f5ae21b` (vérité offre bornée à
`/advise` agents et au planificateur général).

| Contrôle | Résultat au 29 août 2026 | Portée |
|---|---|---|
| Backend complet, archive propre `45e7768` | **1 659/1 659**, 0 échec, 7 warnings `datetime.utcnow()` historiques | État versionné sans aucun fichier utilisateur protégé |
| Backend complet, copie de travail | **1 659/1 659**, 0 échec, 4 warnings | Les 3 warnings retirés dépendent du nettoyage utilisateur protégé de `catalog.py` et ne sont pas attribués à la branche |
| Quality ciblé | **262/262**, 0 échec | Workflow humain, schémas, readiness, métriques, scorecard et intégrité |
| Readiness réelle | `integrity_valid=true`, `ready=false`, `status=not_ready` | **0 cas humain** sur les cinq datasets ; NO-GO produit |
| Web, copie de travail | **17/17**, typecheck réussi, build **42/42** | Dépend de modifications utilisateur protégées, exclues des commits FILON |
| Web, état versionné | **5 échecs MegaMenu** | Un checkout propre de la branche ne bénéficie pas des modifications protégées |
| CI distante | Non publiée et non requise | Aucune branche principale protégée par ces checks n'est prouvée |

La vérité offre durcie par `f5ae21b` est bornée à `/advise` agents et au
planificateur général comme suit :

- une offre recommandable exige stock positif explicite, prix fini positif,
  devise observée et observation fraîche ; le TTL actuel de **72 h est
  provisoire** et ne constitue pas un SLO validé ;
- la devise est conservée. Le budget public est en EUR et aucun moteur FX
  n'existe : aucune conversion ni comparaison multidevise n'est inventée ;
- un total livré n'existe que si le prix article et la livraison sont tous deux
  connus. Une livraison inconnue ne vaut jamais zéro, ne bat pas un total connu
  et ne produit ni économie moyenne ni écart en euros ;
- le budget est une contrainte dure sur le montant actuellement calculable,
  mais une livraison inconnue interdit d'affirmer que le prix final livré est
  sous budget ;
- les recommandations non-abstentionnistes du parcours général renvoient
  `confidence_score=null` et `confidence_band=not_calibrated`. L'abstention
  historique conserve encore `0`/`low` : ce marqueur déterministe n'est pas une
  calibration et reste à normaliser. Aucun niveau de confiance affichable n'est
  soutenu avant calibration sur un holdout indépendant.

Le contrat CLI livré par `45e7768` distingue les états au lieu de les confondre :
un rapport intègre et prêt sort avec 0 ; un rapport intègre mais `not_ready` sort
avec 0 en mode normal et 1 avec `--strict` ; toute invalidité d'intégrité sort
avec 2 dans les deux modes. Le workflow normal écrit
`quality-readiness-report.json` et tentera, lorsqu'il sera exécuté sur GitHub,
de publier l'artefact `quality-readiness-<commit>` même après un échec si le
rapport a pu être produit. Cette mécanique locale ne remplace ni la publication
du workflow, ni des checks requis, ni une protection de branche.

**Décision maintenue : NO-GO hors Phase 0.** L'infrastructure est intègre, mais
les cinq datasets humains sont vides et les preuves de CI gouvernée et de web
vert sur l'état versionné manquent toujours.

## 13. Contrôle courant — preuve, devise et expiration fail-closed

Mesure du 29 août 2026 sur les commits backend `1a167dc`, web `0c6f674` et
mobile `55aaf41`. La suite web complète de la copie de travail est distinguée
des contrôles rejoués dans l'archive propre :

| Surface | Contrôle courant | Résultat | Limite de la preuve |
|---|---|---|---|
| Backend versionné | Pytest complet, archive propre de `1a167dc` (HEAD backend avant le commit mobile) | **1 795 réussis**, 0 échec, 7 warnings, **120,91 s** | Preuve technique locale ; elle ne qualifie ni les données P0.2 ni l'infrastructure de production |
| Web versionné | Archive propre de `0c6f674` | Typecheck, gates contrat v1, claims publics et vérité produit, puis build de production : **verts** | Preuve propre mais bornée ; pas de contrat live de production |
| Web, copie de travail | `npm test` complet | Vert, dont **17 tests MegaMenu** et les gates contrat/claims/vérité produit | Inclut MegaMenu et `SearchAssistant.tsx` protégés ; ce résultat n'est pas attribué à l'archive propre |
| Mobile versionné | Vitest complet au commit `55aaf41` | **166 réussis, 4 ignorés**, 0 échec | Les 4 skips restent les smoke tests OAuth/EAS/session externe explicitement séparés |
| Mobile versionné | TypeScript et ESLint | Typecheck vert ; ESLint **0 erreur, 15 avertissements** | Contrôles statiques ; ne mesurent ni device réel ni backend de production |
| Mobile versionné | Audit indépendant de frontière | **Aucun P0, P1 ou P2** | Revue bornée aux changements mobiles de preuve et d'action |

Les invariants clients couverts par ce passage sont les suivants :

- l'Assistant exige `evidence_current=true` explicitement, revalide les cartes
  avant publication et utilise le cache moteur v4 afin d'invalider les anciennes
  cartes insuffisamment qualifiées ;
- une offre actionnable exige `evidence_current=true`, un `observed_at` ISO
  strict, non futur et âgé d'au plus **72 h**, un prix fini positif, une devise
  supportée, un stock positif et une URL marchande HTTPS avec nom DNS public qualifié ;
- les URL avec identifiants, hôte local/réservé ou littéral IP sont rejetées ; ce
  garde-fou ne vaut pas certification commerciale du domaine ;
- l'expiration est dynamique sur le web et sur mobile, y compris après reprise
  ou retour sur une page ouverte : une preuve qui franchit le TTL cesse d'être
  actionnable sans attendre un nouveau build ;
- sur mobile, les paramètres de deep-link sont display-only : achat, partage,
  sauvegarde et alerte exigent une revalidation contre le détail Core, puis
  l'alerte revalide encore la preuve au submit ;
- les comparaisons sont mono-devise. Chaque point d'historique conserve une
  devise explicite, ne peut pas être futur et exige `in_stock=true` ; les
  historiques futurs, multidevises ou sans stock vrai sont rejetés, et les
  claims de baisse/plus bas sont masqués si la série n'est pas comparable ;
  aucun FX n'est inventé ;
- les tris/filtres prix ont été retirés des catalogues dont l'API ne fournit
  pas de scope devise ;
- les scores Outfit non calibrés ne sont plus remplacés par des nombres
  heuristiques : l'interface affiche « Non mesuré » et les flags Fashion/
  Outfit restent désactivés par défaut ;
- le proxy Pulse web partage un cache de **120 s** entre consommateurs ; ce TTL
  technique ne remplace pas la preuve marchande ni son TTL provisoire de 72 h.

Ces validations ferment des chemins de faux claims ; elles ne rendent pas le
produit prêt. Les intégrations protégées `catalog.py` et
`SearchAssistant.tsx` ne sont pas incluses. Le contrat UTC naïf de
`PriceSnapshot.captured_at` et la divergence d'URL canonique entre les cartes
Assistant et le détail catalogue restent ouverts. Les clients doivent donc
masquer les surfaces non prouvées ou s'abstenir jusqu'à leur intégration
autorisée. P0.2 reste à **0 cas humain**, le Product Graph n'a pas de score
indépendant, et l'infrastructure de production (proxy réel, WAF/quotas
distribués, export, dashboards, pager et trafic représentatif) n'est pas
qualifiée.

**Décision maintenue : NO-GO hors Phase 0.**

## 14. Contrôle final de l'archive propre — Quality v0.5 et mobile public

Mesure du 29 août 2026 sur l'archive propre du HEAD `a78401a`, contenant le lot
Quality `6e12386`. Cette archive exclut les modifications locales protégées et
constitue donc la preuve attribuable à la branche versionnée.

| Surface | Contrôle | Résultat | Lecture correcte |
|---|---|---|---|
| Backend | Pytest complet | **1 907 réussis, 1 ignoré**, 0 échec, 7 warnings, **370,53 s** | Vert technique sur l'archive ; les warnings `datetime.utcnow()` sont historiques |
| Quality Lab | Suite v0.5 ciblée | **345/345** | Couvre le roster de 7 datasets et 7 emplacements d'adaptateur, dont 4 intégrés et 3 fail-closed, les 27 gates, le runner aveugle, la provenance, le scorecard et la régression fail-closed |
| Quality readiness | Modes normal et strict | Normal : **exit 0** ; strict : **exit 1** | `integrity_valid=true`, `ready=false`, `status=not_ready`, 0 cas humain sur 7 datasets ; fingerprint `sha256:fa3d67fa309cfda8ccbd0f567252cb2daf2a63c4b1459ee532c482bcff60927e` |
| Web | Typecheck, gates contrat v1, claims et vérité produit ; build de production | **Verts** ; 42 pages générées | Preuve versionnée bornée, sans contrat live de production |
| Web | Suite complète | **12/17**, 5 échecs | Les cinq échecs sont limités à MegaMenu ; les correctifs locaux protégés du composant et du script de test ne sont pas intégrés à l'archive, donc aucun faux vert n'est revendiqué |
| Mobile | Vitest complet | **326 réussis, 4 ignorés**, 0 échec, 38,56 s | Les 4 skips sont les smoke tests OAuth/EAS/session externe séparés |
| Mobile | TypeScript, ESLint et revue indépendante | Typecheck vert ; ESLint **0 erreur / 17 avertissements** ; **aucun P0/P1/P2** | Les avertissements sont préexistants et hors lot ; pas de device ni backend de production qualifié |
| Extension | Contrat v1, syntaxe background/content/popup et manifeste MV3 | **Verts** | Contrôle local, sans publication de l'extension |

Le lot mobile `a78401a` complète la localisation FR/NL/EN des parcours
publics, maintient les noms canoniques dans les requêtes, masque les claims
marchands non prouvés et sérialise la réconciliation locale entre écrans. Il
ne transforme pas les smoke tests externes ignorés en preuve de production.

Dans cette archive historique, la readiness confirme l'intégrité du
laboratoire, mais les sept golds humains restent absents et les adaptateurs
applicatifs de variante, attachement et décision restent volontairement
fail-closed. Le workflow n'a toujours aucun
run GitHub observé, `main` n'est pas protégée, et l'infrastructure réelle
(Postgres/staging, Railway/Vercel, WAF, dashboards et pager) n'est pas qualifiée.

**Décision maintenue : NO-GO hors Phase 0.**

## 15. Avancée locale postérieure — adaptateur Decision

Le Quality Lab courant branche maintenant les sept moteurs réels sur ses
entrées aveugles. Decision rejoue l'intent et le plan général à une date de
référence explicite, refuse les dérives d'identité ou de provenance et ne
publie qu'un claim `selected_candidate:<candidate_id>` relié aux preuves de
l'offre. Entity, Variant et Offer Attachment appellent le resolver Graph
conservateur `exact-gtin-shadow-v1` : un GTIN manquant, invalide ou conflictuel
produit abstention ou quarantaine, jamais une similarité inventée. La suite
Quality courante passe **377/377** et le backend complet **2 078 réussis + 2
ignorés**. Le holdout contient toujours **0 cas humain** : cette avancée
technique ne change donc pas le NO-GO et ne produit aucune mesure métier.

## 16. Qualification distante courante — intégration, CI et protection

Mesure du 29 août 2026 après les autorisations ciblées et la publication :

| Surface | Preuve | Résultat |
|---|---|---|
| Identité Git applicative avant ce rapport | Local `7026f4a`, distant consolidé `9beeda8` | Arbre commun `fcac4bb28bd2c26835afbc74949eaa37a96b8ab6` |
| Contrat vérité | `4a95a42` + `90246b2` | Catalogue, agrégats, Assistant et MegaMenu intégrés fail-closed |
| Backend local | Pytest complet | **2 020 réussis + 1 ignoré** |
| Web local | Suite, typecheck, build | **17/17**, TypeScript vert, 42 pages |
| GitHub Actions #343 | Migrations, backend et trois clients | **12/12** migrations, **2 021/2 021** backend, web/mobile/extension verts |
| Quality strict | 7 datasets / 27 gates | Échec attendu : `integrity_valid=true`, `ready=false`, `status=not_ready`, 0 cas humain |
| Artefact | `9713798390` | Rapport téléversé, digest `sha256:4806919878e3baccb939aba8db1c6b39e5ea078a4eb45e943c63db69bf5675dd` |
| Vercel | Statuts GitHub sur `e04dfc2` et `9beeda8` | Preview construite avec succès ; production non promue |
| Protection `main` | Ruleset `21798272` | Active, PR et quatre jobs requis, branche à jour, aucun bypass, suppression/force-push interdits |

Le backend Railway public reste un ancien processus `env=dev`, Redis local et
Qdrant désactivé ; il ne prouve ni le nouveau déploiement ni la collecte, les
traces, le WAF ou le pager. Le lot CI/gouvernance est acquis, mais les datasets
humains et la production restent NO-GO. Voir le
[rapport de qualification distante](PHASE_0_REMOTE_QUALIFICATION_REPORT.md).
