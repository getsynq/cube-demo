#!/usr/bin/env bash
# Validate each collected Ossie document with `synqctl ossie validate`.
# synqctl is an internal tool. Set SYNQCTL if it is not on the PATH.
set -uo pipefail
cd "$(dirname "$0")/.."
synqctl="${SYNQCTL:-synqctl}"
status=0
for document in sources/ossie-*/*.ossie.yaml; do
  [ -e "$document" ] || { echo "no Ossie document in sources/"; exit 1; }
  report="${document%.ossie.yaml}.validation.txt"
  if "$synqctl" ossie validate "$document" > "$report" 2>&1; then
    echo "valid   $document"
  else
    echo "invalid $document (see $report)"
    status=1
  fi
done
exit $status
