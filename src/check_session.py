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
    # Le fichier de session est cree par login.py apres une connexion reussie.
    if not STATE_PATH.exists():
        raise FileNotFoundError(
            "Session absente : exécute d'abord python src/login.py"
        )

    with sync_playwright() as playwright:
        playwright.selectors.set_test_id_attribute(TEST_ID_ATTRIBUTE)

        # Lance le navigateur avec le meme mode que les autres scripts.
        browser = playwright.chromium.launch(headless=HEADLESS)

        # Recharge les cookies et informations de session sauvegardes.
        context = browser.new_context(storage_state=STATE_PATH)
        page = context.new_page()

        # Ouvre directement la page inventaire sans repasser par le formulaire.
        page.goto(INVENTORY_URL, wait_until="domcontentloaded")

        # Verifie que l'utilisateur est toujours considere comme connecte.
        expect(page).to_have_url(re.compile(r".*/inventory\.html"))

        # Controle que la page affiche bien le nombre attendu de produits.
        products = page.get_by_test_id("inventory-item")
        expect(products).to_have_count(AVAILABLE_PRODUCTS)

        print("Session réutilisée sans reconnexion")
        print(f"Produits visibles : {products.count()}")

        # Ferme proprement les ressources Playwright.
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
