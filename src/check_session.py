from config import (
    AVAILABLE_PRODUCTS,
    HEADLESS,
    INVENTORY_URL,
    STATE_PATH,
    TEST_ID_ATTRIBUTE,
)
from playwright.sync_api import expect, sync_playwright
import re


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

        expect(page).to_have_url(re.compile(r".*/inventory\.html"))

        products = page.get_by_test_id("inventory-item")
        expect(products).to_have_count(AVAILABLE_PRODUCTS)

        print("Session réutilisée sans reconnexion")
        print(f"Produits visibles : {products.count()}")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
