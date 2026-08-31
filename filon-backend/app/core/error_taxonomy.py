"""Registre canonique des erreurs de qualité produit FILON.

Les valeurs sont persistées et peuvent participer à des clés d'idempotence :
elles sont donc immuables dans une version donnée de la taxonomie.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProductErrorCode(StrEnum):
    """Codes stables des erreurs de données et de décision produit."""

    WRONG_CATEGORY = "E001_WRONG_CATEGORY"
    WRONG_PRODUCT_ROLE = "E002_WRONG_PRODUCT_ROLE"
    FALSE_PRODUCT_MERGE = "E003_FALSE_PRODUCT_MERGE"
    FALSE_PRODUCT_SPLIT = "E004_FALSE_PRODUCT_SPLIT"
    WRONG_VARIANT = "E005_WRONG_VARIANT"
    IRRELEVANT_RETRIEVAL = "E006_IRRELEVANT_RETRIEVAL"
    HARD_CONSTRAINT_VIOLATION = "E007_HARD_CONSTRAINT_VIOLATION"
    WRONG_PRICE = "E008_WRONG_PRICE"
    STALE_PRICE = "E009_STALE_PRICE"
    WRONG_STOCK = "E010_WRONG_STOCK"
    WRONG_SHIPPING = "E011_WRONG_SHIPPING"
    UNSUPPORTED_CLAIM = "E012_UNSUPPORTED_CLAIM"
    WRONG_VERDICT = "E013_WRONG_VERDICT"
    OVERCONFIDENT_DECISION = "E014_OVERCONFIDENT_DECISION"
    DUPLICATE_PRODUCT = "E015_DUPLICATE_PRODUCT"

    # Extensions FILON pour la validité de l'ingestion et des observations.
    SCHEMA_INVALID = "E016_SCHEMA_INVALID"
    INVALID_IDENTIFIER = "E017_INVALID_IDENTIFIER"
    CURRENCY_MISMATCH = "E018_CURRENCY_MISMATCH"

    @property
    def number(self) -> int:
        """Retourne le numéro stable du code, sans son préfixe ``E``."""

        return int(self.value[1:4])


PRODUCT_ERROR_CODES: tuple[str, ...] = tuple(code.value for code in ProductErrorCode)


@dataclass(frozen=True, slots=True)
class DecodedProductErrorCode:
    """Lecture sans perte d'une valeur potentiellement issue d'une version future."""

    raw_value: str
    known: ProductErrorCode | None

    @property
    def is_known(self) -> bool:
        return self.known is not None


def decode_product_error_code(raw_value: str) -> DecodedProductErrorCode:
    """Reconnaît un code v1 sans normaliser ni perdre une valeur inconnue."""

    try:
        known = ProductErrorCode(raw_value)
    except ValueError:
        known = None
    return DecodedProductErrorCode(raw_value=raw_value, known=known)
