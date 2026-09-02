# Wardrobe Intelligence v1

Le dressing Phase 15 est un registre personnel local. Chaque pièce est une
déclaration de la personne, jamais une offre, une observation marchand ou une
inférence silencieuse.

## Invariants

- `provenance = user_declared` ;
- `storage_scope = local_device` ;
- aucune transmission au Product Core ;
- rôle explicite parmi base, structure, footwear et accessory ;
- attributs couleur, taille et matière facultatifs, uniquement déclarés ;
- migration locale v1 → v2 sans duplication ;
- mutations sérialisées et limite de 40 pièces ;
- effacement de la copie v2 et de toute copie legacy ;
- aucune note de dressing ou préférence déduite d'une absence.

Ce contrat ne crée ni table backend, ni writer shadow, ni lecteur public, ni
Cron. Toute synchronisation future nécessitera un contrat Profile/consentement
séparé et une autorisation explicite de transport.
