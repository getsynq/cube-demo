#!/usr/bin/env bash
# Save what Cube Cloud returns for the deployed model: the Metadata API and the Ossie export.
#
# Necessary environment variables:
#   CUBE_API_URL     tenant host of the Platform API, no slash at the end
#   CUBE_API_TOKEN   Platform API key. The Ossie export needs SchemaRead and SqlRunnerRead.
#   DEPLOYMENT_ID    the deployment
#   CUBE_DATA_URL    base URL of the deployment data API, for example https://<host>/cubejs-api
#   CUBE_META_TOKEN  token for the Metadata API with the scopes meta and meta-private
#
# The Ossie export is in preview. Cube support must turn it on for the account.
# This script was written from the Cube docs. It was not run against a Cube Cloud account.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${CUBE_API_URL:?}" "${CUBE_API_TOKEN:?}" "${DEPLOYMENT_ID:?}" "${CUBE_DATA_URL:?}" "${CUBE_META_TOKEN:?}"

meta_out="sources/cloud-metadata-api"
ossie_out="sources/ossie-cloud"
mkdir -p "$meta_out" "$ossie_out"

# --- Metadata API ---
meta_auth="Authorization: Bearer $CUBE_META_TOKEN"
curl --fail --silent --show-error -H "$meta_auth" "$CUBE_DATA_URL/v1/data-sources" \
  | python3 -m json.tool > "$meta_out/data-sources.json"
curl --fail --silent --show-error -H "$meta_auth" \
  "$CUBE_DATA_URL/v1/entities?limit=500&include_private=true" \
  | python3 -m json.tool > "$meta_out/entities.json"
curl --fail --silent --show-error -H "$meta_auth" -H 'Content-Type: application/json' \
  -X POST -d '{"include_private": true}' "$CUBE_DATA_URL/v1/entities/all" \
  | python3 -m json.tool > "$meta_out/entities-all.json"

# --- Ossie export ---
api="$CUBE_API_URL/api/v1/deployments/$DEPLOYMENT_ID/ossie-conversions"
auth="Authorization: Bearer $CUBE_API_TOKEN"

export_ossie() {
  local variant="$1" body="$2" code id status
  for _ in $(seq 1 30); do
    code=$(curl --silent --show-error -o "$ossie_out/$variant.conversion.json" -w '%{http_code}' \
      -X POST -H "$auth" -H 'Content-Type: application/json' -d "$body" "$api")
    [ "$code" = 409 ] || break
    sleep 10
  done
  if [ "$code" != 202 ]; then
    echo "failed $variant: HTTP $code (see $ossie_out/$variant.conversion.json)"
    return
  fi
  id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["conversionId"])' \
    "$ossie_out/$variant.conversion.json")
  while :; do
    status=$(curl --fail --silent --show-error -H "$auth" "$api/$id" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')
    [ "$status" = QUEUED ] || [ "$status" = RUNNING ] || break
    sleep 5
  done
  for part in result files; do
    for _ in $(seq 1 15); do
      code=$(curl --silent --show-error -o "$ossie_out/$variant.$part.json" -w '%{http_code}' \
        -H "$auth" "$api/$id/$part")
      [ "$code" = 409 ] || break
      sleep 2
    done
  done
  python3 - "$ossie_out/$variant" <<'PY'
import json, sys
prefix = sys.argv[1]
try:
    files = json.load(open(prefix + ".files.json"))
    content = files["items"][0]["content"]
except (OSError, KeyError, IndexError, ValueError):
    print(f"failed {prefix}: no file in the result")
else:
    open(prefix + ".ossie.yaml", "w").write(content + "\n")
    print(f"ok     {prefix}")
PY
}

export_ossie full-model '{"direction": "export"}'
for view in orders_overview order_items_detail customer_360; do
  export_ossie "view-$view" "{\"direction\": \"export\", \"view\": \"$view\"}"
done
