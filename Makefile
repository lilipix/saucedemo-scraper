PYTHON := .venv/bin/python

.PHONY: login products details sorts scrape validate transform all

login:
	. ./.env && $(PYTHON) src/login.py

products:
	$(PYTHON) src/scrape_products.py

details:
	$(PYTHON) src/scrape_details.py

sorts:
	$(PYTHON) src/scrape_sorts.py

scrape: products details sorts

transform:
	$(PYTHON) src/transform_products.py

validate:
	$(PYTHON) src/validate_products.py

all: login scrape transform validate