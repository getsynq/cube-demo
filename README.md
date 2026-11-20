# cube-demo

A sample [Cube](https://cube.dev) project that uses each feature of the Cube data model at least one time.
We use it to compare the data that each Cube metadata source returns for the same model.

The project runs on Cube Core v1.8.30 in Docker, on test tables in four warehouses:
Snowflake (the default data source), PostgreSQL, ClickHouse and BigQuery.

## Run the project

The warehouses are private test fixtures. You need access to their configuration to run the project.

1. Connect to the private network of the PostgreSQL and ClickHouse fixtures.
2. Run `make up`. This command writes `.env` and `.secrets/`, starts Cube and waits until Cube is ready.
3. Open `http://localhost:4000` for the Playground.
4. Run `make smoke`. This command runs one query for each feature and shows the first row of each result.

| Command | Result |
|---|---|
| `make up` | Starts Cube Core in development mode |
| `make smoke` | Runs the queries in `tests/queries.json` |
| `make meta` | Saves `/v1/meta` and `/v1/meta?extended` in `sources/rest-meta/` |
| `make ossie-offline` | Converts the model with the offline Apache Ossie converter into `sources/ossie-offline/` |
| `make ossie-validate` | Validates each Ossie document in `sources/` |
| `make cloud` | Saves the Metadata API response and the Ossie export of a Cube Cloud deployment |
| `make down` | Stops Cube |

## Model

| File | Syntax | Data source | Content |
|---|---|---|---|
| `model/cubes/orders.yml` | YAML with Jinja | Snowflake | The fact cube: all measure types, multi-stage measures, pre-aggregations, access policy |
| `model/cubes/events.yml` | YAML with Jinja | Snowflake | A cube on a SQL query with `FILTER_PARAMS` and `FILTER_GROUP` |
| `model/cubes/customers.yml` | YAML | Snowflake | A cube on a SQL query, `geo` and `sub_query` dimensions |
| `model/cubes/products.yml` | YAML | Snowflake | A `one_to_one` join to a hidden cube |
| `model/cubes/order_items.yml` | YAML | Snowflake | A composite primary key, two `many_to_one` joins |
| `model/cubes/calendar.yml` | YAML | Snowflake | A calendar cube with a fiscal year |
| `model/cubes/extends_products.yml` | YAML | Snowflake | A cube that extends a cube |
| `model/cubes/other_sources.yml` | YAML | PostgreSQL, ClickHouse, BigQuery | One cube for each other data source |
| `model/cubes/pg_products.js` | JavaScript | PostgreSQL | A cube and a view in JavaScript |
| `model/cubes/python_generated.yml` | YAML with Jinja | PostgreSQL | Cubes that a Python function defines |
| `model/views/orders_overview.yml` | YAML | | Includes, excludes, prefix, alias, folders, access policy |
| `model/views/order_items_detail.yml` | YAML | | A measure and a dimension of the view, `default_filters` |
| `model/views/customer_360.yml` | YAML with Jinja | | Includes from a loop, a hidden view |
| `model/views/extends_orders_overview.yml` | YAML | | A view that extends a view |
| `model/macros/*.jinja` | Jinja | | Shared macros that the Jinja cubes import |
| `model/globals.py` | Python | | Functions, variables and a filter for the templates |
| `cube.py` | Python | | `context_to_app_id`, `context_to_groups`, `query_rewrite`, `scheduled_refresh_contexts` |

## Feature matrix

The two REST columns show what Cube Core v1.8.30 returns in development mode, with no token.
The responses are in `sources/rest-meta/`.

- **meta** is `GET /cubejs-api/v1/meta`.
- **extended** is `GET /cubejs-api/v1/meta?extended`. The Cube docs do not describe this parameter.
- "name" means the name, the title, the description, the type, the format, `meta` and the `public` flag of the member.

| Feature | Example | meta | extended adds |
|---|---|---|---|
| Cube on `sql_table` | `orders` | name | The file name. The table name is absent. |
| Cube on a `sql` query | `customers`, `events` | name | The SQL of the cube and the file name |
| `data_source` | `pg_orders`, `ch_order_item_facts`, `bq_events` | absent | absent |
| Jinja: macros, `set`, `if`, `for` | `orders`, `events` | The rendered members | The rendered SQL |
| Python globals | `orders` (`order_statuses`, `fq_table`) | The rendered members | The rendered SQL |
| Cubes from a Python function | `pg_customers`, `pg_order_items` | The rendered cubes | The rendered SQL |
| `COMPILE_CONTEXT` | `orders.debug_row_count` | One variant, for the context of the request | One variant |
| Model in JavaScript | `pg_products`, `pg_catalog` | name | The SQL and the file name |
| Measure `count`, `count_distinct`, `count_distinct_approx`, `sum`, `avg`, `min`, `max` | `orders`, `order_items` | name and `aggType` | The SQL of the measure |
| Measure `number` (calculated) | `orders.average_order_value` | name and `aggType` | The SQL with the member references |
| Measure `number_agg` | `orders.median_customer_revenue` | name, `aggType: numberAgg` | The SQL. `add_group_by` is absent. |
| Measure `string`, `time`, `boolean` | `orders.statuses_seen`, `first_order_at`, `has_returns` | name and `aggType` | The SQL |
| Measure `filters` | `orders.new_count`, `products.active_count` | absent | The SQL of each filter |
| `drill_members` | `orders.count` | The members | - |
| `rolling_window` | `orders.revenue_trailing_7_days` | `cumulative: true` | The SQL. The window is absent. |
| Multi-stage `time_shift` | `orders.revenue_prior_month` | name | The SQL. The time shift is absent. |
| Multi-stage `reduce_by`, `group_by`, `add_group_by` | `orders.revenue_all_statuses`, `revenue_of_status_group` | name | The SQL. The grouping change is absent. |
| Multi-stage `rank` | `orders.status_revenue_rank` | name, `aggType: rank` | Nothing. `order_by` is absent. |
| Measure `case` on a `switch` dimension | `orders.revenue_in_unit` | name | Nothing. The `case` is absent. |
| Dimension `string`, `number`, `boolean`, `time` | all cubes | name | The SQL |
| `primary_key` | `orders.id` | `primaryKey: true` | The SQL |
| Custom `granularities` | `orders.ordered_at` | The name, the title, the interval, the offset and the origin | - |
| Dimension `case` with labels | `orders.status_group` | name | The `case` with the SQL and the labels |
| `switch` dimension | `orders.amount_unit` | Type `string` and the values | - |
| `geo` dimension | `customers.region_location` | name | Nothing. The latitude and the longitude SQL are absent. |
| `sub_query` dimension | `customers.lifetime_revenue` | name | The SQL. The `sub_query` flag is absent. |
| Proxy dimension | `orders.customer_region` | name | The SQL with the member reference |
| Segments | `orders.completed` | name | The SQL |
| Hierarchies | `customers.geography`, `orders.order_status` | The levels | - |
| Joins `many_to_one`, `one_to_many`, `one_to_one` | `orders`, `customers`, `products` | Only `connectedComponent` | The cube, the relationship and the SQL of each join |
| Calendar cube | `calendar` | name. The `calendar` flag is absent. | The SQL of the dimension. The time shifts and the granularity SQL are absent. |
| `extends` | `products_snapshot_extended` | The members after the merge | The parent name is absent |
| `public: false` cube, view and member | `product_snapshots`, `events_internal`, `orders.customer_id` | Present with `public: false` in development mode | - |
| `title`, `description`, `format`, `meta` | all cubes | Present | - |
| View `join_path`, `includes`, `excludes`, `prefix`, `alias` | `orders_overview` | The members of the view, each with `aliasMember` | The file name. A view has no joins. |
| View folders | `orders_overview` | `folders` (flat) and `nestedFolders` | - |
| View measure and dimension | `order_items_detail.discount_share` | name | The SQL |
| View `default_filters` | `order_items_detail` | absent | absent |
| View `meta.ai_context` | `orders_overview` | Present | - |
| Pre-aggregations | `orders`, `pg_orders` | absent | The type, the granularity, the partition granularity, the member references, `refreshKey` (`every`, `incremental`, `updateWindow`) and the index types. The index columns, the `build_range` SQL and the `refresh_key` SQL are absent. |
| `FILTER_PARAMS`, `FILTER_GROUP` | `events` | absent | The SQL of the cube, with the calls as text |
| Access policy | `orders`, `events`, `orders_overview` | absent | absent |

## Cube Cloud Metadata API

`make cloud` collects the responses of a Cube Cloud deployment of this repository into `sources/cloud-metadata-api/`.
The script creates a token with the scopes `meta` and `meta-private` from a Platform API key (`tokens-for-meta-sync`).

| File | Request | Content |
|---|---|---|
| `data-sources.json` | `GET /v1/data-sources` | The name, the warehouse type and the database of each data source that connects. The two data sources in the private network are absent. |
| `entities.json` | `GET /v1/entities?include_private=true` | The name, the type and the `public` flag of the 14 cubes and the 6 views |
| `entities-all.json` | `POST /v1/entities/all` with `include_private` | The full metadata. The access policies hide members from this response. |
| `entities-all-public.json` | `POST /v1/entities/all` | The same without the private cubes and views |
| `model-export.json` | `POST /v1/model-export` | The full metadata of each cube, view and member. The access policies do not hide members. |
| `meta.json`, `meta-extended.json` | `GET /v1/meta`, `GET /v1/meta?extended` | The REST API of Cube Core on the deployment. The token gives access to it. |

All the responses are after the render of Jinja, the run of the JavaScript model and the merge of `extends`.

| Feature | `/v1/model-export` |
|---|---|
| Cube on `sql_table` | `table_references` with the data source, the database, the schema and the table |
| Cube on a `sql` query | The SQL of the cube, and `table_references` with the tables of the query |
| `data_source` | In each table reference and each column reference |
| Jinja, Python globals, JavaScript model, `extends` | The compiled members. The parent name of `extends` is absent. |
| `COMPILE_CONTEXT` | One variant, for the security context of the token |
| Measure | `agg_type`, the SQL, `filters`, `member_references` and `column_references` |
| Multi-stage measures | `multi_stage`, `time_shift`, `reduce_by`, `group_by`, `add_group_by`, `order_by` and `case` |
| `rolling_window` | The window |
| Dimension | The SQL, `is_primary_key`, `granularities`, `case`, `values` of a `switch` dimension, `latitude` and `longitude`, `sub_query`, the references |
| Joins | The cube, the relationship and the SQL. `cube_references` has the upstream cubes. |
| Calendar cube | `calendar: true`, the time shifts and the granularity SQL |
| Segments, hierarchies | Present, the segments with the SQL |
| Views | The members with the SQL `${cube.member}`, the references to the cube members and to the columns, the folders with nested folders, `default_filters`, `meta` |
| `public: false` | Present with `public: false` |
| `title`, `description`, `meta` | Present |
| `format` | absent |
| Pre-aggregations | absent |
| Access policy | absent |
| File name | absent |
| `FILTER_PARAMS`, `FILTER_GROUP` | The text of the calls in the SQL of the cube |

Limits of the column lineage:

- A member of a cube on `sql_table` has `column_references`. For a member of a cube on a `sql` query, the list is empty in most cases.
- A cube on a query that does not read a table (`calendar`) has a table reference with the name `TABLE`.
- A measure with `case` on a `switch` dimension has two column references that are not columns (`CUBE`, `amount_unit`).
- A table of a data source that is not Snowflake has no database in the reference.

`/v1/entities/all` has the same properties, without the SQL of the cube and without `add_group_by`.
With `include_private`, it returns the private cubes and views. It does not return the members that the access policy of `orders` hides from the owner of the key: five private members and the hierarchy.

## Cube Cloud Ossie export

The export is in preview. Until Cube support turns it on for the account, the request returns status 403: "Ossie conversions are not enabled for this account."
`make cloud` saves the responses in `sources/ossie-cloud/`.

To deploy this repository to Cube Cloud:

1. Create a deployment and connect it to the git repository with the SSH key and the webhook that the wizard shows.
2. Put `CUBE_API_URL` and `CUBE_API_TOKEN` (a Platform API key of an administrator) in `.secrets/cloud.env`.
3. Run `scripts/cloud_env.py <deployment id>`. This command sends the warehouse credentials of `.env` to the deployment.
4. Run `make cloud`.

## Offline Ossie converter

`make ossie-offline` runs the Cube converter of [apache/ossie-converters](https://github.com/apache/ossie-converters) at a pinned commit.
The results are in `sources/ossie-offline/`: `<variant>.ossie.yaml` is the document and `<variant>.issues.txt` is the report of the converter.

The converter does not convert this model as it is. Each row removes the cause of the failure in the row before.

| Variant | Input | Result |
|---|---|---|
| `full-model` | `model/` | Failure: a cube uses `extends` |
| `no-extends` | `model/` without the `extends_*` files | Failure. The converter skips each file with Jinja. A cube in plain YAML joins `orders`, and `orders` is in a skipped file. |
| `rendered-no-extends` | The output of `scripts/render_jinja.py`, without the `extends_*` files | Failure. The converter skips the JavaScript model, and a YAML cube joins the JavaScript cube. |
| `rendered-yaml-only` | The same, without the cubes that join the JavaScript cube | A document with 10 datasets, 60 metrics, 5 relationships and 33 issues |
| `rendered-yaml-only-snowflake` | The same, with `--source-dialect SNOWFLAKE` | The same document. Each expression has the `SNOWFLAKE` dialect label. |
| `rendered-view-<view>` | One view, with `--view <view> --project` | Failure for each of the three views: a segment, a hierarchy or a `sub_query` dimension in the view has no Ossie form |

`scripts/render_jinja.py` renders the templates with the minijinja package and `model/globals.py`, with an empty security context.
This is an approximation of the Cube Cloud export, which renders the templates in the deployment.

If a file in `model/` is not UTF-8 text, for example a `__pycache__` file, the converter stops with a Python error.

### What the document holds

"Extension" means the `custom_extensions` entry with the vendor name `CUBE`. Its `data` is a JSON string.
A consumer that does not read this string sees only the Ossie properties.

| Feature | Ossie property | Extension |
|---|---|---|
| Cube on `sql_table` | `dataset.source` is the table name | - |
| Cube on a `sql` query | `dataset.source` is the SQL text | - |
| `data_source` | absent | `cube_extras.data_source` |
| Jinja, Python globals, `COMPILE_CONTEXT` | The converter does not render them. The file is skipped. | - |
| Model in JavaScript | The file is skipped | - |
| `extends` | The conversion fails | - |
| Cube `title`, `meta`, `public` | `description` only | `cube_extras` |
| Dimension | `field` with `expression`, `datatype` and `description`. The `title` is the `label`. | `format`, `meta`, `public` |
| `primary_key` | `dataset.primary_key`, with the member name | `computed_primary_key` |
| Time dimension | `dimension.is_time: true` | `granularities` |
| Dimension `case` with labels | One `CASE` expression | The `case` |
| Proxy dimension | The expression `customers.region` | The Cube SQL |
| `geo` dimension | Two fields, `_latitude` and `_longitude` | `geo` |
| `sub_query` dimension | absent | `extra_dimensions` |
| `switch` dimension | absent | `extra_dimensions` |
| Measure `count`, `count_distinct`, `count_distinct_approx`, `sum`, `avg`, `min`, `max` | `metric` with a SQL expression, for example `COUNT(DISTINCT orders.CUSTOMER_ID)` | `format`, `title`, `meta`, `public`, `drill_members` |
| Measure `number` (calculated) | An expression on the metric names | - |
| Measure `string`, `time`, `boolean` | The expression, no `datatype` | `type` |
| Measure `filters` | `CASE WHEN` in the expression. The filter is not a separate property. | - |
| Measure name | The name. If two cubes have the same measure name, the name is `<cube>__<measure>`. A metric has no dataset property. | The Cube name |
| `rolling_window`, multi-stage measures, `number_agg`, `rank`, measure `case` | absent | `extra_measures`, with all the properties |
| Join with two columns | `relationship` with `from_columns` and `to_columns`. The converter adds a field for each column that is not a dimension. | The Cube SQL. `relationship` only for `one_to_many` and `one_to_one`. |
| Join on an expression | absent | `extra_joins` |
| The same join declared on the two cubes | Two relationships | - |
| Calendar cube | A dataset | `calendar: true`, the time shifts and the granularity SQL |
| Segments, hierarchies | absent | `cube_extras` |
| Pre-aggregations | absent | `cube_extras.pre_aggregations`, with the index columns, the `build_range` SQL and the `refresh_key` SQL |
| Access policy | absent | `cube_extras.access_policy`, with the groups, the conditions, the member lists and the row filters |
| `FILTER_PARAMS`, `FILTER_GROUP` | The text of the calls stays in `dataset.source` | - |
| Views | absent in a full model conversion | The model extension has each view: `cubes` with `join_path`, `includes`, `excludes`, `prefix` and `alias`, the folders, the view members, `default_filters` and the access policy |
| File names | absent | `cube_files` and `view_files` in the model extension |

### Validation

`make ossie-validate` validates each document with an Ossie validator that is not in this repository.

- The converter writes `version: 0.3.0.dev0`. A validator with the `0.2.0.dev0` schema rejects the document for the version only.
- With the version changed to `0.2.0.dev0`, the document is valid and has five warnings.
- Each warning is for a relationship: `to_columns` has the column name (`ID`) and `primary_key` has the member name (`id`), so the two names do not match.
- An import of the document into another schema format and an export back keeps each dataset, field, metric, relationship and extension. Only the primary key of four datasets changes from `id` to `ID`, for the same reason.

## Git repository

A reader of the files in git gets each property of the model, but not in the form that Cube compiles.

| Feature | In the files |
|---|---|
| A cube or a view in plain YAML | Each property, as written |
| A file with Jinja | The template. The reader must render it with a minijinja engine and `model/globals.py`. |
| Python globals | Python code. The reader must run it to get the values. |
| `COMPILE_CONTEXT` | The branches of each variant. The security context decides the variant, and it is not in the files. |
| Model in JavaScript | JavaScript code. The reader must run it. |
| `extends` | The parent name and the changed members. The reader must merge the two. |
| View `includes: "*"`, `prefix`, `alias` | The rule. The reader must resolve the member list. |
| `data_source` | The name. The warehouse type and the connection are in environment variables of the deployment. |
| `cube.py` | Python code for the groups, the query rewrite and the application identifier |

`scripts/render_jinja.py` shows the least work that a reader of the files must do for the Jinja files.

## Notes on Cube v1.8.30

- Cube has no model file in Python. A Python function in `model/globals.py` returns the definitions, and a Jinja template writes them as YAML.
- A `number_agg` measure must have `multi_stage: true`, and its SQL can refer only to members.
- The access policies use `group`. The function `context_to_groups` in `cube.py` gives the groups of a request.
- A member of a `row_level` filter must be a member of the same cube. Use a proxy dimension for a member of a joined cube.
- A view accepts a `geo` dimension, but each query that selects it through the view fails. The views exclude `region_location`.
- The template engine is not the Python Jinja library. Use the `items` filter to loop on a dictionary: `{% for k, v in d | items %}`.
- In development mode with no token, `COMPILE_CONTEXT.securityContext` is not defined. Use `COMPILE_CONTEXT.securityContext | default({})`.
- Cube reads `cube.py` only at start. Restart the container after a change.

## License

Apache License 2.0. See `LICENSE`.
