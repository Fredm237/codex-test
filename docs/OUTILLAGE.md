# Outillage agent — ce qui est installé, et ce qui demande ta machine

Tout ce qui suit vient des références partagées en août 2026. Ce document dit
où chaque chose se trouve, ce qui manque pour s'en servir, et ce qui n'a pas pu
être installé — avec la raison.

---

## Installé dans le dépôt, actif tout de suite

### Skills de design — 24 skills

| source | apport | nombre |
|---|---|---|
| `emilkowalski/skills` | craft du mouvement : courbes, durées, interruptions, principes Apple | 9 |
| `Leonxlnx/taste-skill` | lecture du brief, direction artistique, pre-flight, variantes | 13 |
| `h3nryprod01/design-taste` | la fusion dédupliquée des trois | 1 |
| `pbakaus/impeccable` | 23 commandes, 59 règles de détection déterministes | 1 |

Elles vivent dans `.claude/skills/` (liens) et `.agents/skills/` (contenu), donc
elles suivent le dépôt et servent aussi aux autres agents. `skills-lock.json`
garde la trace de chaque source et de son empreinte.

**`design-taste` est la fusion des trois autres** et son auteur déconseille de
les cumuler. Les quatre sont là parce qu'elles ont été demandées ; n'en garder
qu'une active éviterait d'arbitrer entre quatre jeux de règles concurrents.

`impeccable` n'est pas dans le verrou : son installeur échoue derrière le proxy
(HTTP 403), la build a été reprise par git. `node .claude/skills/impeccable/scripts/doctor.mjs`
vérifie sa cohérence.

### Serveurs MCP — `.mcp.json`

**`playwright`** — pilotage de navigateur. Rien à configurer.

**`instagram`** — 23 outils sur la Graph API : publications, commentaires, DM,
stories, hashtags, reels, statistiques. C'est « l'étape 01 » de la méthode
partagée : Claude ↔ MCP ↔ Graph API.

Il lui faut quatre variables d'environnement, **jamais dans le dépôt** :

```bash
export INSTAGRAM_ACCESS_TOKEN=…   # jeton longue durée Meta
export INSTAGRAM_ACCOUNT_ID=…     # identifiant du compte professionnel
export FACEBOOK_APP_ID=…
export FACEBOOK_APP_SECRET=…
```

Le `.mcp.json` ne contient que les *noms* de ces variables. Les DM demandent en
plus un Advanced Access validé par Meta, ce qui passe par leur revue d'app.

**`higgsfield`** — génération d'images, de vidéos et de voix dans le nuage.
Déjà connecté (plan starter).

### Commande `/reel-script`

`.claude/commands/reel-script.md`. Écrit un script de Reel — hook, corps, chute,
texte à l'écran, légende — **à partir d'un chiffre réel du catalogue**, qu'elle
va lire dans l'API avant d'écrire. Si l'API ne répond pas, elle s'arrête au lieu
d'inventer. Elle ne cite que des marchands réellement partenaires.

```
/reel-script                       # choisit l'angle le plus fort
/reel-script "les 2210 offres écartées" --langue nl
```

### Agent Reach — CLI

Accès unifié à Twitter/X, Reddit, YouTube, GitHub, RSS, pages web, LinkedIn,
Facebook, Instagram, recherche globale.

```bash
agent-reach doctor      # ce qui est disponible et ce qui manque
agent-reach install --env=auto --dry-run
```

> **Piège de nom.** `pip install agent-reach` installe **un autre projet**
> (`jgalea/agent-reach`, 2 canaux). Celui de la référence est
> `Panniantong/Agent-Reach` et s'installe depuis git :
>
> ```bash
> pip install "git+https://github.com/Panniantong/Agent-Reach.git"
> ```

L'installation ici est dans le conteneur, donc éphémère : à refaire sur ta
machine avec la commande ci-dessus.

---

## Ce qui ne peut pas être installé ici

### Wan2GP — génération vidéo locale

`scripts/setup-wan2gp.sh` est prêt, mais **il refusera de tourner sur ton Mac**,
et c'est volontaire.

La documentation d'installation de Wan2GP ne couvre que Windows et Linux avec
un GPU NVIDIA (GTX 10xx → RTX 50xx) ou AMD RDNA 2-4. Ni macOS ni Apple Silicon
n'y figurent, et la chaîne repose sur CUDA : le `--index-url` de torch n'a pas
d'équivalent Metal. Sur un MacBook Air il n'existe pas d'installation dégradée
mais utilisable — il n'y a pas d'installation.

Le script vérifie le GPU et l'espace disque (60 Go minimum) avant de
télécharger quoi que ce soit, parce qu'un échec après une heure de
téléchargement coûte plus qu'un refus immédiat.

**Pour de la vidéo depuis le Mac : Higgsfield, déjà connecté.** Génération dans
le nuage, pas de GPU requis, pas de poids à télécharger.

### ManyChat — automatisation des DM

Service en ligne, rien à installer. C'est la brique « commente X et je t'envoie
le lien » : un commentaire déclenche un DM automatique. Se configure sur
manychat.com, se connecte au compte Instagram professionnel, et se combine avec
la commande `/reel-script` — c'est elle qui écrit le mot déclencheur.

### Framerate, le_laptop

Un outil en ligne et une formation Figma. Ni l'un ni l'autre ne s'installe.

---

## Vérifier que tout répond

```bash
claude mcp list                                        # serveurs MCP
node .claude/skills/impeccable/scripts/doctor.mjs      # skill impeccable
agent-reach doctor                                     # canaux d'accès
ls .claude/skills | wc -l                              # 31 skills
```
