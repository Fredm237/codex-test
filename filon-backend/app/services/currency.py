"""Normalisation prudente des devises observées dans les flux marchands."""

from __future__ import annotations


# Roster monétaire explicitement supporté par les parcours FILON Europe et les
# flux internationaux actuellement acceptés. Il est volontairement fermé : un
# nouveau code ISO 4217 doit être examiné puis ajouté avec une nouvelle version,
# plutôt qu'être rendu comparable parce qu'il comporte simplement trois lettres.
SUPPORTED_CURRENCY_ROSTER_VERSION = "filon-currency-roster-2026-08-29-v1"
SUPPORTED_CURRENCY_CODES = frozenset(
    {
        # Marchés FILON et Europe élargie.
        "EUR",
        "CHF",
        "GBP",
        "DKK",
        "SEK",
        "NOK",
        "ISK",
        "PLN",
        "CZK",
        "HUF",
        "RON",
        "BGN",
        "ALL",
        "BAM",
        "MKD",
        "RSD",
        "MDL",
        "UAH",
        "TRY",
        "GEL",
        "AMD",
        "AZN",
        # Devises internationales rencontrées dans les catalogues partenaires.
        "USD",
        "CAD",
        "AUD",
        "NZD",
        "JPY",
        "CNY",
        "HKD",
        "SGD",
        "KRW",
        "INR",
        "AED",
        "SAR",
        "ILS",
        "ZAR",
    }
)


def normalize_currency_code(value: object) -> str | None:
    """Retourne un code monétaire exploitable, sinon l'inconnue explicite.

    Le catalogue reçoit parfois ``None``, une chaîne vide ou un libellé tel que
    ``unknown``. Aucun de ces cas ne permet de comparer un prix ni d'appliquer
    un budget. Les codes valides restent normalisés en majuscules sans inventer
    de devise à partir du pays ou du marchand.
    """

    if not isinstance(value, str):
        return None
    code = value.strip().upper()
    if code not in SUPPORTED_CURRENCY_CODES:
        return None
    return code
