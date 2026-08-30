# FILON — rapport P0.c.1 workflow de curation humaine

- Date de qualification locale : **30 août 2026**
- Périmètre : inventaire catalogue public sans label → cas candidats sans gold
- Décision : **GO technique pour curation humaine ; NO-GO inchangé pour les datasets et la Phase 1**

## Problème fermé

L'inventaire public de 1 000 observations était immuable et sans sortie moteur,
mais le passage vers les packs d'annotation supposait encore une édition
humaine non contractuelle. Modifier directement `curation` cassait à juste
titre l'empreinte de l'inventaire ; aucun artefact séparé ne liait le curateur,
le roster complet et les strates choisies.

`quality_lab.curation_workflow` ajoute ce maillon sans créer de vérité :

1. `prepare` revérifie l'inventaire et son reçu, affecte le roster complet à un
   `curator_id` explicite et empreinte chaque tâche puis le pack ;
2. l'humain remplit seulement `decision.include`, `language`, `scenario_type`,
   `vertical` et `datasets` ;
3. `finalize` refuse une tâche absente, dupliquée, altérée, encore indécise ou
   portant un dataset non supporté ;
4. les cas produits ne contiennent que `case_id`, `group_id`, `strata` et
   `observation`, puis sont validés par le même contrat que le prochain pack
   aveugle ;
5. le JSONL et son reçu sont publiés ensemble sans remplacement d'une cible
   existante.

## Frontière de vérité

Le workflow n'autorise que `taxonomy` et `variant_resolution`, car ce sont les
seuls contrats dont l'entrée peut être constituée honnêtement depuis une
observation catalogue unitaire. Il refuse de dériver :

- une paire `entity_resolution` depuis une similarité de titres ;
- un roster `offer_attachment` absent de l'inventaire ;
- une vérité prix, stock, livraison ou lien affilié volontairement omise ;
- une requête `retrieval` ou `decision` depuis le nom d'un produit.

Une sortie finalisée conserve `labels_present=false`, devient seulement
`ready_for_annotation=true` et reste bloquée sur
`independent_human_annotation`. Le code ne prouve pas que `curator_id`
correspond à une personne ni que cette personne est indépendante des deux
annotateurs ; cette preuve appartient au processus externe. L'identifiant
versionné doit rester pseudonyme : aucune identité civile ni adresse e-mail ne
doit entrer dans le dépôt public.

## Invariants prouvés

- `sampling_vertical` n'est jamais promu automatiquement en verticale gold ;
- exclusion = aucune strate et aucun dataset ; inclusion = trois strates
  fermées et au moins un dataset autorisé ;
- observation, affectation, identité du curateur et roster complet sont liés à
  l'inventaire source ;
- une altération ne peut pas être blanchie en recalculant seulement
  `task_fingerprint` ;
- aucun `gold`, `annotation`, label ou champ supplémentaire ne passe dans la
  sortie ;
- les comptes de strates et le contenu exact des cas sont engagés par le reçu ;
- la publication refuse l'écrasement et laisse l'inventaire brut intact.

## Preuve locale

- nouveau workflow : **9/9 tests** ;
- Quality Lab complet, y compris inventaire, curation, annotation,
  adjudication, schémas, runner, scorecard, régression et CI scope :
  **386/386 tests** sous Python 3.12 ;
- aucune donnée humaine n'a été créée, importée ou simulée ;
- les trois fichiers utilisateur protégés sont restés hors du lot.

## Gate suivant

Un humain identifié doit exécuter la curation réelle de l'inventaire. Deux
autres humains indépendants doivent ensuite annoter les mêmes packs, avec un
troisième adjudicateur distinct en cas de désaccord. Les cinq autres datasets
requièrent des collectes réelles dédiées. Tant qu'ils restent à zéro, le
verdict demeure **NO-GO Phase 1 et NO-GO immersive**.
