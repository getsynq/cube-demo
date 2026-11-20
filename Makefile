.PHONY: up down env logs smoke meta core-sql ossie-offline ossie-validate cloud

# Start the project: write .env and .secrets/, start Cube, wait until it is ready.
up: env
	docker compose up -d
	@until curl -sf localhost:4000/readyz >/dev/null; do sleep 1; done
	@echo "Cube is ready: http://localhost:4000"

env:
	python3 scripts/make_env.py

down:
	docker compose down

logs:
	docker compose logs --tail 100 cube

# Run one query for each feature of the model.
smoke:
	python3 scripts/smoke.py

# Save /v1/meta and /v1/meta?extended in sources/rest-meta/.
meta:
	scripts/collect_meta.sh

# Save the SQL that Cube Core compiles for each member, with its tables and columns (needs uv).
core-sql:
	uvx --quiet --with sqlglot python scripts/collect_core_sql.py

# Convert the model with the offline Apache Ossie converter (needs uv).
ossie-offline:
	scripts/collect_ossie_offline.sh

# Validate each collected Ossie document.
ossie-validate:
	scripts/validate_ossie.sh

# Save the Metadata API response and the Ossie export of Cube Cloud.
cloud:
	scripts/collect_cloud.sh
