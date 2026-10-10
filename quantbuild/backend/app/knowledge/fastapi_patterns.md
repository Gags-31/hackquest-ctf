# FastAPI Backend Patterns

## Application Factory and Routers
Create the app in main.py, register one APIRouter per resource under /api.
Each router owns: list (GET /api/<resource>), retrieve (GET /api/<resource>/{id}),
create (POST), update (PUT), delete (DELETE). Return proper status codes:
201 on create, 404 for missing rows, 403 for forbidden, 401 when unauthenticated.

## Dependency Injection
Use Depends() for the database session and current-user resolution. A
get_db dependency yields a SQLAlchemy session per request. A
get_current_user dependency decodes the bearer JWT and loads the user;
require_roles("Admin") builds a role-checking dependency for RBAC.

## Pydantic Schemas
Separate Create, Update and Read schemas per entity. Read schemas use
model_config = ConfigDict(from_attributes=True). Never expose password_hash
or internal flags in a Read schema.

## SQLAlchemy Models
Declarative Base, Mapped columns, relationships declared both directions where
navigation is needed. Foreign keys reference "<table>.id". Use server_default
for created_at timestamps.

## Error Handling
Raise HTTPException with a detail message. Do not leak stack traces or
database errors to clients. Validate input with Pydantic, not manual checks.

## Configuration
Read configuration (database URL, secret key, token TTL, CORS origins) from
environment variables with sensible development defaults. Never hardcode
production secrets.
