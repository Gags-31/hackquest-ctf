# Coding Standards

## Python Style
PEP 8 formatting, type hints on public functions, docstrings for modules and
non-trivial functions. snake_case for modules, functions and variables;
PascalCase for classes. One responsibility per module.

## Naming
Routers: <entity>.py under routers/. Services: verb-led functions
(create_order, list_products). Schemas: <Entity>Create / <Entity>Update /
<Entity>Read. Tests: test_<behavior>.py with descriptive test names.

## Testing Pyramid
Unit tests for business rules and security helpers, API tests for every
endpoint (success + auth + validation + not-found paths), a small number of
end-to-end flows (register -> login -> use feature). Tests must not depend on
execution order or shared mutable state.

## Error and Edge Cases
Handle empty lists, missing rows, duplicate natural keys, and concurrent
updates explicitly. Return meaningful messages that a UI can display.

## Documentation
Every project ships README (setup + run), ARCHITECTURE.md (structure and
decisions), API.md (endpoint reference), DATABASE.md (schema + ER diagram)
and DEPLOYMENT.md (build and release steps). Docs update when code changes.

## Git Hygiene
Small commits with imperative messages, feature branches, and no generated
artifacts or secrets in version control. Provide a .env.example with every
required variable documented.
