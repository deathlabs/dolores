# ---------------------------------------------------------
# Misc.
# ---------------------------------------------------------

# Force bash so indirect variable expansion ($${!var}) works.
SHELL := /bin/bash

# Set the default goal.
.DEFAULT_GOAL := redeploy-zarf-package

# Tell Docker to build images in parallel.
COMPOSE_BAKE := true

# Set the Docker Compose profile to "all" if an argument is not provided.
DOCKER_COMPOSE_PROFILE ?= all

COMPONENTS ?= backend inference tools database

# Per-component image names.
BACKEND_IMAGE ?= dolores/backend:latest
INFERENCE_IMAGE ?= dolores/inference:latest
TOOLS_IMAGE ?= dolores/tools:latest
DATABASE_IMAGE ?= dolores/database:latest

# Per-component SBOM/VEX file names.
BACKEND_SBOM ?= dolores-backend-sbom.json
INFERENCE_SBOM ?= dolores-inference-sbom.json
TOOLS_SBOM ?= dolores-tools-sbom.json
DATABASE_SBOM ?= dolores-database-sbom.json

BACKEND_ADVISORIES ?= backend/vex.yaml
INFERENCE_ADVISORIES ?= inference/vex.yaml
TOOLS_ADVISORIES ?= tools/vex.yaml
DATABASE_ADVISORIES ?= database/vex.yaml

BACKEND_VEX ?= backend/vex.json
INFERENCE_VEX ?= inference/vex.json
TOOLS_VEX ?= tools/vex.json
DATABASE_VEX ?= database/vex.json

VEX_AUTHOR ?= Victor Fernandez III
VEX_ID_BASE ?= dolores

# Export per-component variables so bash's indirect expansion ($${!var})
# can resolve them inside recipe shell loops (Make variables aren't
# shell environment variables by default).
export BACKEND_IMAGE INFERENCE_IMAGE TOOLS_IMAGE DATABASE_IMAGE
export BACKEND_SBOM INFERENCE_SBOM TOOLS_SBOM DATABASE_SBOM
export BACKEND_ADVISORIES INFERENCE_ADVISORIES TOOLS_ADVISORIES DATABASE_ADVISORIES
export BACKEND_VEX INFERENCE_VEX TOOLS_VEX DATABASE_VEX

# Security scanner configurations.
SEMGREP_CONFIG ?= auto
GRYPE_FAILURE_THRESHOLD ?= medium

# Helpers to look up the image/sbom/advisories/vex path for a given component.
component_image = $($(shell echo $(1) | tr a-z A-Z)_IMAGE)
component_sbom = $($(shell echo $(1) | tr a-z A-Z)_SBOM)
component_advisories = $($(shell echo $(1) | tr a-z A-Z)_ADVISORIES)
component_vex = $($(shell echo $(1) | tr a-z A-Z)_VEX)

PYTHON_COMPONENTS ?= backend inference tools

# ---------------------------------------------------------
# Update uv.lock for each Python component.
# ---------------------------------------------------------

.PHONY: lock
.SILENT: lock

lock:
	for component in $(PYTHON_COMPONENTS); do \
		if [ -f "$$component/pyproject.toml" ]; then \
			echo "==> Locking $$component"; \
			cd $$component && uv lock && cd ..; \
		fi; \
	done

# ---------------------------------------------------------
# Reset Django migrations (backend only; Django-specific).
# ---------------------------------------------------------

.PHONY: migrations
.SILENT: migrations

migrations: 
	find backend \
		-mindepth 3 -maxdepth 3 \
		-path "*/migrations/*.py" \
		! -name "__init__.py" \
		-type f -delete
	find backend \
		-mindepth 3 -maxdepth 3 \
		-path "*/migrations/__pycache__" \
		-type d -exec rm -rf {} +
	cd backend && SECRET_KEY=dolores uv run python manage.py makemigrations

# ---------------------------------------------------------
# Check each Python component for bugs.
# ---------------------------------------------------------

.PHONY: check
.SILENT: check

check:
	for component in $(PYTHON_COMPONENTS); do \
		if [ -d "$$component" ]; then \
			echo "==> Checking $$component"; \
			ruff check --fix --exclude migrations $$component; \
		fi; \
	done

# ---------------------------------------------------------
# Format each Python component for consistency.
# ---------------------------------------------------------

.PHONY: format
.SILENT: format

format:
	for component in $(PYTHON_COMPONENTS); do \
		if [ -d "$$component" ]; then \
			echo "==> Formatting $$component"; \
			ruff format --exclude migrations $$component; \
		fi; \
	done

# ---------------------------------------------------------
# Check each component's source code for vulnerabilities.
# ---------------------------------------------------------

.PHONY: sast
.SILENT: sast

sast:
	for component in $(COMPONENTS); do \
		if [ -d "$$component" ]; then \
			echo "==> Running SAST on $$component"; \
			semgrep scan --config $(SEMGREP_CONFIG) $$component; \
		fi; \
	done

# ---------------------------------------------------------
# Build the container images.
# ---------------------------------------------------------

.PHONY: build
.SILENT: build

build: lock migrations check format 
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) build

# ---------------------------------------------------------
# Generate VEX statements for each component.
# ---------------------------------------------------------

.PHONY: vex
.SILENT: vex

define VEX_FILTER
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": env(VEX_ID),
  "author": "$(VEX_AUTHOR)",
  "timestamp": env(VEX_TIMESTAMP),
  "version": 1,
  "statements": [
    .advisories[] | {
      "vulnerability": { "name": .vulnerability },
      "products": [ .products[] | { "@id": . } ],
      "status": .status,
      "justification": .justification,
      "impact_statement": .impact_statement
    }
  ]
}
endef
export VEX_FILTER

vex: 
	for component in $(COMPONENTS); do \
		advisories=$$(echo $$component | tr a-z A-Z)_ADVISORIES; \
		vex_out=$$(echo $$component | tr a-z A-Z)_VEX; \
		advisories_path=$${!advisories}; \
		vex_path=$${!vex_out}; \
		if [ -f "$$advisories_path" ]; then \
			echo "==> Generating VEX for $$component"; \
			VEX_ID="$(VEX_ID_BASE)-$$component-$$(date +%s)" \
			VEX_TIMESTAMP="$$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
			yq -o=json "$$VEX_FILTER" $$advisories_path > $$vex_path; \
		fi; \
	done

# ---------------------------------------------------------
# Generate SBOMs for each component's container image.
# ---------------------------------------------------------

.PHONY: sbom
.SILENT: sbom

sbom: build
	for component in $(COMPONENTS); do \
		image=$$(echo $$component | tr a-z A-Z)_IMAGE; \
		sbom_out=$$(echo $$component | tr a-z A-Z)_SBOM; \
		image_ref=$${!image}; \
		sbom_path=$${!sbom_out}; \
		echo "==> Generating SBOM for $$component ($$image_ref)"; \
		syft $$image_ref -o cyclonedx-json=$$sbom_path; \
	done

# ---------------------------------------------------------
# Scan each container image's dependencies for CVEs.
# ---------------------------------------------------------

.PHONY: dependency-scan
.SILENT: dependency-scan

dependency-scan: sbom vex
	grype db update
	for component in $(COMPONENTS); do \
		sbom_out=$$(echo $$component | tr a-z A-Z)_SBOM; \
		vex_out=$$(echo $$component | tr a-z A-Z)_VEX; \
		sbom_path=$${!sbom_out}; \
		vex_path=$${!vex_out}; \
		echo "==> Scanning dependencies for $$component"; \
		if [ -f "$$vex_path" ]; then \
			grype sbom:$$sbom_path --vex $$vex_path --fail-on $(GRYPE_FAILURE_THRESHOLD); \
		else \
			grype sbom:$$sbom_path --fail-on $(GRYPE_FAILURE_THRESHOLD); \
		fi; \
	done

# ---------------------------------------------------------
# Start the containers.
# ---------------------------------------------------------

.PHONY: start
.SILENT: start

start-containers: dependency-scan
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) up -d

# ---------------------------------------------------------
# Stop the containers.
# ---------------------------------------------------------

.PHONY: stop
.SILENT: stop

stop-containers: 
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) down

# ---------------------------------------------------------
# Check the status of the containers.
# ---------------------------------------------------------

.PHONY: status
.SILENT: status

status:
	docker compose --profile $(DOCKER_COMPOSE_PROFILE) ps --format "table {{.Name}}\t{{.Ports}}\t{{.Status}}"

# ---------------------------------------------------------
# Deploy the Zarf package.
# ---------------------------------------------------------

.PHONY: deploy
.SILENT: deploy

deploy: dependency-scan
	uds zarf package create --confirm && \
	uds zarf package deploy zarf-package-dolores-amd64-0.1.0.tar.zst --confirm

# ---------------------------------------------------------
# Remove the Zarf package.
# ---------------------------------------------------------

.PHONY: remove
.SILENT: remove

remove-zarf-package:
	uds zarf package remove dolores --confirm || true &&\
	uds zarf tools kubectl delete namespace dolores --ignore-not-found 
	# kubectl patch packages.uds.dev dolores -n dolores --type=merge -p '{"metadata":{"finalizers":[]}}'

# ---------------------------------------------------------
# Redeploy the Zarf package.
# ---------------------------------------------------------

.PHONY: redeploy
.SILENT: redeploy

redeploy-zarf-package: remove deploy

# ---------------------------------------------------------
# Update the UDS package.
# ---------------------------------------------------------

.PHONY: update-uds-package
.SILENT: update-uds-package

update-uds-package: 
	uds zarf tools kubectl apply -f uds-package.yaml
