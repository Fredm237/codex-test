"""Régressions des intrusions visibles signalées par l’utilisateur dans les rayons publics."""

import pytest

from app.services.taxonomy import classify, classify_subcategory


def destination(source: str | None, name: str, brand: str | None = None) -> tuple[str | None, str | None]:
    category = classify(source, name, brand)
    return category, classify_subcategory(category, name, source)


@pytest.mark.parametrize(
    ("source", "name", "brand", "expected"),
    [
        (None, "WMNS X MOON BOOT LEGGING", "Adidas", ("Mode femme", "Pantalons & Jeans")),
        (None, "X MOON BOOT ULTRABOOST 1.0", "Adidas", ("Chaussures", "Baskets & Sneakers")),
        (None, "Jollein Changing Table Basket - Cosy Knit", "Jollein", ("Bébé & Puériculture", None)),
        (
            "Lifestyle > Sneakers > Junior > Mixte",
            "Baskets enfant Hummel rubber boot",
            "Hummel",
            ("Chaussures", "Bottes & Bottines"),
        ),
        (
            "Women's Clothing",
            "Ice Silk Nightgown Sexy Backless Cross Suspender Skirt Home Wear Thin Breathable Short Skirt",
            "voghion",
            ("Mode femme", "Lingerie & Nuit"),
        ),
        (
            "Women's Clothing",
            "Long Sleeve Solid Pocket Cardigan Blazer",
            "voghion",
            ("Mode femme", "Manteaux & Vestes"),
        ),
        (
            "Women's Clothing",
            "Winter Coat Double-breasted Cardigan Thermal Anti-wrinkle Lapel Women Winter Coat Women Overcoat",
            "voghion",
            ("Mode femme", "Manteaux & Vestes"),
        ),
        (
            "Women's Clothing",
            "Turtleneck Oversized Knitted Sweater Women Pullover Autumn Winter White Black Sweater Female Jumpers Casual Ladies Tops",
            "voghion",
            ("Mode femme", "Pulls & Sweats"),
        ),
        (
            "Luggage & Bags",
            "Shoulder Bag 2026 Top Quality Head Layer Cowhide Wide Shoulder Strap Fashion Large Capacity High-end Ladies Messenger Bag",
            "voghion",
            ("Bagagerie", "Sacs à main"),
        ),
        (
            "Beauté & Santé > Hygiène corporelle > Rasage & Épilation",
            "Tondeuse bikini 6 en 1 - Sansbeauté - Epilateur électrique",
            "Sansbeauté",
            ("Beauté & Parfum", "Rasage & Épilation"),
        ),
        ("Make up", "NYX Lingerie Glans Helder", "NYX", ("Beauté & Parfum", "Maquillage")),
        (
            "Hair Extensions & Wigs",
            "Short bob Ombre 613 orange color lace frontal wig 100% human hair wig for women",
            "voghion",
            ("Beauté & Parfum", "Cheveux"),
        ),
        (None, "Chaussettes invisibles femme Short n Snug", "Liv", ("Mode femme", "Chaussettes")),
    ],
)
def test_user_reported_intrusions_are_routed_by_explicit_object(
    source: str | None, name: str, brand: str | None, expected: tuple[str, str | None]
) -> None:
    assert destination(source, name, brand) == expected


@pytest.mark.parametrize(
    ("source", "name", "brand", "expected"),
    [
        (None, "AXEL ARIGATO Pillow Boot", "Axel Arigato", ("Chaussures", "Bottes & Bottines")),
        ("Women's Clothing", "Soft knitted cardigan for women", "voghion", ("Mode femme", "Pulls & Sweats")),
        ("Women's Clothing", "Satin midi skirt for women", "voghion", ("Mode femme", "Jupes")),
        ("Jardinage", "Tondeuse à gazon électrique", None, ("Jardin & Bricolage", "Jardinage & Apiculture")),
        ("Women's Clothing", "T-shirt femme col rond", None, ("Mode femme", "Hauts & T-shirts")),
    ],
)
def test_correct_objects_remain_in_their_intended_rays(
    source: str | None, name: str, brand: str | None, expected: tuple[str, str | None]
) -> None:
    assert destination(source, name, brand) == expected
