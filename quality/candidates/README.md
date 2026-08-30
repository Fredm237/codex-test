# Inventaires de candidats Quality Lab

Ce dossier contient des observations publiques réelles, jamais des golds. Un
inventaire est une étape de collecte : il reste volontairement
`ready_for_annotation=false` tant qu'un humain n'a pas choisi les cas, confirmé
la langue et le type de scénario, puis produit deux annotations indépendantes.

`quality_lab.candidate_inventory` refuse HTTP, les paramètres de requête libres,
plus de 50 snapshots, les snapshots de plus de 8 Mio, les inventaires de plus
de 64 Mio, les reçus de plus de 1 Mio, les doublons et l'écrasement d'un artefact. Il
omet les sorties du moteur qui pourraient biaiser l'annotation : catégorie et
sous-catégorie FILON, prix, devise, stock, fraîcheur, type d'offre, image et lien
affilié. Le reçu engage les octets exacts des réponses publiques et chaque ligne
de l'inventaire.

`sampling_vertical` décrit uniquement le filtre qui a servi à tirer la ligne.
Il ne certifie jamais la vraie verticale : le catalogue public contient
précisément des erreurs de classement que ce benchmark doit mesurer. Le champ
`curation.vertical` reste donc nul jusqu'au jugement humain.

Vérification d'un lot publié :

```bash
cd filon-backend
python -m quality_lab.candidate_inventory verify \
  --input ../quality/candidates/catalog-public-2026-08-29.jsonl \
  --receipt ../quality/candidates/catalog-public-2026-08-29.receipt.json
```

Les champs `curation` nuls ne doivent pas être remplis par le moteur. Le passage
vers les packs v0.5 utilise `quality_lab.curation_workflow` dans un fichier
séparé. Il lie l'inventaire, le curateur et le roster complet, puis ne produit
que des cas `taxonomy` ou `variant_resolution` encore sans gold. Le protocole
et les commandes sont décrits dans `../README.md`. Les paires d'entités, les
rosters de variantes, les vérités d'offre et les requêtes Retrieval/Decision
exigent des collectes dédiées ; elles ne sont jamais inventées depuis les noms
du catalogue.
