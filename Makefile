current_dir := $(shell pwd)
ENV=$(current_dir)/env

all: help

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Utility target for checking required parameters
guard-%:
	@if [ "$($*)" = '' ]; then \
     echo "Missing required $* variable."; \
     exit 1; \
   fi;

.PHONY: clean
clean:  ## Clean out some superficial crust
	find . -name "*.pyc" -exec /bin/rm -rf {} \;

.PHONY: clean-all
clean-all: clean  ## Burn everything to the ground
	rm -rf env
	rm -rf build
	rm -rf deploy-env
	rm -rf lambda.zip
	rm -rf docs/_build
	rm -f .coverage

env: clean
	test -d $(ENV) || virtualenv $(ENV)

.PHONY: install
install: env  ## Install project dependencies
	$(ENV)/bin/pip install -r requirements.txt
	$(ENV)/bin/pip install -r requirements-dev.txt

.PHONY: checkstyle
checkstyle:  ## Run the linters locally
	$(ENV)/bin/flake8 --max-complexity 10 server.py
	$(ENV)/bin/flake8 --max-complexity 10 auth_backend
	$(ENV)/bin/flake8 --max-complexity 10 tests

.PHONY: unit-test
unit-test:  ## Run the unit-tests locally
	$(ENV)/bin/nosetests \
		-v \
		--with-coverage \
		--cover-package=auth_backend \
		tests

.PHONY: test
test: checkstyle unit-test  ## Run all the acceptance tests locally
	@echo "Tests look good!"

.PHONY: server
server:  ## Run the local development server
	$(ENV)/bin/python server.py 127.0.0.1 8080

# e.g. PART=major make release
# e.g. PART=minor make release
# e.g. PART=patch make release
.PHONY: release
release: guard-PART  ## Cut a new release! (e.g. PART=patch make release)
	$(ENV)/bin/bumpversion $(PART)
	@echo "Now manually run: git push && git push --tags"

.PHONY: lambda
lambda: clean-all  ## Prepare the lambda.zip file for AWS Lambda
	mkdir build
	pip install -r requirements.txt -t build
	cp -R auth_backend build/
	find build -type d -exec chmod ugo+rx {} \;
	find build -type f -exec chmod ugo+r {} \;
	find build -name "*.pyc" -exec /bin/rm -rf {} \;
	cd build; zip -Xr ../lambda.zip *

.PHONY: ngrok
ngrok:
	ngrok http 127.0.0.1:8080
