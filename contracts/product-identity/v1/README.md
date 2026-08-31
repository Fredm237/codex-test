# FILON Product Identity Contracts v1

Statut : `frozen_for_shadow` depuis le 31 août 2026.

Ces contrats décrivent la frontière interne entre une observation source et
une résolution canonique shadow. Ils ne modifient aucun endpoint public v1.

| Contrat | Rôle |
|---|---|
| `identity-assertion` | un fait scalaire sourcé, sans promotion implicite |
| `identity-resolution` | une décision versionnée : resolved, quarantine ou unresolved |

Règles :

- `raw_source_record_id`, `source_ref` et `observed_at` sont obligatoires ;
- une assertion `observed` n'est pas une identité canonique ;
- `gtin` est global, `mpn` est scoped par Brand, `merchant_sku` par marchand ;
- toute résolution favorable cite au moins une preuve raw ;
- une quarantaine ou une inconnue ne porte jamais de `canonical_id` ;
- aucune valeur `unknown` n'est convertie en preuve favorable.

La sémantique détaillée est fixée dans
[ADR-006](../../../docs/architecture/ADR-006-PRODUCT-IDENTITY-V1-BOUNDARIES.md).
