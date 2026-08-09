# Reprise — brief pour une nouvelle session

Copier-coller ce fichier comme premier message d'une session cloud sur
`Fredm237/codex-test`, environnement **Par défaut** en accès réseau **Complet**.

---

Tu reprends le travail sur **FILON**, un copilote d'achat francophone premium
(Belgique d'abord, puis FR/NL/EN). Monorepo `Fredm237/codex-test` :
`filon-web` (Next.js 15, App Router, déployé sur Vercel, racine `filon-web`) et
`filon-backend` (FastAPI + LangGraph + SQLAlchemy async, déployé sur Railway).

**Développe sur la branche `claude/ui-ux-pro-max-skill-install-8x985i`.** Ne
pousse jamais ailleurs sans autorisation explicite.

## Ce que tu dois savoir avant de toucher à quoi que ce soit

Le catalogue compte **799 435 offres** issues des flux Awin. Le défaut que
l'utilisateur signale depuis le début, et qui n'est pas encore réglé en
production : **des articles s'affichent dans le mauvais rayon**. Cliquer sur
« Claviers & Souris » renvoyait des tissus, des patrons de couture, un panneau
de façade. Ce n'est pas propre à l'informatique — tous les rayons sont touchés.

Trois causes ont été identifiées et corrigées dans le code :

1. **Le motif l'emportait sur le support.** Un tissu imprimé de souris partait
   en Informatique. Mesuré sur quinze libellés de mercerie réels : **1/15**
   correctement classés avant, **15/15** après.
2. **Les couleurs composées.** « Gris souris », « bleu canard » étaient lues
   comme des objets.
3. **Le marchand n'était pas exploité.** Quand un rayon couvre ≥ 70 % du
   catalogue d'un vendeur, les offres minoritaires y sont ramenées
   (`app/services/coherence.py`).

## L'état exact, à vérifier avant d'agir

Cinq commits sont sur la branche et **pas encore sur `main`**, donc **pas
déployés** :

```
bfe0146  firecrawl: MCP en transport HTTP, et les 33 skills versionnées
b3e6166  outillage: MCP Playwright et Instagram, Agent Reach, /reel-script
ef84530  skills: verrou des sources
98daec9  skills: installe les quatre skills de design demandées
68df403  fix(cohérence): c'est le département qui sépare l'activité de l'erreur
```

Le dernier est le seul qui compte pour le catalogue. **228 tests backend
passent** (`cd filon-backend && python -m pytest -q`).

## La tâche immédiate

**1. Fusionner et déployer `68df403`.** Ouvre une PR de la branche vers `main`,
fusionne. Railway et Vercel redéploient seuls. Vérifie que c'est en ligne :

```bash
export FILON_API=https://web-production-c6842.up.railway.app
export FILON_TOKEN=...                    # ADMIN_SYNC_TOKEN — à récupérer dans les
                                          # variables Railway, jamais écrit ici
curl -s $FILON_API/health | python3 -m json.tool | head -5
```

Attention : `"status": "ok"` ne prouve pas que le nouveau build est en ligne —
l'ancien le rend déjà. Le seul indice fiable est `uptime_seconds`, qui doit
repartir de zéro après un redéploiement.

**2. Reclasser, puis simuler.**

```bash
curl -s -X POST "$FILON_API/api/catalog/admin/reclassify?batch=5000" \
  -H "x-admin-token: $FILON_TOKEN" | python3 -m json.tool

curl -s -X POST "$FILON_API/api/catalog/admin/realign?dry_run=true" \
  -H "x-admin-token: $FILON_TOKEN" | python3 -m json.tool
```

La simulation rend le **détail par marchand** : vers quel rayon, combien
d'offres, sur quel total. **Lis-le avant d'écrire**, et présente-le à
l'utilisateur. Un cas douteux se tranche avec :

```bash
curl -s "$FILON_API/api/catalog/admin/merchant-breakdown?merchant=<nom>" \
  -H "x-admin-token: $FILON_TOKEN" | python3 -m json.tool
```

**3. Écrire, seulement après accord.** `dry_run=false`. `exclude=<nom>` met un
marchand entièrement de côté.

## Ce qui a déjà été essayé et rejeté — ne le refais pas

Deux garde-fous « automatiques » ont été construits puis retirés, parce que les
vrais chiffres les ont réfutés. L'idée était qu'une minorité *fournie* dans un
rayon, puis dans un département, signale une seconde activité plutôt que du
bruit. **C'est faux** : une erreur de mots-clés systématique est fournie elle
aussi.

La preuve : YesStyle FR vend des cosmétiques coréens. Sur 42 851 offres,
**2 113 tombent en Informatique** (4,9 %) — pile assez pour déclencher la
protection. Ce bloc n'est pas une activité, c'est exactement la pollution qu'on
veut retirer. Sa mode réelle tient en **103 offres**, soit 0,2 %.

Ce qui marche, et qui est en place dans `68df403` : **c'est le département qui
sépare l'activité de l'erreur**. Un spécialiste étale son catalogue sur les
rayons voisins de son département — Overhemden vend des chemises homme et
1 979 cravates en « Accessoires », Kinguin vend des clés de jeu et 1 238
recharges en « Téléphonie » ; dans les deux cas le département tient 98 %. Un
bloc tombé dans un *autre* département est la signature de l'erreur. Le
département du rayon dominant est donc protégé en entier ; tout ce qui en sort
est ramené.

## Nouvelle référence de design

L'utilisateur a changé d'étalon. **Ce n'est plus phia.com** mais le compte
Instagram **`w.wearebrand`** : <https://www.instagram.com/w.wearebrand>

Va le voir. Instagram exige souvent une connexion — si le profil public ne
suffit pas, demande des captures plutôt que d'inventer. **Ne produis aucune
analyse d'un site que tu n'as pas ouvert** : c'est une erreur qui a déjà été
commise et durement reprochée.

Note aussi que le studio est une *vitrine*, pas un produit. Son esthétique
nourrit la page d'accueil, les visuels et les Reels ; elle ne dit rien de la
page catalogue à 700 000 offres, où lisibilité et vitesse décident. Fais la
distinction explicitement avec l'utilisateur avant de refondre quoi que ce soit.

## Outillage disponible

- **31 skills de design** dans `.claude/skills/` — dont `impeccable`
  (59 détecteurs déterministes), `design-taste`, et la famille
  `emilkowalski`. `design-taste` est la fusion de trois autres, toutes
  installées : arbitre, ne les empile pas.
- **33 skills Firecrawl** — attention, celles qui appellent le CLI `firecrawl`
  échouent derrière un proxy (405, axios trop ancien). Le **MCP** Firecrawl,
  lui, fonctionne.
- **MCP** : `playwright` (navigateur), `instagram` (Graph API, 23 outils),
  `firecrawl` (HTTP). Voir `.mcp.json` et `docs/OUTILLAGE.md`.
- **`/reel-script`** — écrit un script de Reel à partir d'un chiffre réel du
  catalogue, et s'arrête si l'API ne répond pas plutôt que d'inventer.

## Règles non négociables

- **Aucun secret dans un commit.** Jetons Awin, `ADMIN_SYNC_TOKEN`, clé
  Firecrawl : variables d'environnement uniquement.
- **Ne cite jamais un marchand non partenaire.** Fnac, Amazon, Cdiscount,
  Boulanger, Darty n'en sont pas. Un repli de démonstration qui inventait des
  recommandations chez eux a été supprimé du frontend ; ne le réintroduis pas.
- **Ne déclare rien « vérifié » sans l'avoir mesuré.** L'utilisateur vérifie, et
  a raison de le faire.
- Commits en français, avec `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Reste ouvert, plus tard

Taux de cashback vides pour tous les marchands (décision commerciale), CORS en
`"*"`, endpoint SSE sans authentification ni limite de débit, code mort
SmartWave et dossier `filon-site/` à purger, articles de blog 2 à 6 sans
traduction anglaise.

---

**Commence par** : vérifier l'état de la branche, ouvrir la PR de `68df403`
vers `main`, et confirmer le déploiement avec `/health`. Puis ouvre
`w.wearebrand` et dis-moi ce que tu y vois réellement.
