"""Modèles PostgreSQL de FILON.

Deux familles :
- Mémoire classique (utilisateurs, recherches, alertes).
- Catalogue Awin (marchands inscrits, offres produits, historique de prix) — le
  socle « couche de données » qui alimentera les pages catalogue/marchand/produit
  et les scores. Alimenté par l'ingestion Awin (app/services/awin_catalog.py).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    searches: Mapped[list["SearchLog"]] = relationship(back_populates="user")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512))
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class SearchLog(Base):
    __tablename__ = "search_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    query: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User | None"] = relationship(back_populates="searches")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_external_id: Mapped[str] = mapped_column(String(128))
    target_price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="alerts")


# ─────────────────────────────────────────────────────────────────────────────
# Catalogue Awin — le socle « couche de données »
# ─────────────────────────────────────────────────────────────────────────────


class Merchant(Base):
    """Un annonceur Awin auquel l'éditeur FILON est inscrit (programme « joined »)."""

    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    awin_mid: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cashback: Mapped[str | None] = mapped_column(String(64), nullable=True)
    joined: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    offers: Mapped[list["Offer"]] = relationship(back_populates="merchant")


class CatalogProduct(Base):
    """Un produit réel, regroupant les offres de plusieurs marchands par EAN.

    Distinct du modèle `Product` (mémoire classique, table `products`) : celui-ci
    est l'unité du catalogue, celle qu'on présente à l'utilisateur et sur
    laquelle on compare les marchands.
    """

    __tablename__ = "catalog_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    ean: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512))
    brand: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    offers_count: Mapped[int] = mapped_column(Integer, default=0)
    merchants_count: Mapped[int] = mapped_column(Integer, default=0, index=True)
    price_min: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    price_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    offers: Mapped[list["Offer"]] = relationship(back_populates="product")


class Offer(Base):
    """Une offre produit issue d'un feed Awin (produit × marchand)."""

    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint("merchant_id", "awin_product_id", name="uq_offer_merchant_product"),
        Index("ix_offer_category", "category"),
        Index("ix_offer_brand", "brand"),
        Index("ix_offer_ean", "ean"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    # Rattachement au produit regroupé par EAN. Nullable : une offre sans EAN
    # exploitable reste autonome plutôt que d'être rattachée à tort.
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("catalog_products.id"), nullable=True, index=True
    )
    awin_product_id: Mapped[str] = mapped_column(String(191))
    ean: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(512))
    brand: Mapped[str | None] = mapped_column(String(191), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Catégorie FILON, dérivée du nom et de la catégorie du marchand. Les flux
    # déclarent des libellés hétérogènes et parfois faux : celle-ci est la seule
    # sur laquelle on peut bâtir une navigation.
    filon_category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Sous-rayon, à l'intérieur du rayon. Nullable : tous les rayons n'en ont pas.
    filon_subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # Clé de regroupement des doublons (déclinaisons de taille, mêmes articles
    # relistés). Calculée à l'ingestion plutôt qu'à la requête : dédupliquer
    # 795 000 lignes par fenêtrage à chaque affichage était trop coûteux.
    dedup_key: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    # Représentant retenu pour sa clé — le moins cher. Un booléen indexé rend le
    # filtrage immédiat, là où un DISTINCT imposait un tri complet.
    is_canonical: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    # Article du rayon adulte, exclu de tout affichage public. Un annonceur a
    # refusé le partenariat au motif « Contenu pour adultes » : le drapeau est
    # posé à l'ingestion (app/services/safety.py) plutôt qu'évalué à la requête,
    # pour que le filtre soit un simple index sur 795 000 lignes.
    is_adult: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Prix relevé juste avant la dernière écriture, alimenté par l'ingestion dans
    # le `SET` du `ON CONFLICT` (où `offers.price` désigne encore l'ancienne
    # valeur). Sert à n'écrire un `price_snapshots` que lorsque le prix bouge
    # réellement : l'insertion était inconditionnelle et produisait 2 413 308
    # lignes par jour pour 5 447 changements effectifs, soit 99,8 % d'écritures
    # inutiles et environ 65 Go par an. Voir app/services/awin_catalog.py.
    previous_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    in_stock: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    deep_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    merchant: Mapped["Merchant"] = relationship(back_populates="offers")
    product: Mapped["CatalogProduct | None"] = relationship(back_populates="offers")


class PriceSnapshot(Base):
    """Un relevé de prix horodaté — la brique d'historique (ne se rattrape pas)."""

    __tablename__ = "price_snapshots"
    __table_args__ = (Index("ix_snapshot_offer_time", "offer_id", "captured_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), index=True)
    price: Mapped[float] = mapped_column(Float)
    in_stock: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
