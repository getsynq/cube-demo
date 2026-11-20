#!/usr/bin/env bash
# Save what Cube Cloud returns for the deployed model: the Metadata API and the Ossie export.
#
# Necessary values, in the environment or in .secrets/cloud.env:
#   CUBE_API_URL     tenant host of the Platform API, no slash at the end
#   CUBE_API_TOKEN   Platform API key of an administrator
#   DEPLOYMENT_ID    optional. The default is the first deployment of the account.
#
# The script reads the environment and the data API URL from the Platform API.
# It creates a token for the Metadata API with the scopes meta and meta-private.
# The Ossie export is in preview. Cube support must turn it on for the account.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .secrets/cloud.env ]; then
  set -a
  . .secrets/cloud.env
  set +a
fi
: "${CUBE_API_URL:?}" "${CUBE_API_TOKEN:?}"

auth="Authorization: Bearer $CUBE_API_TOKEN"
platform() { curl --fail --silent --show-error -H "$auth" -H 'Content-Type: application/json' "$@"; }
field() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

DEPLOYMENT_ID="${DEPLOYMENT_ID:-$(platform "$CUBE_API_URL/api/v1/deployments" | field 'd["items"][0]["id"]')}"
environments="$(platform "$CUBE_API_URL/api/v1/deployments/$DEPLOYMENT_ID/environments")"
environment_id="$(echo "$environments" | field '[e for e in d["items"] if e["type"]=="production"][0]["id"]')"
data_url="$(echo "$environments" | field '[c["url"] for e in d["items"] if e["type"]=="production" for c in e["api_credentials"] if c["type"]=="rest"][0]')"
meta_token="$(platform -X POST -d '{"security_context": {}, "scopes": ["meta-private"]}' \
  "$CUBE_API_URL/api/v1/deployments/$DEPLOYMENT_ID/environments/$environment_id/tokens-for-meta-sync" \
  | field 'd.get("data", d)["token"]')"

meta_out="sources/cloud-metadata-api"
ossie_out="sources/ossie-cloud"
mkdir -p "$meta_out" "$ossie_out"

# --- Metadata API ---
# $data_url ends with /cubejs-api/v1.
metadata() {
  local file="$1" code
  shift
  code=$(curl --silent --show-error -o "$meta_out/$file.raw" -w '%{http_code}' \
    -H "Authorization: Bearer $meta_token" -H 'Content-Type: application/json' "$@")
  python3 -m json.tool "$meta_out/$file.raw" > "$meta_out/$file" 2>/dev/null || cp "$meta_out/$file.raw" "$meta_out/$file"
  rm "$meta_out/$file.raw"
  echo "HTTP $code $meta_out/$file"
}
metadata data-sources.json "$data_url/data-sources"
# A cloud project identifier must not be in this repository.
python3 - "$meta_out/data-sources.json" <<'PY'
import json, sys
path = sys.argv[1]
document = json.load(open(path))
for source in document["data"]["data_sources"]:
    if "project_id" in source.get("properties", {}):
        source["properties"]["project_id"] = "<redacted>"
json.dump(document, open(path, "w"), indent=4)
PY
metadata entities.json "$data_url/entities?limit=500&include_private=true"
metadata entities-all.json -X POST -d '{"include_private": true}' "$data_url/entities/all"
metadata entities-all-public.json -X POST -d '{}' "$data_url/entities/all"
metadata model-export.json -X POST -d '{}' "$data_url/model-export"
# The REST API of Cube Core, on the same deployment, with the same token.
metadata meta.json "$data_url/meta"
metadata meta-extended.json "$data_url/meta?extended"

# --- Ossie export ---
api="$CUBE_API_URL/api/v1/deployments/$DEPLOYMENT_ID/ossie-conversions"

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
