import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse
from playwright.sync_api import Page, expect, sync_playwright
from config import (
    AVAILABLE_PRODUCTS,
    HEADLESS,
    INVENTORY_URL,
    NAVIGATION_DELAY_MS,
    RAW_DETAILS_PATH,
    RAW_PRODUCTS_PATH,
    STATE_PATH,
    TEST_ID_ATTRIBUTE,
)


PRODUCTS_PATH = RAW_PRODUCTS_PATH
DETAILS_PATH = RAW_DETAILS_PATH


def load_products() -> list[dict]:
    """Charge les produits collectés depuis l'inventaire."""

    # Sans ce fichier, nous ne connaissons pas les produits à parcourir.
    if not PRODUCTS_PATH.exists():
        raise FileNotFoundError(
            "Produits absents : exécute d'abord "
            "python src/scrape_products.py"
        )

    with PRODUCTS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)

def extract_product_id(product_url: str) -> int:
    """Extrait l'identifiant stable présent dans l'URL du produit."""

    query_parameters = parse_qs(urlparse(product_url).query)
    product_ids = query_parameters.get("id")

    if not product_ids or not product_ids[0].isdigit():
        raise ValueError(
            f"Identifiant absent ou invalide dans l'URL : {product_url}"
        )

    return int(product_ids[0])

def extract_product_detail(page: Page, product_name: str) -> dict:
    """Ouvre la fiche d'un produit et collecte ses données brutes."""

    # On retrouve le produit grâce à son nom plutôt que par sa position.
    # Cela reste fiable même si l'ordre des produits change.
    card = page.get_by_test_id("inventory-item").filter(
        has=page.get_by_test_id(
            "inventory-item-name"
        ).filter(has_text=product_name)
    )

    # Il doit exister exactement une carte correspondant à ce produit.
    expect(card).to_have_count(1)

    # Le href vaut "#" dans le DOM : le clic permet à JavaScript
    # d'effectuer la navigation vers la véritable page détail.
    card.get_by_test_id("inventory-item-name").click()

    # On attend une condition précise au lieu d'utiliser une attente fixe.
    expect(page).to_have_url(
        re.compile(r".*/inventory-item\.html\?id=\d+")
    )

    # On vérifie que le contenu principal de la fiche est bien affiché.
    expect(
        page.get_by_test_id("inventory-item-name")
    ).to_be_visible()

    product_url = page.url
    collected_at = datetime.now(timezone.utc).isoformat()

    # Les données restent brutes à ce stade :
    # le prix conserve notamment son symbole "$".
    detail = {
        "id": extract_product_id(product_url),
        "name": page.get_by_test_id(
            "inventory-item-name"
        ).inner_text().strip(),
        "price": page.get_by_test_id(
            "inventory-item-price"
        ).inner_text().strip(),
        "description": page.get_by_test_id(
            "inventory-item-desc"
        ).inner_text().strip(),
        # Contrairement au href "#", page.url contient l'URL réelle.
        "url": page.url,
        "collected_at": collected_at,
    }

    # Retour à l'inventaire pour traiter le produit suivant.
    page.go_back(wait_until="domcontentloaded")

    if NAVIGATION_DELAY_MS > 0:
        page.wait_for_timeout(NAVIGATION_DELAY_MS)

    # On vérifie que le retour est terminé et que les cartes
    # sont de nouveau disponibles avant de continuer.
    expect(page).to_have_url(
        re.compile(r".*/inventory\.html")
    )
    expect(
        page.get_by_test_id("inventory-item")
    ).to_have_count(AVAILABLE_PRODUCTS)

    return detail


def save_details(details: list[dict]) -> None:
    """Enregistre les données brutes des pages détail en JSON."""

    # Crée le dossier raw s'il n'existe pas encore.
    DETAILS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with DETAILS_PATH.open("w", encoding="utf-8") as file:
        json.dump(
            details,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    # Le script réutilise la session créée par login.py.
    # Il ne saisit donc pas de nouveau les identifiants.
    if not STATE_PATH.exists():
        raise FileNotFoundError(
            "Session absente : exécute d'abord python src/login.py"
        )

    products = load_products()

    with sync_playwright() as playwright:
        # Sauce Demo utilise data-test au lieu de data-testid.
        playwright.selectors.set_test_id_attribute(TEST_ID_ATTRIBUTE)

        browser = playwright.chromium.launch(headless=HEADLESS)

        # Chargement des cookies et du stockage local de la session sauvegardée.
        context = browser.new_context(storage_state=STATE_PATH)
        page = context.new_page()

        page.goto(INVENTORY_URL, wait_until="domcontentloaded")

        # Cette vérification prouve que la session réutilisée permet
        # d'accéder directement à l'inventaire.
        expect(
            page.get_by_test_id("inventory-item")
        ).to_have_count(AVAILABLE_PRODUCTS)

        details = []

        # Chaque produit provient du fichier products.json.
        for product in products:
            detail = extract_product_detail(
                page,
                product["name"],
            )
            details.append(detail)
            print(detail)

        save_details(details)

        print(f"\nPages détail collectées : {len(details)}")
        print(f"Données enregistrées dans : {DETAILS_PATH}")

        context.close()
        browser.close()


# main() ne s'exécute que si ce fichier est lancé directement.
if __name__ == "__main__":
    main()
