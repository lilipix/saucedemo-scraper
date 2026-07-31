PYTHON := .venv/bin/python

.PHONY: login check-session products details sorts scrape validate transform all

login:
	@echo "== Connexion =="
	. ./.env && $(PYTHON) src/login.py

check-session:
	@echo "== Verification de session =="
	$(PYTHON) src/check_session.py

products:
	@echo "== Scraping inventaire =="
	$(PYTHON) src/scrape_products.py

details:
	@echo "== Scraping details =="
	$(PYTHON) src/scrape_details.py

sorts:
	@echo "== Scraping tris =="
	$(PYTHON) src/scrape_sorts.py

scrape: products details sorts

transform:
	@echo "== Transformation =="
	$(PYTHON) src/transform_products.py

validate:
	@echo "== Validation =="
	$(PYTHON) src/validate_products.py

all: login check-session scrape transform validate
