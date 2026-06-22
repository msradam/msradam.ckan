SHELL := /bin/bash
VENV ?= .venv
BIN := $(abspath $(VENV)/bin)
PYVER := $(shell "$(BIN)/python" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)
NS := msradam
NAME := ckan
COLLPATH := $(abspath ..)/.ckan-test-tree
TREE := $(COLLPATH)/ansible_collections/$(NS)/$(NAME)

RSYNC_EXCLUDES := --exclude '.git' --exclude '.venv' --exclude 'tests/output' \
	--exclude '__pycache__' --exclude '*.pyc' --exclude 'dist'

.PHONY: help sync sanity units test integration build clean

help:
	@echo "Targets:"
	@echo "  sanity       run ansible-test sanity"
	@echo "  units        run ansible-test units"
	@echo "  test         run sanity + units"
	@echo "  integration  run the live smoke playbook (needs CKAN_URL, CKAN_API_TOKEN)"
	@echo "  build        build the collection tarball into dist/"
	@echo "  clean        remove the temp test tree and build artifacts"

sync:
	@mkdir -p "$(TREE)"
	@rsync -a --delete $(RSYNC_EXCLUDES) ./ "$(TREE)/"

sanity: sync
	cd "$(TREE)" && "$(BIN)/ansible-test" sanity --local

units: sync
	uv pip install --python "$(VENV)" -q pytest pytest-xdist pytest-mock pytest-forked
	cd "$(TREE)" && "$(BIN)/ansible-test" units --local --python $(PYVER)

test: sanity units

integration: sync
	@: $${CKAN_URL:?set CKAN_URL to your CKAN base URL}
	@: $${CKAN_API_TOKEN:?set CKAN_API_TOKEN to a CKAN API token}
	ANSIBLE_COLLECTIONS_PATH="$(COLLPATH)" "$(BIN)/ansible-playbook" \
		-i localhost, --connection local tests/smoke.yml

build:
	"$(BIN)/ansible-galaxy" collection build --force --output-path dist

clean:
	rm -rf "$(COLLPATH)" dist tests/output
