## Phase et décision demandée

- Phase / lot :
- Owner :
- Décision demandée : `GO shadow` / `GO limité` / `NO-GO` / autre
- Feature flag et valeur par défaut :

## Current state et root cause

Décrire le comportement mesuré avant la modification, sa cause et les
consommateurs concernés. Ne pas déduire une qualité produit d'un simple test
technique vert.

## Contrats et données

- Contrats modifiés ou confirmés :
- Tables / index / jobs modifiés :
- Callers web, mobile, extension ou internes :
- Compatibilité ascendante et traitement de `unknown` :
- Données réelles utilisées, provenance et anonymisation :

## Migration et rollback

- Stratégie expand / shadow / contract :
- Commande ou runbook de migration :
- Snapshot et restauration testés :
- Rollback fonctionnel :
- Rollback schéma :

## Preuves avant / après

| Mesure | Dataset / environnement | Avant | Après | Gate |
|---|---|---:|---:|---|
| | | | | |

- Tests et checks exécutés :
- Latence P50 / P95 / P99 :
- Coût calcul / stockage / fournisseur :
- Cas limites, abstentions et quarantaines :
- Limites connues de la mesure :

## Risques et observabilité

- Risque utilisateur / données / opérations :
- Signal précoce et alerte :
- Dashboard / trace / journal de décision :
- Owner et date de revue post-déploiement :

## Checklist de gouvernance

- [ ] Aucun secret, payload personnel ou jeton n'est ajouté au dépôt.
- [ ] Aucune valeur favorable n'est fabriquée à partir d'un champ inconnu.
- [ ] Les migrations et leur rollback sont testés sur une base éphémère.
- [ ] Les tests contractuels couvrent chaque client concerné.
- [ ] Les chiffres métier utilisent un jeu indépendant et indiquent leur version.
- [ ] Les désaccords humains restent en adjudication, jamais auto-résolus.
- [ ] Le shadow n'a aucun lecteur public tant que ses gates ne sont pas passées.
- [ ] Aucun travail Fashion, Recreate, 3D ou immersif n'entre avant le GO Core.
- [ ] Les ADR, le System Map, le rapport de phase et la mission sont à jour.
