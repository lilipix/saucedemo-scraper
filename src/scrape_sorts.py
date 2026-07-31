import json

from config import (
    AVAILABLE_PRODUCTS,
    HEADLESS,
    INVENTORY_URL,
    MAX_PRODUCTS,
    NAVIGATION_DELAY_MS,
    RAW_SORTS_PATH,
    STATE_PATH,
    TEST_ID_ATTRIBUTE,
)
from playwright.sync_api import Page, expect, sync_playwright


SORTS_PATH = RAW_SORTS_PATH


# Valeurs présentes dans le menu de tri de Sauce Demo.
SORT_OPTIONS = {
    "az": "Nom : A à Z",
    "za": "Nom : Z à A",
    "lohi": "Prix : croissant",
    "hilo": "Prix : décroissant",
}


def extract_current_order(page: Page) -> list[dict]:
    """Collecte l'ordre actuellement affiché des produits configurés."""

    cards = page.get_by_test_id("inventory-item")

    expect(cards).to_have_count(AVAILABLE_PRODUCTS)


    products = []

    for sort_order, card in enumerate(cards.all()[:MAX_PRODUCTS], start=1):
        products.append(
            {
                "name": card.get_by_test_id(
                    "inventory-item-name"
                ).inner_text().strip(),
                "price": card.get_by_test_id(
                    "inventory-item-price"
                ).inner_text().strip(),
                "sort_order": sort_order,
            }
        )

    return products


def collect_sorts(page: Page) -> list[dict]:
    """Applique les quatre tris et collecte chaque ordre obtenu."""

    sort_select = page.get_by_test_id("product-sort-container")
    results = []

    for option_value, option_label in SORT_OPTIONS.items():
        # Sélectionne le tri grâce à la valeur de son option HTML.
        sort_select.select_option(option_value)

        # Attend que le menu confirme la sélection.
        expect(sort_select).to_have_value(option_value)

        if NAVIGATION_DELAY_MS > 0:
            page.wait_for_timeout(NAVIGATION_DELAY_MS)

        current_order = extract_current_order(page)

        results.append(
            {
                "sort": option_value,
                "label": option_label,
                "products": current_order,
            }
        )

        print(f"\n{option_label}")

        for product in current_order:
            print(
                f"{product['sort_order']}. "
                f"{product['name']} — "
                f"{product['price']}"
            )

    return results


def save_sorts(sorts: list[dict]) -> None:
    """Enregistre les quatre ordres de tri dans un fichier JSON."""

    SORTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with SORTS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            sorts,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    # Le script doit accéder directement à l'inventaire sans reconnexion.
    if not STATE_PATH.exists():
        raise FileNotFoundError(
            "Session absente : exécute d'abord python src/login.py"
        )

    with sync_playwright() as playwright:
        # Sauce Demo utilise l'attribut data-test.
        playwright.selectors.set_test_id_attribute(TEST_ID_ATTRIBUTE)

        browser = playwright.chromium.launch(headless=HEADLESS)

        # Réutilisation de l'état connecté précédemment enregistré.
        context = browser.new_context(storage_state=STATE_PATH)
        page = context.new_page()

        page.goto(INVENTORY_URL, wait_until="domcontentloaded")

        # Vérifie que la session donne bien accès aux produits.
        expect(
            page.get_by_test_id("inventory-item")
        ).to_have_count(AVAILABLE_PRODUCTS)

        sorts = collect_sorts(page)
        save_sorts(sorts)

        print(f"\nNombre de tris collectés : {len(sorts)}")
        print(f"Données enregistrées dans : {SORTS_PATH}")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
