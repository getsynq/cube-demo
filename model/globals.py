# Python functions, variables and filters for the Jinja templates in this directory.
import os

from cube import TemplateContext

template = TemplateContext()

# Statuses of an order, in the sequence of the order life cycle.
ORDER_STATUSES = ["new", "paid", "shipped", "delivered", "returned"]

template.add_variable("warehouse_database", "DWH_TESTING")
template.add_variable("high_value_threshold", 1000)


@template.function("order_statuses")
def order_statuses():
    return ORDER_STATUSES


@template.function("fq_table")
def fq_table(schema, table):
    """Fully qualified name of a table in the default (Snowflake) data source."""
    return f"DWH_TESTING.{schema}.{table}"


@template.function("bigquery_dataset")
def bigquery_dataset():
    return os.environ.get("CUBE_DEMO_BIGQUERY_DATASET", "synq_dwhtesting")


@template.filter("title_case")
def title_case(value):
    return str(value).replace("_", " ").title()


@template.function("python_cubes")
def python_cubes():
    """Cube definitions made in Python. model/cubes/python_generated.yml renders them.

    Cube has no model file in Python: a Python function returns the
    definitions and a Jinja template writes them as YAML.
    """
    tables = {
        "pg_customers": {
            "table": "schema_b.customers",
            "description": "Customer directory in PostgreSQL",
            "primary_key": "id",
            "columns": [
                {"name": "id", "sql": "id", "type": "number"},
                {"name": "full_name", "sql": "full_name", "type": "string"},
                {"name": "region", "sql": "region", "type": "string"},
            ],
            "sums": [],
            "joins": [],
        },
        "pg_order_items": {
            "table": "schema_a.order_items",
            "description": "Order line items in PostgreSQL",
            "primary_key": "id",
            "columns": [
                {
                    "name": "id",
                    "sql": "{CUBE}.order_id || '-' || {CUBE}.item_id",
                    "type": "string",
                },
                {"name": "order_id", "sql": "order_id", "type": "number"},
                {"name": "product_id", "sql": "product_id", "type": "number"},
            ],
            "sums": ["quantity", "discount"],
            "joins": [
                {
                    "name": "pg_products",
                    "relationship": "many_to_one",
                    "sql": "{CUBE}.product_id = {pg_products.id}",
                }
            ],
        },
    }
    return [{"name": name, **definition} for name, definition in tables.items()]
