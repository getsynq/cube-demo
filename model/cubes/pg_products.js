// A model in JavaScript, on the PostgreSQL data source.
// Shows: cube() and view() in JavaScript, a member made in a loop, a segment.
const priceBands = { budget: [0, 10], standard: [10, 30], premium: [30, 1000000] };

cube(`pg_products`, {
  sql_table: `schema_a.products`,
  data_source: `postgres`,
  title: `Products (PostgreSQL)`,
  description: `Product catalog in PostgreSQL, defined in a JavaScript model file`,
  meta: { owner: `catalog-team`, language: `javascript` },

  dimensions: {
    id: { sql: `id`, type: `number`, primary_key: true },
    name: { sql: `name`, type: `string` },
    category: { sql: `category`, type: `string` },
    is_active: { sql: `is_active`, type: `boolean` },
    created_at: { sql: `created_at`, type: `time` },
  },

  measures: {
    count: { type: `count` },
    avg_price: { sql: `price`, type: `avg`, format: `currency` },
    // One filtered count for each price band.
    ...Object.fromEntries(
      Object.entries(priceBands).map(([band, [low, high]]) => [
        `${band}_count`,
        {
          type: `count`,
          filters: [{ sql: `${CUBE}.price >= ${low} AND ${CUBE}.price < ${high}` }],
        },
      ])
    ),
  },

  segments: {
    batch: { sql: `${CUBE}.category = 'Batch'` },
  },
});

view(`pg_catalog`, {
  description: `A view in JavaScript on the PostgreSQL cubes`,
  cubes: [
    { join_path: pg_order_items, includes: [`count`, `total_quantity`] },
    { join_path: pg_order_items.pg_products, includes: [`name`, `category`, `avg_price`], prefix: true },
  ],
});
