#!/usr/bin/env python3
"""Save the SQL that Cube Core compiles for each member, with the tables it reads.

Usage: collect_core_sql.py [base URL]

The script reads the cubes from /v1/meta?extended. For each measure and each
dimension of a cube it requests /v1/sql with a query of that one member.
Cube does not run the query. The response has the data source and the SQL in
the dialect of the warehouse. The script asks for an ungrouped query first,
so a pre-aggregation does not replace the tables. The script parses the SQL with sqlglot and records
the tables and the columns. Run it with `uvx --with sqlglot python`.

Output: sources/core-sql/members.json
"""

import json
import pathlib
import sys
import urllib.parse
import urllib.request

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import build_scope

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4000/cubejs-api/v1"
DIALECTS = {"snowflake": "snowflake", "postgres": "postgres", "clickhouse": "clickhouse", "bigquery": "bigquery"}


def get(path, **params):
    url = f"{BASE}/{path}"
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return {"error": json.load(error).get("error", str(error))}


def lineage(sql, dialect):
    """Tables and columns of physical tables that the SQL reads."""
    tree = sqlglot.parse_one(sql, read=dialect)
    tables, columns = set(), set()
    root = build_scope(tree)
    for scope in root.traverse():
        physical = {
            alias: source
            for alias, source in scope.sources.items()
            if isinstance(source, exp.Table)
        }
        for table in physical.values():
            tables.add(table.sql(dialect=dialect).split(" AS ")[0])
        for column in scope.columns:
            source = physical.get(column.table)
            if source is None and not column.table and len(physical) == 1 and len(scope.sources) == 1:
                source = next(iter(physical.values()))
            if source is not None:
                columns.add(f"{source.sql(dialect=dialect).split(' AS ')[0]}.{column.name}")
    return sorted(tables), sorted(columns)


def main():
    meta = get("meta?extended")
    # The warehouse type of a data source is not in the API. Read it from the model names.
    result = []
    for cube in meta["cubes"]:
        for kind, key in (("measure", "measures"), ("dimension", "dimensions")):
            for member in cube[key]:
                # An ungrouped query has the expression of the member with no aggregation,
                # and Cube does not replace the tables with a pre-aggregation.
                query = {key: [member["name"]], "limit": 1, "ungrouped": True}
                response = get("sql", query=json.dumps(query))
                mode = "ungrouped"
                if "error" in response:
                    del query["ungrouped"]
                    response = get("sql", query=json.dumps(query))
                    mode = "grouped"
                entry = {
                    "cube": cube["name"],
                    "type": cube["type"],
                    "kind": kind,
                    "member": member["name"],
                    "mode": mode,
                }
                if "error" in response:
                    entry["error"] = response["error"]
                else:
                    sql = response["sql"]
                    entry["data_source"] = sql.get("dataSource")
                    entry["sql"] = sql["sql"][0]
                    entry["uses_pre_aggregation"] = bool(sql.get("preAggregations"))
                    dialect = DIALECTS.get(guess_type(entry["data_source"]), "snowflake")
                    try:
                        entry["tables"], entry["columns"] = lineage(entry["sql"], dialect)
                    except Exception as error:  # the parser does not know each dialect feature
                        entry["parse_error"] = str(error).splitlines()[0]
                result.append(entry)
    out = ROOT / "sources/core-sql"
    out.mkdir(parents=True, exist_ok=True)
    (out / "members.json").write_text(json.dumps(result, indent=1) + "\n")
    errors = [e for e in result if "error" in e]
    parse_errors = [e for e in result if "parse_error" in e]
    print(f"{len(result)} members, {len(errors)} errors of Cube, {len(parse_errors)} errors of the parser")


def guess_type(data_source):
    return {"default": "snowflake"}.get(data_source, data_source)


if __name__ == "__main__":
    main()
