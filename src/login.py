import os
import re
import sys

from config import (
    AVAILABLE_PRODUCTS,
    BASE_URL,
    HEADLESS,
    STATE_PATH,
    TEST_ID_ATTRIBUTE,
)
from playwright.sync_api import expect, sync_playwright


def get_required_env(name: str) -> str:
    """Recupere une variable d'environnement obligatoire."""
    value = os.environ.get(name)

    if not value:
        sys.exit(f"{name} doit etre exporte")

    return value


# Les identifiants sont lus depuis l'environnement pour eviter de les ecrire
# directement dans le code source.
USERNAME = get_required_env("SAUCEDEMO_USERNAME")
PASSWORD = get_required_env("SAUCEDEMO_PASSWORD")


def main() -> None:
    # Cree le dossier qui contiendra l'etat de session Playwright si besoin.
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        playwright.selectors.set_test_id_attribute(TEST_ID_ATTRIBUTE)

        # Lance Chromium, cree un contexte de navigation, puis ouvre une page.
        browser = playwright.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        page = context.new_page()

        # Ouvre la page de connexion et attend que le HTML initial soit charge.
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Remplit le formulaire de connexion avec les identifiants exportes.
        page.get_by_placeholder("Username").fill(USERNAME)
        page.get_by_placeholder("Password").fill(PASSWORD)
        page.get_by_role("button", name="Login").click()

        # Verifie que la connexion a bien redirige vers la page d'inventaire.
        expect(page).to_have_url(re.compile(r".*/inventory\.html"))

        # Verifie que le nombre attendu de produits est visible.
        products = page.get_by_test_id("inventory-item")
        expect(products).to_have_count(AVAILABLE_PRODUCTS)

        # Sauvegarde les cookies et informations de session pour les autres scripts.
        context.storage_state(path=STATE_PATH)

        print("Connexion réussie")
        print(f"Produits visibles : {products.count()}")
        print(f"Session enregistrée dans : {STATE_PATH}")

        # Ferme proprement les ressources Playwright.
        context.close()
        browser.close()


if __name__ == "__main__":
    # Point d'entree du script lorsqu'il est lance directement.
    main()
