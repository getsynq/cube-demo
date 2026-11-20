#!/usr/bin/env bash
# Save what the REST API of the local Cube returns for the model.
set -euo pipefail
cd "$(dirname "$0")/.."
api="http://localhost:4000/cubejs-api/v1"
mkdir -p sources/rest-meta
curl --fail --silent --show-error "$api/meta" | python3 -m json.tool > sources/rest-meta/meta.json
# `?extended` is not in the Cube docs. It adds the SQL, the joins and the pre-aggregations.
curl --fail --silent --show-error "$api/meta?extended" | python3 -m json.tool > sources/rest-meta/meta-extended.json
wc -c sources/rest-meta/*.json
