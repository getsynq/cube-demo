#!/usr/bin/env bash
# Convert the model with the offline Apache Ossie converter for Cube.
# The converter needs no Cube deployment. It reads the files in model/ as they are,
# so it does not render Jinja.
#
# Output in sources/ossie-offline/:
#   <variant>.ossie.yaml   the Ossie document, absent if the conversion failed
#   <variant>.issues.txt   the issues and errors that the converter reported
set -uo pipefail
cd "$(dirname "$0")/.."

# Pinned commit of https://github.com/apache/ossie-converters
converter_ref="${OSSIE_CONVERTERS_REF:-a8c26e8cd60dc9f5e19e354f3d4ca22f62d83afb}"
converter="git+https://github.com/apache/ossie-converters@${converter_ref}#subdirectory=cube"
out="sources/ossie-offline"
mkdir -p "$out"

convert() {
  local variant="$1"
  shift
  rm -f "$out/$variant.ossie.yaml"
  if uvx --quiet --from "$converter" ossie-cube import "$@" -o "$out/$variant.ossie.yaml" \
    > "$out/$variant.issues.txt" 2>&1; then
    echo "ok     $variant"
  else
    echo "failed $variant (see $out/$variant.issues.txt)"
  fi
}

# 1. The full model. A cube with `extends` stops the conversion.
convert full-model -i model/

# 2. The model without the `extends_*` files.
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir "$work/model"
(cd model && tar cf - --exclude 'extends_*' --exclude '__pycache__' .) | (cd "$work/model" && tar xf -)
convert no-extends -i "$work/model"

# 3. One document for each view: only the public members, with the names of the view.
for view in orders_overview order_items_detail customer_360; do
  convert "view-$view" -i "$work/model" --view "$view" --project
done
