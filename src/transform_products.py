import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from config import (
    MAX_PRODUCTS,
    RAW_DETAILS_PATH,
    RAW_PRODUCTS_PATH,
    STAGING_PRODUCTS_PATH,
    STAGING_PRODUCTS_JSONL_PATH,
)

PRODUCTS_PATH = RAW_PRODUCTS_PATH
DETAILS_PATH = RAW_DETAILS_PATH
STAGING_PATH = STAGING_PRODUCTS_PATH
STAGING_JSONL_PATH = STAGING_PRODUCTS_JSONL_PATH

CURRENCIES_BY_SYMBOL = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
}


def load_json(path: Path) -> list[dict]:
    """Charge une liste d'objets depuis un fichier JSON."""

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Le fichier {path} doit contenir une liste")

    return data


def normalize_price(raw_price: str) -> str:
    """Transforme un prix brut comme '$29.99' en '29.99'."""

    cleaned_price = raw_price.strip()

    for symbol in CURRENCIES_BY_SYMBOL:
        cleaned_price = cleaned_price.replace(symbol, "")

    cleaned_price = cleaned_price.strip()

    try:
        price = Decimal(cleaned_price)
    except InvalidOperation as error:
        raise ValueError(
            f"Prix invalide rencontré : {raw_price}"
        ) from error

    return str(price)

def extract_currency(raw_price: str) -> str :
    """Déduit le code de la devise en fonction du symbole du prix brut."""
    for symbol, currency in CURRENCIES_BY_SYMBOL.items():
        if symbol in raw_price:
            return currency

    raise ValueError(
        f"Devise inconnue dans le prix : {raw_price}"
    )


def extract_product_id(product_url: str) -> int:
    """Extrait l'identifiant stable présent dans l'URL du produit."""

    query_parameters = parse_qs(urlparse(product_url).query)
    product_ids = query_parameters.get("id")

    if not product_ids or not product_ids[0].isdigit():
        raise ValueError(
            f"Identifiant absent ou invalide dans l'URL : {product_url}"
        )

    return int(product_ids[0])


def transform_products(
    raw_products: list[dict],
    product_details: list[dict],
) -> list[dict]:
    """Fusionne et transforme les données des produits."""

    # Indexation des pages détail par nom pour retrouver rapidement
    # la fiche correspondant à chaque produit de l'inventaire.
    details_by_name = {
        detail["name"]: detail
        for detail in product_details
    }

    transformed_products = []

    for raw_product in raw_products:
        product_name = raw_product["name"]
        detail = details_by_name.get(product_name)

        if detail is None:
            raise ValueError(
                f"Page détail absente pour : {product_name}"
            )
        raw_price = detail["price"]
        product_url = detail["url"]
        collected_at = datetime.now(timezone.utc).isoformat()

        # La page détail fournit la véritable URL.
        # Le sort_order provient de l'ordre par défaut de l'inventaire.
        transformed_products.append(
            {
                "id": extract_product_id(product_url),
                "name": product_name,
                "price": normalize_price(raw_price),
                "currency": extract_currency(raw_price),
                "description": detail["description"],
                "url": product_url,
                "sort_order": raw_product["sort_order"],
                "collected_at": collected_at,
            }
        )

    return transformed_products


def save_products(products: list[dict]) -> None:
    """Enregistre les produits transformés au format JSON."""

    STAGING_PATH.parent.mkdir(parents=True, exist_ok=True)

    with STAGING_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            products,
            file,
            ensure_ascii=False,
            indent=2,
        )


def save_products_jsonl(products: list[dict]) -> None:
    """Enregistre un produit JSON par ligne dans le fichier JSONL."""

    STAGING_JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)

    with STAGING_JSONL_PATH.open("w", encoding="utf-8") as file:
        for product in products:
            json_line = json.dumps(product, ensure_ascii=False)
            file.write(f"{json_line}\n")


def main() -> None:
    raw_products = load_json(PRODUCTS_PATH)
    product_details = load_json(DETAILS_PATH)

    # On vérifie les volumes attendus avant la transformation.
    if len(raw_products) != MAX_PRODUCTS:
        raise ValueError(
            f"{MAX_PRODUCTS} produits attendus dans l'inventaire, "
            f"{len(raw_products)} trouvé(s)"
        )

    if len(product_details) != MAX_PRODUCTS:
        raise ValueError(
            f"{MAX_PRODUCTS} pages détail attendues, "
            f"{len(product_details)} trouvée(s)"
        )

    products = transform_products(
        raw_products,
        product_details,
    )

    save_products(products)
    save_products_jsonl(products)

    for product in products:
        print(product)

    print(f"\nProduits transformés : {len(products)}")
    print(f"Données enregistrées dans : {STAGING_PATH}")
    print(f"Données JSONL enregistrées dans : {STAGING_JSONL_PATH}")


if __name__ == "__main__":
    main()
