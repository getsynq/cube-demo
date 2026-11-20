#!/usr/bin/env python3
"""Write .env and .secrets/ for the local Cube run.

The credentials are not in this repository. The single source of truth is
dev-infra/dwhtesting/integrations/*.json in the getsynq/cloud repository.
Set DWHTESTING_DIR if the cloud repository is not at ~/getsynq/cloud.
"""

import base64
import json
import os
import pathlib
import secrets
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DWHTESTING = pathlib.Path(
    os.environ.get("DWHTESTING_DIR", "~/getsynq/cloud/dev-infra/dwhtesting")
).expanduser()


def integration(name):
    path = DWHTESTING / "integrations" / f"{name}.json"
    if not path.exists():
        sys.exit(f"missing {path}: set DWHTESTING_DIR to dev-infra/dwhtesting")
    config = json.loads(path.read_text())["configuration"]
    return next(iter(config.values()))


def main():
    secrets_dir = ROOT / ".secrets"
    secrets_dir.mkdir(exist_ok=True)
    secrets_dir.chmod(0o700)

    snowflake = integration("snowflake")
    postgres = integration("postgresql")
    clickhouse = integration("clickhouse")
    bigquery = integration("bigquery")

    key_path = secrets_dir / "snowflake.p8"
    key_path.write_text(snowflake["keyPair"]["privateKeySecret"])
    key_path.chmod(0o600)

    bq_key = bigquery["serviceAccountKey"]
    bq_path = secrets_dir / "bigquery.json"
    bq_path.write_text(bq_key)
    bq_path.chmod(0o600)

    # Keep the API secret between runs, so a saved token stays valid.
    env_path = ROOT / ".env"
    api_secret = secrets.token_hex(32)
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("CUBEJS_API_SECRET="):
                api_secret = line.split("=", 1)[1]

    env = {
        "CUBEJS_API_SECRET": api_secret,
        # default data source: Snowflake DWH_TESTING
        "CUBEJS_DB_TYPE": "snowflake",
        "CUBEJS_DB_SNOWFLAKE_ACCOUNT": snowflake["account"],
        "CUBEJS_DB_SNOWFLAKE_WAREHOUSE": snowflake["warehouse"],
        "CUBEJS_DB_SNOWFLAKE_ROLE": snowflake["role"],
        "CUBEJS_DB_NAME": "DWH_TESTING",
        "CUBEJS_DB_USER": snowflake["user"],
        "CUBEJS_DB_SNOWFLAKE_AUTHENTICATOR": "SNOWFLAKE_JWT",
        "CUBEJS_DB_SNOWFLAKE_PRIVATE_KEY_PATH": "/cube/secrets/snowflake.p8",
        # postgres data source (private network)
        "CUBEJS_DS_POSTGRES_DB_TYPE": "postgres",
        "CUBEJS_DS_POSTGRES_DB_HOST": postgres["host"],
        "CUBEJS_DS_POSTGRES_DB_PORT": str(postgres["port"]),
        "CUBEJS_DS_POSTGRES_DB_NAME": postgres["database"],
        "CUBEJS_DS_POSTGRES_DB_USER": postgres["user"],
        "CUBEJS_DS_POSTGRES_DB_PASS": postgres["password"],
        # clickhouse data source (private network, HTTP port)
        "CUBEJS_DS_CLICKHOUSE_DB_TYPE": "clickhouse",
        "CUBEJS_DS_CLICKHOUSE_DB_HOST": clickhouse["host"],
        "CUBEJS_DS_CLICKHOUSE_DB_PORT": "8123",
        "CUBEJS_DS_CLICKHOUSE_DB_NAME": "synq_test",
        "CUBEJS_DS_CLICKHOUSE_DB_USER": clickhouse["username"],
        "CUBEJS_DS_CLICKHOUSE_DB_PASS": clickhouse["password"],
        # bigquery data source
        "CUBEJS_DS_BIGQUERY_DB_TYPE": "bigquery",
        "CUBEJS_DS_BIGQUERY_DB_BQ_PROJECT_ID": bigquery["projectId"],
        "CUBEJS_DS_BIGQUERY_DB_BQ_LOCATION": bigquery["region"],
        "CUBEJS_DS_BIGQUERY_DB_BQ_CREDENTIALS": base64.b64encode(
            bq_key.encode()
        ).decode(),
    }
    env_path.write_text("".join(f"{k}={v}\n" for k, v in env.items()))
    env_path.chmod(0o600)
    print(f"wrote {env_path.relative_to(ROOT)} and .secrets/ from {DWHTESTING}")


if __name__ == "__main__":
    main()
