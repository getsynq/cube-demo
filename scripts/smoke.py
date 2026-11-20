#!/usr/bin/env python3
"""Run one query for each feature of the sample model against the local Cube.

Usage: scripts/smoke.py [name-filter]
The queries are in tests/queries.json. A query passes if Cube returns rows.
"""

import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = "http://localhost:4000/cubejs-api/v1"


def load(query):
    url = f"{API}/load?" + urllib.parse.urlencode({"query": json.dumps(query)})
    for _ in range(120):
        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                body = json.load(response)
        except urllib.error.HTTPError as error:
            body = json.load(error)
        if body.get("error") != "Continue wait":
            return body
        time.sleep(1)
    return {"error": "timeout"}


def main():
    name_filter = sys.argv[1] if len(sys.argv) > 1 else ""
    cases = json.loads((ROOT / "tests" / "queries.json").read_text())
    failed = 0
    for case in cases:
        if name_filter not in case["name"]:
            continue
        body = load(case["query"])
        rows = body.get("data")
        if body.get("error") or not rows:
            failed += 1
            error = str(body.get("error", "no rows")).strip().splitlines()
            print(f"FAIL {case['name']}: {' | '.join(error[:3])[:400]}")
        else:
            print(f"ok   {case['name']}: {len(rows)} rows, first {json.dumps(rows[0])[:160]}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
