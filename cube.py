# Python configuration of Cube. Cube reads this file at start.
from cube import config

config.schema_path = "model"


def security_context(ctx: dict) -> dict:
    # The security context is None for a request without a token (development mode).
    return ctx.get("securityContext") or {}


@config("context_to_app_id")
def context_to_app_id(ctx: dict) -> str:
    # One compiled data model for each environment, as the model reads
    # COMPILE_CONTEXT.securityContext.environment.
    environment = security_context(ctx).get("environment", "default")
    return f"CUBE_DEMO_{environment}"


@config("context_to_groups")
def context_to_groups(ctx: dict) -> list[str]:
    # The access policies in the model refer to these groups.
    # A request without a token (development mode) is in the `default` group.
    return security_context(ctx).get("groups", ["default"])


@config("query_rewrite")
def query_rewrite(query: dict, ctx: dict) -> dict:
    # A tenant in the security context limits each query on `orders` to its customers.
    customer_id = security_context(ctx).get("customer_id")
    members = query.get("measures", []) + query.get("dimensions", [])
    if customer_id is not None and any(m.startswith("orders.") for m in members):
        query.setdefault("filters", []).append(
            {
                "member": "orders.customer_id",
                "operator": "equals",
                "values": [str(customer_id)],
            }
        )
    return query


@config("scheduled_refresh_contexts")
def scheduled_refresh_contexts() -> list[dict]:
    return [{"securityContext": {"environment": "default"}}]
