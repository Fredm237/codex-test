"""Contrats de données partagés entre l'API et le système d'agents."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AdviseRequest(BaseModel):
    query: str = Field(..., description="Besoin exprimé en langage naturel.")
    budget: float | None = Field(default=None, description="Budget max en euros.")
    locale: str = Field(default="fr-BE")


class Criteria(BaseModel):
    """Sortie de l'agent Compréhension : le besoin traduit en critères."""

    category: str | None = None
    budget_max: float | None = None
    usage: list[str] = Field(default_factory=list)
    must_have: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class Offer(BaseModel):
    merchant: str
    price: float = Field(..., gt=0)
    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=8,
        description="Devise observée du prix article.",
    )
    observed_at: datetime | None = Field(
        default=None,
        description="Horodatage de l'observation prix/stock utilisée.",
    )
    # Les flux marchands (Awin) ne portent ni délai de livraison ni durée de
    # garantie : `catalog_source._shape()` les laisse volontairement à None
    # plutôt que d'inventer une valeur. Le schéma doit donc les accepter comme
    # absents, sinon la sérialisation de la réponse échoue en ValidationError.
    delivery_days: int | None = Field(default=None, ge=0)
    delivery_cost: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Frais de livraison observés. None signifie que la source ne les "
            "fournit pas ; ce n'est jamais une livraison gratuite."
        ),
    )
    warranty_months: int | None = Field(default=None, ge=0)
    in_stock: bool | None = Field(
        default=None,
        description=(
            "Disponibilité du dernier flux marchand. None signifie inconnue et "
            "ne doit jamais être interprété comme en stock."
        ),
    )
    affiliate_network: str | None = None


class Cashback(BaseModel):
    platform: str
    rate_percent: float
    amount: float


class Promo(BaseModel):
    code: str
    description: str
    amount: float
    stackable: bool = False


class PriceHistory(BaseModel):
    current: float
    average_90d: float
    min_90d: float
    max_90d: float
    trend: str  # "baisse" | "hausse" | "stable"
    buy_signal: str  # "acheter" | "attendre"
    reason: str


class ReviewSummary(BaseModel):
    count: int
    rating: float
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)


class ProductAnalysis(BaseModel):
    product_id: str
    name: str
    specs: dict[str, str] = Field(default_factory=dict)
    best_offer: Offer
    cashback: Cashback | None = None
    promo: Promo | None = None
    history: PriceHistory | None = None
    reviews: ReviewSummary | None = None
    real_price: float = Field(
        ...,
        description=(
            "Prix calculé après cashback et promo. Les frais de livraison ne "
            "sont inclus que lorsque shipping_cost_known vaut true."
        ),
    )
    shipping_cost_known: bool = Field(
        default=False,
        description="True uniquement si le coût de livraison a été observé.",
    )
    price_comparison_complete: bool = Field(
        default=False,
        description=(
            "True uniquement si toutes les offres comparées ont un total "
            "prix + livraison observé dans la même devise."
        ),
    )
    savings_vs_market: float | None = Field(
        default=None,
        description=(
            "Écart au total moyen comparable. None lorsque la livraison ou la "
            "devise empêche une comparaison complète."
        ),
    )


class Recommendation(BaseModel):
    product: ProductAnalysis
    verdict: str  # "acheter" | "attendre"
    headline: str
    reasons: list[str] = Field(default_factory=list)


class AdviseResponse(BaseModel):
    query: str
    criteria: Criteria
    recommendation: Recommendation | None = None
    alternatives: list[ProductAnalysis] = Field(default_factory=list)
    trace: list[str] = Field(
        default_factory=list, description="Journal des agents exécutés."
    )
