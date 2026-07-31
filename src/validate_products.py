import json
from decimal import Decimal
from urllib.parse import parse_qs, urlparse
from datetime import datetime

from config import (
    MAX_PRODUCTS,
    PRODUCT_DETAIL_PATH,
    SAUCEDEMO_HOST,
    STAGING_PRODUCTS_PATH,
)
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


STAGING_PATH = STAGING_PRODUCTS_PATH


class Product(BaseModel):
    """Structure et règles de validation d'un produit final."""

    # Refuse les champs supplémentaires qui ne font pas partie du modèle.
    model_config = ConfigDict(extra="forbid")

    id: int = Field(ge=0)
    name: str = Field(min_length=1)
    price: Decimal = Field(gt=0, decimal_places=2)
    currency: str
    description: str = Field(min_length=1)
    url: HttpUrl
    sort_order: int = Field(ge=1, le=MAX_PRODUCTS)
    collected_at: datetime

    @field_validator("name", "description")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        """Refuse les textes constitués uniquement d'espaces."""

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Le texte ne peut pas être vide")

        return cleaned_value

    @field_validator("currency")
    @classmethod
    def currency_must_be_valid_code(cls, value: str) -> str:
        """Vérifie que la devise est un code ISO lisible."""

        cleaned_value = value.strip().upper()

        if len(cleaned_value) != 3 or not cleaned_value.isalpha():
            raise ValueError(
                "La devise doit être un code sur trois lettres"
            )

        return cleaned_value

    @field_validator("url")
    @classmethod
    def url_must_be_product_detail(cls, value: HttpUrl) -> HttpUrl:
        """Vérifie qu'il s'agit d'une page détail de Sauce Demo."""

        parsed_url = urlparse(str(value))

        if parsed_url.hostname != SAUCEDEMO_HOST:
            raise ValueError(f"Le domaine doit être {SAUCEDEMO_HOST}")

        if parsed_url.path != PRODUCT_DETAIL_PATH:
            raise ValueError(
                "L'URL doit correspondre à une page détail"
            )

        query_parameters = parse_qs(parsed_url.query)
        product_ids = query_parameters.get("id")

        if (
            not product_ids
            or len(product_ids) != 1
            or not product_ids[0].isdigit()
        ):
            raise ValueError(
                "L'URL doit contenir un identifiant numérique"
            )

        return value


def load_products() -> list[dict]:
    """Charge les produits transformés."""

    if not STAGING_PATH.exists():
        raise FileNotFoundError(
            "Fichier staging absent : exécute d'abord "
            "python src/transform_products.py"
        )

    with STAGING_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Le fichier staging doit contenir une liste"
        )

    return data


def validate_products(raw_products: list[dict]) -> list[Product]:
    """Valide le volume, les produits et l'absence de doublons."""

    if len(raw_products) != MAX_PRODUCTS:
        raise ValueError(
            f"{MAX_PRODUCTS} produits attendus, "
            f"{len(raw_products)} trouvé(s)"
        )

    products = [
        Product.model_validate(raw_product)
        for raw_product in raw_products
    ]

    names = [product.name for product in products]
    urls = [str(product.url) for product in products]
    sort_orders = [product.sort_order for product in products]
    ids = [product.id for product in products]

    if len(set(names)) != len(names):
        raise ValueError("Des noms de produits sont en doublon")

    if len(set(urls)) != len(urls):
        raise ValueError("Des URL de produits sont en doublon")

    expected_sort_orders = list(range(1, MAX_PRODUCTS + 1))

    if sorted(sort_orders) != expected_sort_orders:
        raise ValueError(
            "Les sort_order doivent contenir une fois chaque "
            f"position de 1 à {MAX_PRODUCTS}"
        )

    if len(set(ids)) != len(ids):
        raise ValueError("Des identifiants de produits sont en doublon")

    return products


def main() -> None:
    raw_products = load_products()
    products = validate_products(raw_products)

    for product in products:
        print(
            f"OK — {product.sort_order}. "
            f"id : {product.id} "
            f"{product.name} — "
            f"{product.price} {product.currency} "
            f"Date : {product.collected_at}"
        )

    print(f"\nValidation réussie : {len(products)} produits valides")


if __name__ == "__main__":
    main()
