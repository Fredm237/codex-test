# FILON — règles permanentes de l'agent

Ce fichier est chargé à chaque session. Il décrit comment travailler sur ce
dépôt, et surtout comment ne pas se tromper. Il n'est pas décoratif : les
règles ci-dessous viennent d'erreurs réellement commises et payées.

---

## 1. La boucle

Toute demande qui appelle une action se traite ainsi, jamais en répondant
seulement :

```
OBSERVE → PLANIFIE → EXÉCUTE → VÉRIFIE → CORRIGE → CONTINUE → LIVRE
```

Ne demande pas confirmation à chaque étape. Demande-la seulement quand
l'action est **irréversible, destructive, engageante financièrement,
juridiquement sensible**, ou qu'il manque une information que rien ne permet
de déduire. Fusionner une PR, écrire sur 800 000 lignes, révoquer un jeton :
on demande. Créer une branche, lancer les tests, lire une page : on fait.

## 2. Vérifier veut dire mesurer

Une commande qui rend 0 n'est pas une preuve. Après chaque étape qui compte,
poser : *est-ce vraiment le résultat attendu, ou seulement l'absence
d'erreur ?*

Trois pièges déjà rencontrés sur ce projet, à connaître :

- **`/health` ment.** Il ne passe en `degraded` que si la base est en
  `error`, jamais sur `slow`. Une base incapable de répondre à `SELECT 1`
  en deux secondes laisse afficher `"status": "ok"`. Pour savoir si un
  déploiement est passé, lire `uptime_seconds` — il repart de zéro.
- **Un document d'état périme.** `docs/REPRISE.md` annonçait cinq commits en
  avance ; `main` en avait huit d'avance en sens inverse. Toujours
  `git fetch` et comparer avant de croire un fichier.
- **Un outil annoncé n'est pas un outil disponible.** `.mcp.json` déclarait
  trois serveurs dont aucun n'était chargé. Tester avant d'affirmer.

Ne déclare jamais « vérifié » ce qui n'a pas été mesuré. L'utilisateur
vérifie, et il a raison de le faire.

## 3. Accès web — ordre de repli imposé

Le navigateur local **ne peut pas atteindre l'extérieur** : la politique
d'egress coupe le trafic Chromium (`ERR_CONNECTION_RESET`), y compris à
travers le proxy. Ce n'est pas une panne, c'est une règle — le README du
proxy interdit de la contourner. `curl` passe, le navigateur non.

Prendre dans cet ordre, descendre d'un cran à chaque échec :

| Besoin | Outil | Note |
|---|---|---|
| Lire une page, extraire du contenu | `firecrawl` (MCP) | rendu JS inclus |
| Chercher | `WebSearch`, `firecrawl_search` | |
| Réseaux sociaux | Apify | Instagram : seule voie qui marche |
| Rendu ou interaction réelle | sandbox `higgsfield` | réseau libre, distant |
| Nos propres apps | Playwright local | `localhost` seulement, ça marche |

Ce qui est **définitivement fermé**, ne pas réessayer : Firecrawl sur
Instagram (refus de politique, pas un incident), le navigateur local vers
l'extérieur, l'API web publique d'Instagram.

Le port du proxy est **dynamique** : lire `$HTTPS_PROXY`, ne jamais coder un
port en dur. Un `403`/`407` du proxy est une décision de l'organisation : on
la rapporte, on ne la contourne pas.

## 4. Secrets

Aucun secret dans un commit. Jamais. Jetons Awin, `ADMIN_SYNC_TOKEN`, clés
Firecrawl et Apify : variables d'environnement uniquement.

Un précédent : `docs/REPRISE.md` exportait `ADMIN_SYNC_TOKEN` en clair, dans
la ligne même qui le déclarait « jamais commité ». Si tu trouves un secret
dans un fichier suivi, retire-le **avant** toute fusion, et signale qu'il
reste à révoquer — le retirer du fichier ne le retire pas de l'historique.

## 5. Données

**Ne jamais fabriquer un chiffre, un marchand ou un exemple.** Une section
sans données ne s'affiche pas ; elle ne se remplit pas d'un cas inventé pour
faire tourner une animation. C'est la règle qui structure `lib/proof.ts` et
`CostStack3D` : sans écart mesuré, rien ne s'affiche.

**Ne cite jamais un marchand non partenaire.** Fnac, Amazon, Cdiscount,
Boulanger, Darty n'en sont pas. Un repli de démonstration qui inventait des
recommandations chez eux a été supprimé du frontend ; ne pas le réintroduire.

## 6. Ce qui a été essayé et rejeté — ne pas reconstruire

**Les seuils de volume dans la cohérence du catalogue.** L'idée qu'une
minorité *fournie* dans un rayon signale une seconde activité est fausse :
une erreur de mots-clés systématique est fournie elle aussi. YesStyle FR le
prouve — 2 113 de ses 42 851 offres tombent en Informatique (4,9 %), et ce
bloc est exactement la pollution à retirer.

Ce qui marche et qui est en place : **c'est le département qui sépare
l'activité de l'erreur**. Le département du rayon dominant est protégé en
entier ; ce qui en sort est ramené.

## 7. Design

La référence est le compte Instagram **`w.wearebrand`**, observé
directement. Ce n'est plus phia.com — le blanc pur, la serif de titrage et
les pilules appartiennent à l'ancienne identité et ne reviennent pas.

Ce que le compte donne : sous-exposition, béton chaud, ambre des spots comme
seule couleur, géométrie orthogonale, une seule grotesque en bas de casse —
**et une alternance franche sombre/clair écran par écran**, plus **un objet
3D unique qui se transforme au défilement et dont la transformation explique
le produit**.

Distinction à tenir : la vitrine respire, le catalogue à 799 435 offres
remonte le contraste et resserre l'espace. Même monde, autre débit. Voir
`filon-web/app/tokens.css`, qui documente chaque valeur par ce qui a été vu.

**N'écris aucune analyse d'un site que tu n'as pas ouvert.** Cette erreur a
déjà été commise et durement reprochée. Si l'accès échoue, demande des
captures.

## 8. Dépôt

- Monorepo : `filon-web` (Next.js 15, Vercel) et `filon-backend`
  (FastAPI + LangGraph, Railway).
- Tests backend : `cd filon-backend && python -m pytest -q`.
- Build web : `cd filon-web && npm run build`.
- Commits **en français**, et ils expliquent *pourquoi*, pas *quoi*.
- Ne pousse jamais sur une autre branche que celle demandée.

## 9. État de mission

Les missions longues s'écrivent dans `.claude/agent/missions/`. Le format et
les commandes sont dans `.claude/agent/README.md`. Une mission qui dure plus
de quelques étapes **doit** avoir son fichier d'état : le contexte se perd,
pas le fichier.
