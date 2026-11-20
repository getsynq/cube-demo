# AGENTS.md - cube-demo

This repository holds a sample Cube project. The project uses each Cube data model feature at least one time. We use it to compare the data that each Cube metadata source returns: the REST API `/v1/meta`, the Cube Cloud Metadata API, the Apache Ossie export, the offline Ossie converter and the files in git.

## This repository will be public

Apply these rules to each file, commit message, branch name and pull request.

- Do not write a customer name, a workspace name or an internal codename.
- Do not copy a file, a name or a SQL statement from a customer project. Write each example again on the test tables.
- Do not link to an internal issue, a Slack message or an internal document.
- Do not commit a credential, an account identifier, a hostname or a cloud project identifier. These values are only in `.env` and `.secrets/`, and git ignores the two paths.
- If a model file needs such a value, read it from an environment variable.
- Before each commit, run `git status` and make sure that `.env` and `.secrets/` are not staged.

A public commit is permanent. A force push does not remove it from public archives.

## Layout

| Path | Content |
|---|---|
| `model/cubes/` | The cubes, one topic for each file |
| `model/views/` | The views |
| `model/macros/` | Shared Jinja macro files that the cubes import |
| `model/globals.py` | Python functions and variables for the Jinja templates |
| `cube.py` | The Python configuration of Cube |
| `scripts/make_env.py` | Writes `.env` and `.secrets/` from the private test warehouse configuration |
| `scripts/smoke.py` | Runs the queries in `tests/queries.json` against the local Cube |
| `scripts/render_jinja.py` | Renders the Jinja templates to plain YAML for the offline Ossie converter |
| `scripts/collect_core_sql.py` | Saves the compiled SQL and the lineage of each member from `/v1/sql` |
| `scripts/cloud_env.py` | Sets the environment variables of the Cube Cloud deployment from `.env` |
| `scripts/collect_*.sh` | Save what each metadata source returns into `sources/` |
| `sources/` | The saved response of each metadata source, one directory for each source |
| `docker-compose.yml` | Cube Core in development mode |

## Run the project

1. Connect to the private network. The Postgres and ClickHouse data sources are in a private network.
2. Run `make up`. Set `DWHTESTING_DIR` if the test warehouse configuration is not in the default location.
3. Open `http://localhost:4000` for the Playground.

Cube runs in development mode, so the REST API needs no token. Cube reads the model files again on each request, so a restart is not necessary after a model change. Restart the container after a change of `cube.py`, `.env` or `docker-compose.yml`.

## Data sources

| Name | Warehouse | Reachable from Cube Cloud |
|---|---|---|
| `default` | Snowflake | Yes |
| `bigquery` | BigQuery | Yes |
| `postgres` | PostgreSQL | No, private network |
| `clickhouse` | ClickHouse | No, private network |

The tables are test fixtures that a seed creates. This repository does not own the seed.

- Do not change the warehouse tables from this repository. If the model needs a derived column, calculate it in the `sql` of a cube.
- A reseed adds rows to the fact tables. Do not write a check that expects an exact row count of a fact table.
- Write the SQL of a cube in the dialect of its data source.

## Model rules

- Each Cube feature in the feature matrix of `README.md` must have at least one example in the model. If you remove an example, add the feature in a different file.
- When you add a feature, add a row to the feature matrix in the same change.
- Keep some cubes in plain YAML and some in YAML with Jinja. The offline Ossie converter skips a file that has Jinja, so the two groups show different results.
- Put a shared macro in `model/macros/` and import it. Do not copy a macro into a cube file.
- Put a short comment at the top of each model file that names the features that the file shows.
- A file that uses `extends` stops the Ossie export of the full model. Keep each `extends` example in a file with the `extends_` prefix, so a script can exclude it.
- Do not keep a file that is not UTF-8 text in `model/`. The offline Ossie converter stops on such a file. A Python script that imports `model/globals.py` must set `sys.dont_write_bytecode`.
- In a `sql` property, refer to a column as `{CUBE}.COLUMN` and to a member as `{member}`. The converters can then qualify the names.
- Use upper case for Snowflake identifiers.

## Check a change

1. Request `http://localhost:4000/cubejs-api/v1/meta`. Status 200 shows that the model compiles. Status 500 has the compile errors in the `error` field.
2. For each new or changed member, add a query that uses it to `tests/queries.json`.
3. Run `make smoke`. To run a part of the queries, run `scripts/smoke.py <text in the query name>`.
4. If a query fails, read the generated SQL in `make logs`.
5. Run `make meta` and commit the changed files in `sources/rest-meta/`.
6. Run `make ossie-offline` and commit the changed files in `sources/ossie-offline/`. Update the tables in `README.md` if a result changes.

A model that compiles can still generate SQL that the warehouse rejects. Do not report a feature as done before its query returns rows.

## Writing

- Write documents in this repository in simple technical English: short sentences, one instruction for each sentence, the condition first.
- Use the same term for the same thing in each document.
- Keep technical names (functions, flags, paths, product names) as they are.

## Git

- Work on a branch and open a pull request. Do not push to `main`.
- Use the title format `<area>: <what changed>`, for example `model: Add calendar cube`.
- Push with `git push --set-upstream --force-with-lease origin <branch>`.
