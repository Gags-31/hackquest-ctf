# React Frontend Patterns

## Project Structure
src/api (typed API client), src/auth (context + guards), src/components
(reusable UI), src/pages (route-level screens), src/types (shared models).
Keep pages thin: fetch through the API client and compose components.

## Routing and Guards
Use a small declarative router. A ProtectedRoute component redirects to
/login when no token is present. An AdminRoute additionally checks the role
stored in the auth context.

## State Management
Keep auth state in a React context (token in localStorage, user profile in
memory). Server data is fetched per page with loading and error states; avoid
global mutable stores for small apps.

## Forms
Controlled inputs with client-side validation mirroring the backend schema:
required fields, min lengths, numeric ranges. Show server validation messages
returned by the API next to the offending field.

## API Client
One module exports typed functions per resource and attaches the bearer token
from storage. On a 401 response, clear the token and redirect to login.

## Styling
Tailwind utility classes, a consistent color palette, responsive grid layouts
and accessible form labels. Prefer small composed components over page-level
CSS.
