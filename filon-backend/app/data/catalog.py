"""Catalogue produit et offres marchandes — données de démonstration.

Remplace, en Phase 2, par les connecteurs réels (APIs marchands et réseaux
d'affiliation Awin / Impact / CJ / Rakuten). Le format ci-dessous est le
contrat que ces connecteurs devront produire.
"""

from __future__ import annotations

from typing import Any

# Chaque produit : specs + plusieurs offres marchandes + méta d'analyse.
CATALOG: list[dict[str, Any]] = [
    {
        "product_id": "lap-acer-a315",
        "name": "Acer Aspire 15 (Ryzen 5, 16 Go, 512 Go SSD)",
        "category": "ordinateur_portable",
        "tags": ["étudiant", "bureautique", "léger", "ssd", "web"],
        "specs": {"cpu": "Ryzen 5", "ram": "16 Go", "stockage": "512 Go SSD", "poids": "1.7 kg", "autonomie": "9 h"},
        "rating": 4.3,
        "reviews_count": 2140,
        "offers": [
            {"merchant": "Amazon", "price": 649.0, "delivery_days": 1, "warranty_months": 24, "affiliate_network": "Amazon"},
            {"merchant": "Fnac", "price": 679.0, "delivery_days": 2, "warranty_months": 24, "affiliate_network": "Awin"},
            {"merchant": "Boulanger", "price": 699.0, "delivery_days": 3, "warranty_months": 24, "affiliate_network": "CJ"},
        ],
        "price_history": {"average_90d": 719.0, "min_90d": 639.0, "max_90d": 799.0},
        "cashback": [
            {"platform": "iGraal", "rate_percent": 4.0},
            {"platform": "Poulpeo", "rate_percent": 3.5},
        ],
        "promos": [
            {"code": "RENTREE20", "description": "-20 € dès 500 € d'achat", "amount": 20.0, "stackable": True},
        ],
        "pros": ["Bon rapport qualité/prix", "16 Go de RAM confortables", "Léger pour la fac"],
        "cons": ["Écran un peu terne", "Autonomie moyenne en usage intensif"],
    },
    {
        "product_id": "lap-lenovo-slim5",
        "name": "Lenovo IdeaPad Slim 5 (Core i5, 16 Go, 512 Go SSD)",
        "category": "ordinateur_portable",
        "tags": ["étudiant", "bureautique", "léger", "ssd", "autonomie"],
        "specs": {"cpu": "Core i5", "ram": "16 Go", "stockage": "512 Go SSD", "poids": "1.5 kg", "autonomie": "12 h"},
        "rating": 4.5,
        "reviews_count": 3380,
        "offers": [
            {"merchant": "Fnac", "price": 749.0, "delivery_days": 2, "warranty_months": 24, "affiliate_network": "Awin"},
            {"merchant": "Amazon", "price": 769.0, "delivery_days": 1, "warranty_months": 24, "affiliate_network": "Amazon"},
            {"merchant": "Darty", "price": 779.0, "delivery_days": 2, "warranty_months": 24, "affiliate_network": "Impact"},
        ],
        "price_history": {"average_90d": 799.0, "min_90d": 739.0, "max_90d": 869.0},
        "cashback": [
            {"platform": "Poulpeo", "rate_percent": 5.0},
            {"platform": "iGraal", "rate_percent": 4.0},
        ],
        "promos": [
            {"code": "STUDENT30", "description": "-30 € offre étudiante", "amount": 30.0, "stackable": True},
        ],
        "pros": ["Excellente autonomie (12 h)", "Très léger (1,5 kg)", "Écran IPS lumineux", "Finition premium"],
        "cons": ["Un peu au-dessus des 750 €", "Pas de port Ethernet"],
    },
    {
        "product_id": "lap-hp-pav14",
        "name": "HP Pavilion 14 (Core i3, 8 Go, 256 Go SSD)",
        "category": "ordinateur_portable",
        "tags": ["étudiant", "bureautique", "web", "ssd", "budget"],
        "specs": {"cpu": "Core i3", "ram": "8 Go", "stockage": "256 Go SSD", "poids": "1.4 kg", "autonomie": "10 h"},
        "rating": 4.0,
        "reviews_count": 1520,
        "offers": [
            {"merchant": "Cdiscount", "price": 499.0, "delivery_days": 4, "warranty_months": 24, "affiliate_network": "Awin"},
            {"merchant": "Amazon", "price": 519.0, "delivery_days": 1, "warranty_months": 24, "affiliate_network": "Amazon"},
        ],
        "price_history": {"average_90d": 529.0, "min_90d": 489.0, "max_90d": 579.0},
        "cashback": [
            {"platform": "iGraal", "rate_percent": 3.0},
        ],
        "promos": [],
        "pros": ["Très abordable", "Léger et compact"],
        "cons": ["8 Go de RAM justes pour durer", "256 Go de stockage limité"],
    },
    {
        "product_id": "lap-asus-tuf-a15",
        "name": "Asus TUF Gaming A15 (Ryzen 7, RTX 4060, 16 Go)",
        "category": "ordinateur_portable",
        "tags": ["gaming", "performance", "gpu"],
        "specs": {"cpu": "Ryzen 7", "gpu": "RTX 4060", "ram": "16 Go", "stockage": "1 To SSD", "poids": "2.2 kg", "autonomie": "6 h"},
        "rating": 4.4,
        "reviews_count": 980,
        "offers": [
            {"merchant": "Amazon", "price": 1099.0, "delivery_days": 1, "warranty_months": 24, "affiliate_network": "Amazon"},
            {"merchant": "LDLC", "price": 1149.0, "delivery_days": 3, "warranty_months": 24, "affiliate_network": "CJ"},
        ],
        "price_history": {"average_90d": 1149.0, "min_90d": 1079.0, "max_90d": 1299.0},
        "cashback": [{"platform": "Poulpeo", "rate_percent": 3.0}],
        "promos": [],
        "pros": ["Excellent pour le jeu", "RTX 4060 performante"],
        "cons": ["Lourd (2,2 kg)", "Autonomie faible", "Dépasse un budget étudiant"],
    },
]


def all_products() -> list[dict[str, Any]]:
    return CATALOG
