# Database Design Guidelines

## Normalization
Design to third normal form: every non-key attribute depends on the whole
primary key and nothing else. Denormalize only with a measured performance
reason (e.g. cached counters).

## Keys and Relationships
Every table has an integer surrogate primary key named id. One-to-many
relationships use a foreign key on the many side referencing <table>.id.
One-to-one uses a unique foreign key. Name foreign keys <entity>_id.

## Constraints and Indexes
Add NOT NULL unless the attribute is genuinely optional. UNIQUE on natural
identifiers (email, sku, slug). Index every foreign key and every column used
in frequent filters or sorting. CHECK constraints for enums kept as strings.

## Field Types
ids: integer; money and measurements: float (document if decimal needed);
flags: boolean; timestamps: datetime with server defaults; long content: text;
short labels: bounded strings.

## Migrations
Schema changes ship as versioned migration SQL. Never edit released
migrations - add a new one. Keep the SQL DDL and the ORM models in sync.

## Common Pitfalls
missing foreign-key indexes, nullable ownership columns, storing derived
values without invalidation rules, and polymorphic columns that mix types.
