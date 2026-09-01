# FILON — Phase 2D Entity Signal Extractors Report

- Date locale : **1er septembre 2026**
- Statut : **TERMINÉ LOCALEMENT — SHADOW, NON DÉPLOYÉ**
- Contrat : `entity-resolution-signal-extraction/v1`
- Extracteur : `awin-entity-signals/v1`
- Lecteurs publics et writers : **inchangés**

## Verdict

Les extracteurs Entity Resolution sont déterministes, bornés et fail-closed.
Chaque raw produit exactement une sortie pour chacun des seize signaux ciblés.
Une absence reste `unknown`, une valeur structurée invalide devient `invalid`
et deux alias structurés contradictoires deviennent `conflict`. Aucun de ces
états ne peut devenir une preuve favorable.

MPN et modèle ne sont jamais extraits d'un titre libre. Stockage, mémoire,
capacité, taille, couleur et génération peuvent être repérés lexicalement,
mais restent `candidate_only`, faibles et non promotionnels. Cette frontière
traduit directement l'audit P2B.

## Sorties contractuelles

Chaque signal porte :

- son état ;
- les champs source réellement lus ;
- zéro, une ou plusieurs valeurs normalisées selon l'état ;
- sa force et son rôle autorisés ;
- un reason code ;
- la transformation et sa version.

| État | Valeur | Force | Effet autorisé |
|---|---|---|---|
| `observed` | une valeur structurée | forte ou faible selon le signal | preuve ou corroboration shadow |
| `candidate_only` | une ou plusieurs valeurs | faible | génération de candidats seulement |
| `unknown` | aucune | aucune | abstention |
| `invalid` | aucune | aucune | abstention et diagnostic |
| `conflict` | au moins deux valeurs | aucune | veto explicite |

Le JSON Schema interdit notamment une valeur favorable sur `unknown`, une
force forte sur `candidate_only` et une force quelconque sur `conflict`.

## Signaux couverts

Les seize sorties sont : Brand, MPN, modèle, stockage, mémoire, capacité,
taille, couleur, génération, édition, condition, quantité de pack, rôle
produit, titre, image et taxonomie.

Les champs structurés reconnus restent des alias fermés et versionnés. Par
exemple, MPN accepte `mpn`, `manufacturer_part_number` ou `part_number` ; si
plusieurs de ces champs portent des valeurs différentes, l'extracteur refuse
de choisir.

## Politique lexicale

Le titre peut générer des candidats uniquement pour :

- stockage et mémoire avec unité explicite ;
- capacité en BTU ou litres ;
- dimension, pouces ou dimension de pneu ;
- couleur dans un vocabulaire FR/EN fermé ;
- génération explicitement libellée.

Les contextes RAM et stockage sont distingués lorsqu'un marqueur explicite
existe. Les codes alphanumériques généraux ne sont pas interprétés comme MPN
ou modèle, car P2B a montré 903 détections bruitées sur 1 000 titres de bijoux.

## Impact du feed actuel

Sur le schéma raw observé en P2B :

- Brand peut être `observed` mais reste une corroboration faible isolée ;
- titre, image et taxonomie peuvent générer des candidats faibles ;
- MPN, modèle et attributs structurés restent `unknown` lorsqu'ils ne sont pas
  fournis ;
- aucune sortie `HIGH_CONFIDENCE` n'est possible avec ces seuls champs.

L'extracteur n'a pas été déployé ni exécuté comme writer en production. Cette
étape fige la transformation pure et son contrat ; le replay raw borné et la
persistance appartiennent à P2F après le resolver P2E.

## Vérification

Les tests couvrent :

- validation Draft 2020-12 du contrat et de deux exemples ;
- raw Awin actuel avec MPN/modèle explicitement inconnus ;
- faits structurés forts et versionnés ;
- signaux de titre maintenus faibles ;
- conflit entre alias structurés ;
- type invalide fail-closed ;
- provenance obligatoire et horodatage avec offset ;
- stabilité du benchmark et des contrats P2A–P2C.

Suite ciblée : **62 tests réussis**.

## Décision P2D

P2D est fermé localement. P2E peut construire un candidate generator et un
resolver hiérarchique qui consomment ces sorties sans modifier leurs états ni
permettre à un score de contourner un conflit. La publication publique reste
séparée de cette qualification locale.
