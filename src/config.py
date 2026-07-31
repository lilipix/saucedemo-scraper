from pathlib import Path


# Nombre total de produits disponibles sur le site Sauce Demo.
AVAILABLE_PRODUCTS = 6

# Nombre de produits a traiter.
MAX_PRODUCTS = AVAILABLE_PRODUCTS

# Delai optionnel entre les actions de navigation.
NAVIGATION_DELAY_MS = 500

# Affiche le navigateur pendant l'execution du script.
HEADLESS = False

# Informations principales sur le site cible.
BASE_URL = "https://www.saucedemo.com/"
INVENTORY_URL = f"{BASE_URL}inventory.html"
SAUCEDEMO_HOST = "www.saucedemo.com"
PRODUCT_DETAIL_PATH = "/inventory-item.html"

# Sauce Demo utilise data-test comme attribut de test.
TEST_ID_ATTRIBUTE = "data-test"

# Chemins des fichiers utilises ou generes par les scripts.
STATE_PATH = Path("data/state/saucedemo_state.json")
RAW_PRODUCTS_PATH = Path("data/raw/products.json")
RAW_DETAILS_PATH = Path("data/raw/product_details.json")
RAW_SORTS_PATH = Path("data/raw/product_sorts.json")
STAGING_PRODUCTS_PATH = Path("data/staging/products.json")
STAGING_PRODUCTS_JSONL_PATH = Path("data/staging/products.jsonl")


# Verifie que le nombre de produits demande reste coherent.
if not 1 <= MAX_PRODUCTS <= AVAILABLE_PRODUCTS:
    raise ValueError(
        f"MAX_PRODUCTS doit être compris entre 1 "
        f"et {AVAILABLE_PRODUCTS}"
    )

# Le delai de navigation a été défini à 500 dans le diagnostic.
MIN_NAVIGATION_DELAY_MS = 500
if NAVIGATION_DELAY_MS < MIN_NAVIGATION_DELAY_MS:
    raise ValueError(
        f"NAVIGATION_DELAY_MS doit être supérieur ou égal à "
        f"{MIN_NAVIGATION_DELAY_MS} ms"
    )
