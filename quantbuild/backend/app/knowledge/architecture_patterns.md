# Software Architecture Patterns

## Monolithic Architecture
A single deployable unit containing all layers. Best for small teams, MVPs and
simple domains. Advantages: simple deployment, easy local development,
straightforward transactions. Risks: tight coupling as the codebase grows.

## Modular Monolith
A monolith internally split into well-isolated modules (auth, catalog, orders)
with explicit boundaries and one-way dependencies. Best default for most
business applications: keeps deployment simple while enforcing separation of
concerns. Modules communicate through service interfaces.

## Microservices
Independently deployable services, each owning its data. Use only when scaling,
team autonomy or fault-isolation requirements justify the operational cost:
service discovery, distributed tracing, eventual consistency, API gateways.

## Event-Driven Architecture
Components communicate through events on a broker (order.created, payment.succeeded).
Good for high-throughput asynchronous workflows and integration-heavy systems.
Adds complexity: idempotency, ordering, schema evolution.

## Layered Backend Structure
routes (HTTP) -> services (business logic) -> models (persistence). Routers
never query the database directly; services never know about HTTP. This keeps
business rules testable without a web server.

## Choosing an Architecture
Consider: number of distinct domains, expected traffic, team size, consistency
requirements and deployment maturity. Recommend the simplest architecture that
satisfies the requirements, and justify the choice explicitly.
