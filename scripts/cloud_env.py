#!/usr/bin/env python3
"""Set the environment variables of the Cube Cloud deployment from the local .env.

Usage: cloud_env.py <deployment id>

Necessary environment variables: CUBE_API_URL and CUBE_API_TOKEN.
Run `make env` first. The script sends the warehouse credentials to Cube Cloud.
"""

import json
import os
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Cube Cloud has its own API secret, and it has no file for the private key.
SKIP = {"CUBEJS_API_SECRET", "CUBEJS_DB_SNOWFLAKE_PRIVATE_KEY_PATH"}


def main():
    deployment = sys.argv[1]
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        name, value = line.split("=", 1)
        if name not in SKIP:
            env[name] = value
    env["CUBEJS_DB_SNOWFLAKE_PRIVATE_KEY"] = (ROOT / ".secrets/snowflake.p8").read_text()
    # The same values as in docker-compose.yml.
    env["CUBEJS_DATASOURCES"] = "default,postgres,clickhouse,bigquery"
    env["CUBEJS_TESSERACT_SQL_PLANNER"] = "true"

    body = {"env_variables": [{"name": k, "value": v} for k, v in env.items()]}
    request = urllib.request.Request(
        f"{os.environ['CUBE_API_URL']}/api/v1/deployments/{deployment}/env-vars",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={
            "Authorization": f"Bearer {os.environ['CUBE_API_TOKEN']}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request) as response:
        names = [item["name"] for item in json.load(response)["items"]]
    print(f"deployment {deployment} has {len(names)} variables: {', '.join(sorted(names))}")


if __name__ == "__main__":
    main()
