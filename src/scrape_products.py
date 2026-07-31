from config import (
    AVAILABLE_PRODUCTS,
    HEADLESS,
    INVENTORY_URL,
    MAX_PRODUCTS,
    RAW_PRODUCTS_PATH,
    STATE_PATH,
    TEST_ID_ATTRIBUTE,
)
from playwright.sync_api import Locator, Page, expect, sync_playwright
import json

RAW_PATH = RAW_PRODUCTS_PATH


def require_product_field(
    card: Locator,
    test_id: str,
    field_name: str,
    sort_order: int,
) -> Locator:
    field = card.get_by_test_id(test_id)

    if field.count() != 1:
        raise ValueError(
            f"Ancrage introuvable pour le champ '{field_name}' "
            f"du produit en position {sort_order} : data-test='{test_id}'"
        )

    return field


def save_raw_products(products: list[dict]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)

    with RAW_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            products,
            file,
            ensure_ascii=False,
            indent=2,
        )

def extract_products(page: Page) -> list[dict]:
    products = []

    cards = page.get_by_test_id("inventory-item")
    expect(cards).to_have_count(AVAILABLE_PRODUCTS)

    for sort_order, card in enumerate(cards.all()[:MAX_PRODUCTS], start=1):
        name_element = require_product_field(
            card,
            "inventory-item-name",
            "name",
            sort_order,
        )
        price_element = require_product_field(
            card,
            "inventory-item-price",
            "price",
            sort_order,
        )
        description_element = require_product_field(
            card,
            "inventory-item-desc",
            "description",
            sort_order,
        )

        # Le href est sur la balise <a> parente du nom
        detail_link = name_element.locator("..")
        relative_url = detail_link.get_attribute("href")

        if relative_url is None:
            raise ValueError(
                f"URL de la page détail absente pour le produit "
                f"en position {sort_order}"
            )

        products.append(
            {
                "name": name_element.inner_text().strip(),
                "price": price_element.inner_text().strip(),
                "description": description_element.inner_text().strip(),
                "url": relative_url,
                "sort_order": sort_order,
            }
        )

    return products


def main() -> None:
    if not STATE_PATH.exists():
        raise FileNotFoundError(
            "Session absente : exécute d'abord python src/login.py"
        )

    with sync_playwright() as playwright:
        playwright.selectors.set_test_id_attribute(TEST_ID_ATTRIBUTE)

        browser = playwright.chromium.launch(headless=HEADLESS)
        context = browser.new_context(storage_state=STATE_PATH)
        page = context.new_page()

        page.goto(INVENTORY_URL, wait_until="domcontentloaded")

        products = extract_products(page)

        save_raw_products(products)

        for product in products:
          print(product)

        print(f"\nNombre de produits collectés : {len(products)}")
        print(f"Données brutes enregistrées dans : {RAW_PATH}")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
