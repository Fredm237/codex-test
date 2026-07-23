"""Contrats de données partagés entre l'API et le système d'agents."""

from __future__ import annotations

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
    price: float
    delivery_days: int
    delivery_cost: float = 0.0
    warranty_months: int = 24
    in_stock: bool = True
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
    real_price: float = Field(..., description="Prix réel après cashback + promo.")
    savings_vs_market: float = Field(default=0.0)


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
