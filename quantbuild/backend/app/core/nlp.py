"""Natural-language requirement understanding (offline NLP engine).

This module powers the Requirement Agent when no external LLM is configured,
and provides the deterministic fallback that keeps the whole platform usable
with zero external dependencies.  It performs:

* application-type / domain detection
* user-role extraction
* feature extraction
* database-entity extraction with typed fields and relationships
* natural-language *modification* analysis (add / remove / change)

The output is the structured project specification consumed by every other
agent through the Central Project Context.
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------

def f(name: str, type_: str = "str", **kw: Any) -> dict[str, Any]:
    field = {"name": name, "type": type_}
    field.update(kw)
    return field


ID_FIELD = f("id", "int", primary_key=True)
CREATED = f("created_at", "datetime")


def entity(keywords: list[str], fields: list[dict[str, Any]],
           description: str = "") -> dict[str, Any]:
    return {"keywords": keywords, "fields": fields, "description": description}


# ---------------------------------------------------------------------------
# Entity catalog — typed fields + foreign-key relationships
# ---------------------------------------------------------------------------

ENTITY_CATALOG: dict[str, dict[str, Any]] = {
    "User": entity(["user", "users", "account", "accounts", "member", "members"], [
        ID_FIELD, f("email", unique=True), f("password_hash"), f("full_name"),
        f("role", default="user"), f("is_active", "bool", default=True), CREATED,
    ], "Registered application user"),
    "Product": entity(["product", "products", "item", "items", "catalog", "catalogue"], [
        ID_FIELD, f("name"), f("description", "text"), f("price", "float"),
        f("stock", "int", default=0), f("sku", unique=True), f("image_url", nullable=True),
        f("category_id", "fk", ref="Category", nullable=True), CREATED,
    ], "Sellable product"),
    "Category": entity(["category", "categories"], [
        ID_FIELD, f("name", unique=True), f("description", "text", nullable=True), CREATED,
    ]),
    "Cart": entity(["cart", "carts", "basket", "baskets"], [
        ID_FIELD, f("user_id", "fk", ref="User", unique=True), CREATED,
    ]),
    "CartItem": entity(["cart item", "cart items"], [
        ID_FIELD, f("cart_id", "fk", ref="Cart"), f("product_id", "fk", ref="Product"),
        f("quantity", "int", default=1), CREATED,
    ]),
    "Order": entity(["order", "orders", "purchase", "purchases"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("status", default="pending"),
        f("total", "float", default=0.0), f("shipping_address", "text", nullable=True), CREATED,
    ]),
    "OrderItem": entity(["order item", "order items"], [
        ID_FIELD, f("order_id", "fk", ref="Order"), f("product_id", "fk", ref="Product"),
        f("quantity", "int", default=1), f("unit_price", "float"),
    ]),
    "Payment": entity(["payment", "payments", "checkout", "transaction", "transactions"], [
        ID_FIELD, f("order_id", "fk", ref="Order"), f("amount", "float"),
        f("method", default="card"), f("status", default="pending"),
        f("transaction_ref", nullable=True), CREATED,
    ]),
    "Review": entity(["review", "reviews", "rating", "ratings"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("product_id", "fk", ref="Product"),
        f("rating", "int"), f("comment", "text", nullable=True), CREATED,
    ]),
    "Wishlist": entity(["wishlist", "wishlists", "wish list"], [
        ID_FIELD, f("user_id", "fk", ref="User", unique=True), CREATED,
    ]),
    "WishlistItem": entity(["wishlist item", "wishlist items"], [
        ID_FIELD, f("wishlist_id", "fk", ref="Wishlist"), f("product_id", "fk", ref="Product"),
        CREATED,
    ]),
    "Address": entity(["address", "addresses"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("line1"), f("line2", nullable=True),
        f("city"), f("state"), f("postal_code"), f("country"),
        f("is_default", "bool", default=False),
    ]),
    "Shipment": entity(["shipment", "shipments", "delivery", "deliveries", "shipping", "tracking"], [
        ID_FIELD, f("order_id", "fk", ref="Order"), f("carrier", nullable=True),
        f("tracking_number", nullable=True), f("status", default="preparing"),
        f("shipped_at", "datetime", nullable=True),
    ]),
    "Notification": entity(["notification", "notifications", "alert", "alerts"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("title"), f("message", "text"),
        f("is_read", "bool", default=False), CREATED,
    ]),
    "Doctor": entity(["doctor", "doctors", "physician", "physicians"], [
        ID_FIELD, f("user_id", "fk", ref="User", unique=True), f("specialization"),
        f("bio", "text", nullable=True), f("consultation_fee", "float", default=0.0),
        f("rating", "float", default=0.0),
    ]),
    "Patient": entity(["patient", "patients"], [
        ID_FIELD, f("user_id", "fk", ref="User", unique=True), f("date_of_birth", "date"),
        f("gender", nullable=True), f("phone", nullable=True),
        f("medical_history", "text", nullable=True),
    ]),
    "Appointment": entity(["appointment", "appointments", "booking", "bookings", "slot", "slots"], [
        ID_FIELD, f("patient_id", "fk", ref="Patient"), f("doctor_id", "fk", ref="Doctor"),
        f("scheduled_at", "datetime"), f("status", default="scheduled"),
        f("reason", "text", nullable=True), CREATED,
    ]),
    "Availability": entity(["availability", "available slots", "schedule"], [
        ID_FIELD, f("doctor_id", "fk", ref="Doctor"), f("day_of_week", "int"),
        f("start_time"), f("end_time"),
    ]),
    "Post": entity(["post", "posts", "article", "articles", "blog"], [
        ID_FIELD, f("author_id", "fk", ref="User"), f("title"), f("content", "text"),
        f("status", default="draft"), CREATED,
    ]),
    "Comment": entity(["comment", "comments"], [
        ID_FIELD, f("post_id", "fk", ref="Post"), f("author_id", "fk", ref="User"),
        f("content", "text"), CREATED,
    ]),
    "Tag": entity(["tag", "tags"], [
        ID_FIELD, f("name", unique=True),
    ]),
    "Task": entity(["task", "tasks", "todo", "todos", "to-do"], [
        ID_FIELD, f("project_id", "fk", ref="Project"), f("assignee_id", "fk", ref="User", nullable=True),
        f("title"), f("description", "text", nullable=True), f("status", default="todo"),
        f("priority", default="medium"), f("due_date", "date", nullable=True), CREATED,
    ]),
    "Project": entity(["project", "projects", "workspace", "workspaces"], [
        ID_FIELD, f("owner_id", "fk", ref="User"), f("name"),
        f("description", "text", nullable=True), CREATED,
    ]),
    "Course": entity(["course", "courses", "class", "classes"], [
        ID_FIELD, f("instructor_id", "fk", ref="User"), f("title"),
        f("description", "text", nullable=True), f("price", "float", default=0.0), CREATED,
    ]),
    "Lesson": entity(["lesson", "lessons", "module", "modules", "lecture", "lectures"], [
        ID_FIELD, f("course_id", "fk", ref="Course"), f("title"),
        f("content", "text", nullable=True), f("position", "int", default=0),
    ]),
    "Enrollment": entity(["enrollment", "enrollments", "enrolment"], [
        ID_FIELD, f("student_id", "fk", ref="User"), f("course_id", "fk", ref="Course"),
        f("progress", "float", default=0.0), CREATED,
    ]),
    "Listing": entity(["listing", "listings", "property rental", "stay", "stays"], [
        ID_FIELD, f("host_id", "fk", ref="User"), f("title"), f("description", "text"),
        f("location"), f("price_per_night", "float"), f("max_guests", "int", default=2), CREATED,
    ]),
    "Booking": entity(["reservation", "reservations"], [
        ID_FIELD, f("guest_id", "fk", ref="User"), f("listing_id", "fk", ref="Listing"),
        f("check_in", "date"), f("check_out", "date"), f("guests", "int", default=1),
        f("status", default="pending"), f("total_price", "float", default=0.0), CREATED,
    ]),
    "Restaurant": entity(["restaurant", "restaurants"], [
        ID_FIELD, f("owner_id", "fk", ref="User"), f("name"),
        f("description", "text", nullable=True), f("address"), f("cuisine", nullable=True),
    ]),
    "MenuItem": entity(["menu item", "menu items", "dish", "dishes", "menu"], [
        ID_FIELD, f("restaurant_id", "fk", ref="Restaurant"), f("name"),
        f("description", "text", nullable=True), f("price", "float"),
        f("is_available", "bool", default=True),
    ]),
    "Account": entity(["bank account", "bank accounts", "wallet", "wallets"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("name"), f("balance", "float", default=0.0),
        f("currency", default="USD"), CREATED,
    ]),
    "Expense": entity(["expense", "expenses", "spending"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("amount", "float"),
        f("category"), f("note", "text", nullable=True), f("spent_at", "datetime"),
    ]),
    "Budget": entity(["budget", "budgets"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("category"),
        f("monthly_limit", "float"), CREATED,
    ]),
    "Room": entity(["room", "rooms", "channel", "channels", "group chat"], [
        ID_FIELD, f("name"), f("is_group", "bool", default=False),
        f("created_by", "fk", ref="User"), CREATED,
    ]),
    "Message": entity(["message", "messages", "chat"], [
        ID_FIELD, f("room_id", "fk", ref="Room"), f("sender_id", "fk", ref="User"),
        f("content", "text"), f("sent_at", "datetime"),
    ]),
    "Event": entity(["event", "events", "concert", "concerts", "meetup", "meetups"], [
        ID_FIELD, f("organizer_id", "fk", ref="User"), f("title"),
        f("description", "text", nullable=True), f("location"),
        f("starts_at", "datetime"), f("capacity", "int", default=100), CREATED,
    ]),
    "Ticket": entity(["ticket", "tickets"], [
        ID_FIELD, f("event_id", "fk", ref="Event"), f("user_id", "fk", ref="User"),
        f("seat", nullable=True), f("status", default="booked"), f("purchased_at", "datetime"),
    ]),
    "Job": entity(["job", "jobs", "vacancy", "vacancies", "position", "positions"], [
        ID_FIELD, f("employer_id", "fk", ref="User"), f("title"),
        f("description", "text"), f("location", nullable=True),
        f("salary_min", "float", nullable=True), f("salary_max", "float", nullable=True),
        f("status", default="open"), CREATED,
    ]),
    "Application": entity(["application", "applications", "applicant", "applicants", "candidates"], [
        ID_FIELD, f("job_id", "fk", ref="Job"), f("applicant_id", "fk", ref="User"),
        f("resume_url", nullable=True), f("cover_letter", "text", nullable=True),
        f("status", default="submitted"), CREATED,
    ]),
    "Property": entity(["property", "properties", "house", "houses", "home", "homes", "real estate"], [
        ID_FIELD, f("agent_id", "fk", ref="User"), f("title"),
        f("description", "text", nullable=True), f("address"), f("price", "float"),
        f("bedrooms", "int", default=2), f("bathrooms", "int", default=1),
        f("status", default="available"), CREATED,
    ]),
    "Workout": entity(["workout", "workouts", "exercise", "exercises"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("name"), f("notes", "text", nullable=True),
        f("duration_minutes", "int", nullable=True), f("performed_at", "datetime"),
    ]),
    "Subscription": entity(["subscription", "subscriptions", "plan", "plans"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("plan_name"),
        f("status", default="active"), f("renews_at", "datetime", nullable=True), CREATED,
    ]),
    "Invoice": entity(["invoice", "invoices", "bill", "bills"], [
        ID_FIELD, f("user_id", "fk", ref="User"), f("amount", "float"),
        f("status", default="unpaid"), f("due_date", "date", nullable=True), CREATED,
    ]),
}

# Map singular / lowercase keyword -> entity name for quick lookup
_KEYWORD_INDEX: dict[str, str] = {}
for _ename, _edef in ENTITY_CATALOG.items():
    for _kw in _edef["keywords"]:
        _KEYWORD_INDEX[_kw] = _ename

# Companion entities that only make sense with their parents
_COMPANIONS: dict[str, list[str]] = {
    "Cart": ["CartItem"],
    "Order": ["OrderItem"],
    "Wishlist": ["WishlistItem"],
    "Course": ["Lesson"],
}


# ---------------------------------------------------------------------------
# Domain catalog
# ---------------------------------------------------------------------------

DOMAINS: dict[str, dict[str, Any]] = {
    "ecommerce": {
        "keywords": ["e-commerce", "ecommerce", "shop", "shopping", "store", "marketplace",
                     "cart", "checkout", "sell", "buy", "retail"],
        "app_type": "E-Commerce Platform",
        "roles": ["Customer", "Admin"],
        "entities": ["User", "Product", "Category", "Cart", "CartItem", "Order",
                     "OrderItem", "Payment", "Notification"],
        "features": ["User Registration", "User Login", "Browse Products", "Product Search",
                     "Shopping Cart", "Checkout & Payments", "Order Tracking",
                     "Admin Dashboard", "Notifications"],
    },
    "healthcare": {
        "keywords": ["healthcare", "health", "hospital", "clinic", "doctor", "doctors",
                     "patient", "patients", "medical", "appointment", "appointments"],
        "app_type": "Healthcare Appointment Platform",
        "roles": ["Patient", "Doctor", "Administrator"],
        "entities": ["User", "Doctor", "Patient", "Appointment", "Availability", "Notification"],
        "features": ["User Registration", "User Login", "Doctor Search", "Availability Management",
                     "Appointment Booking", "Notifications", "Admin Dashboard"],
    },
    "rental": {
        "keywords": ["rental", "rentals", "airbnb", "stay", "stays", "listing", "listings",
                     "vacation", "accommodation"],
        "app_type": "Property Rental Platform",
        "roles": ["Guest", "Host", "Admin"],
        "entities": ["User", "Listing", "Booking", "Review", "Payment", "Notification"],
        "features": ["User Registration", "User Login", "Browse Listings", "Search & Filters",
                     "Booking Management", "Payments", "Reviews", "Notifications"],
    },
    "food_delivery": {
        "keywords": ["food", "restaurant", "restaurants", "menu", "delivery", "meal", "meals",
                     "dish", "dishes"],
        "app_type": "Food Delivery Platform",
        "roles": ["Customer", "Restaurant Owner", "Admin"],
        "entities": ["User", "Restaurant", "MenuItem", "Order", "OrderItem", "Payment",
                     "Notification"],
        "features": ["User Registration", "User Login", "Browse Restaurants", "Menu Management",
                     "Order Placement", "Payments", "Order Tracking", "Notifications"],
    },
    "blog": {
        "keywords": ["blog", "blogs", "cms", "article", "articles", "news", "publishing"],
        "app_type": "Content Publishing Platform",
        "roles": ["Reader", "Author", "Editor"],
        "entities": ["User", "Post", "Comment", "Tag", "Category"],
        "features": ["User Registration", "User Login", "Create & Publish Posts",
                     "Comments", "Tags & Categories", "Search"],
    },
    "task_management": {
        "keywords": ["task", "tasks", "todo", "to-do", "kanban", "project management",
                     "team collaboration", "sprint"],
        "app_type": "Project & Task Management Platform",
        "roles": ["Team Member", "Project Manager", "Admin"],
        "entities": ["User", "Project", "Task", "Comment", "Notification"],
        "features": ["User Registration", "User Login", "Project Workspaces", "Task Boards",
                     "Assignments & Due Dates", "Comments", "Notifications"],
    },
    "learning": {
        "keywords": ["learning", "lms", "course", "courses", "lesson", "lessons", "student",
                     "students", "teacher", "education", "e-learning", "mooc"],
        "app_type": "Online Learning Platform",
        "roles": ["Student", "Instructor", "Admin"],
        "entities": ["User", "Course", "Lesson", "Enrollment", "Review", "Notification"],
        "features": ["User Registration", "User Login", "Course Catalog", "Lesson Content",
                     "Enrollments & Progress", "Reviews", "Certificates", "Admin Dashboard"],
    },
    "finance": {
        "keywords": ["expense", "expenses", "budget", "budgets", "finance", "money", "spending",
                     "wallet", "bank"],
        "app_type": "Personal Finance Manager",
        "roles": ["User", "Admin"],
        "entities": ["User", "Account", "Expense", "Budget", "Notification"],
        "features": ["User Registration", "User Login", "Expense Tracking", "Budgets & Limits",
                     "Spending Reports", "Notifications"],
    },
    "chat": {
        "keywords": ["chat", "messaging", "messenger", "rooms", "channels", "slack"],
        "app_type": "Real-Time Messaging Platform",
        "roles": ["User", "Moderator", "Admin"],
        "entities": ["User", "Room", "Message", "Notification"],
        "features": ["User Registration", "User Login", "Chat Rooms", "Direct Messages",
                     "Message History", "Notifications"],
    },
    "jobs": {
        "keywords": ["job", "jobs", "recruitment", "hiring", "career", "careers", "applicant",
                     "applicants", "candidate"],
        "app_type": "Recruitment & Job Board Platform",
        "roles": ["Job Seeker", "Employer", "Admin"],
        "entities": ["User", "Job", "Application", "Notification"],
        "features": ["User Registration", "User Login", "Job Listings", "Search & Filters",
                     "Applications", "Application Tracking", "Admin Dashboard"],
    },
    "real_estate": {
        "keywords": ["real estate", "property", "properties", "house", "houses", "homes",
                     "apartment", "apartments"],
        "app_type": "Real Estate Marketplace",
        "roles": ["Buyer", "Agent", "Admin"],
        "entities": ["User", "Property", "Appointment", "Notification"],
        "features": ["User Registration", "User Login", "Property Listings", "Search & Filters",
                     "Viewing Appointments", "Saved Properties", "Admin Dashboard"],
    },
    "events": {
        "keywords": ["event", "events", "ticket", "tickets", "ticketing", "concert", "meetup",
                     "conference"],
        "app_type": "Event Ticketing Platform",
        "roles": ["Attendee", "Organizer", "Admin"],
        "entities": ["User", "Event", "Ticket", "Payment", "Notification"],
        "features": ["User Registration", "User Login", "Browse Events", "Ticket Booking",
                     "Payments", "E-Tickets", "Notifications", "Admin Dashboard"],
    },
    "fitness": {
        "keywords": ["fitness", "workout", "workouts", "gym", "exercise", "training"],
        "app_type": "Fitness Tracking Platform",
        "roles": ["Member", "Coach", "Admin"],
        "entities": ["User", "Workout", "Subscription", "Notification"],
        "features": ["User Registration", "User Login", "Workout Logging", "Progress Tracking",
                     "Subscriptions", "Notifications"],
    },
    "generic": {
        "keywords": [],
        "app_type": "Web Application",
        "roles": ["User", "Admin"],
        "entities": ["User"],
        "features": ["User Registration", "User Login", "Dashboard", "Admin Panel"],
    },
}

ROLE_KEYWORDS = [
    "customer", "customers", "admin", "administrator", "administrators", "patient", "patients",
    "doctor", "doctors", "guest", "guests", "host", "hosts", "student", "students",
    "instructor", "instructors", "teacher", "teachers", "author", "authors", "reader",
    "readers", "editor", "editors", "member", "members", "manager", "managers", "employer",
    "employers", "job seeker", "applicant", "applicants", "buyer", "buyers", "seller",
    "sellers", "agent", "agents", "attendee", "attendees", "organizer", "organizers",
    "driver", "drivers", "restaurant owner", "moderator", "moderators", "coach", "user", "users",
]

FEATURE_PATTERNS: list[tuple[str, str]] = [
    (r"regist", "User Registration"),
    (r"log\s?in|sign\s?in|authentication|login", "User Login"),
    (r"browse", "Browse & Discovery"),
    (r"search", "Search"),
    (r"filter", "Filtering"),
    (r"cart|basket", "Shopping Cart"),
    (r"checkout", "Checkout"),
    (r"pay", "Payments"),
    (r"track", "Tracking"),
    (r"order", "Order Management"),
    (r"book", "Booking"),
    (r"notif", "Notifications"),
    (r"dashboard", "Dashboard"),
    (r"review|rating", "Reviews & Ratings"),
    (r"wishlist|wish list", "Wishlist"),
    (r"upload", "File Uploads"),
    (r"report|analytics", "Reports & Analytics"),
    (r"chat|messag", "Messaging"),
    (r"profile", "User Profiles"),
    (r"admin", "Admin Panel"),
    (r"cancel", "Cancellations"),
    (r"refund", "Refunds"),
    (r"email", "Email Integration"),
    (r"export", "Data Export"),
    (r"import", "Data Import"),
    (r"comment", "Comments"),
    (r"subscription|subscribe", "Subscriptions"),
    (r"invoice|billing", "Billing & Invoices"),
]


# ---------------------------------------------------------------------------
# Public analysis API
# ---------------------------------------------------------------------------

def singularize(word: str) -> str:
    w = word.strip().lower()
    if w.endswith("ies") and len(w) > 3:
        return w[:-3] + "y"
    if w.endswith(("ses", "xes", "zes", "ches", "shes")):
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 1:
        return w[:-1]
    return w


def title_name(words: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[\s_\-]+", words.strip()) if part)


def detect_domain(text: str) -> str:
    lower = text.lower()
    scores: dict[str, int] = {}
    for key, dom in DOMAINS.items():
        if key == "generic":
            continue
        score = sum(1 for kw in dom["keywords"] if kw in lower)
        if score:
            scores[key] = score
    if not scores:
        return "generic"
    return max(scores, key=lambda k: scores[k])


def extract_roles(text: str, domain: str) -> list[str]:
    lower = text.lower()
    roles: list[str] = []
    for kw in ROLE_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", lower):
            role = kw.capitalize() if " " not in kw else kw.title()
            if role not in ("User", "Users") and role not in roles:
                roles.append(role)
    # "<role>s can ..." pattern
    for match in re.finditer(r"\b([a-z][a-z]+)s?\s+can\b", lower):
        word = match.group(1)
        if word in ROLE_KEYWORDS:
            role = word.capitalize()
            if role not in roles:
                roles.append(role)
    for role in DOMAINS[domain]["roles"]:
        if role not in roles and role != "User":
            roles.append(role)
    return roles or ["User", "Admin"]


def extract_features(text: str, domain: str) -> list[str]:
    lower = text.lower()
    features: list[str] = []
    for pattern, name in FEATURE_PATTERNS:
        if re.search(pattern, lower) and name not in features:
            features.append(name)
    for feat in DOMAINS[domain]["features"]:
        if feat not in features:
            features.append(feat)
    # explicit "can <verb phrase>" extraction
    for match in re.finditer(r"\bcan\s+([a-z][a-z\s]{2,40}?)(?:[,.;]| and |\s+can\b|$)", lower):
        phrase = match.group(1).strip()
        if 3 <= len(phrase) <= 40:
            feat = phrase.capitalize()
            if not any(feat.lower() == f.lower() for f in features):
                features.append(feat)
    deduped: list[str] = []
    for feat in features:
        if feat not in deduped:
            deduped.append(feat)
    return deduped[:24]


def extract_entities(text: str, domain: str) -> list[str]:
    """Return entity names mentioned in the text, merged with domain defaults."""
    lower = text.lower()
    found: list[str] = []
    for kw, ename in sorted(_KEYWORD_INDEX.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"\b{re.escape(kw)}\b", lower):
            if ename not in found:
                found.append(ename)
                for comp in _COMPANIONS.get(ename, []):
                    if comp not in found:
                        found.append(comp)
    for ename in DOMAINS[domain]["entities"]:
        if ename not in found:
            found.append(ename)
    if "User" not in found:
        found.insert(0, "User")
    # order: User first, then by first appearance in text, then domain defaults
    order_fallback = {ename: idx for idx, ename in enumerate(found)}

    def position(ename: str) -> int:
        kws = ENTITY_CATALOG[ename]["keywords"]
        positions = [lower.find(kw) for kw in kws if lower.find(kw) >= 0]
        return min(positions) if positions else len(lower) + order_fallback[ename]

    found.sort(key=lambda e: (e != "User", position(e)))
    return found


def build_entity_schema(entity_names: list[str]) -> list[dict[str, Any]]:
    schema = []
    for name in entity_names:
        cat = ENTITY_CATALOG[name]
        schema.append({
            "name": name,
            "table": to_table_name(name),
            "description": cat["description"] or f"{name} entity",
            "fields": [dict(field) for field in cat["fields"]],
        })
    # wire back-references for relationships
    for ent in schema:
        for field in ent["fields"]:
            if field.get("type") == "fk":
                field["ref_table"] = to_table_name(field["ref"])
    return schema


# When a catalog entity's FK target is not part of the selected schema,
# remap it to the best available substitute (in priority order).
FK_REMAP: dict[tuple[str, str], list[str]] = {
    ("Payment", "order_id"): ["Order", "Booking", "Ticket", "Appointment",
                              "Enrollment", "Subscription", "Invoice"],
    ("Review", "product_id"): ["Product", "Course", "Listing", "Restaurant",
                               "Event", "MenuItem", "Property"],
}


def repair_references(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Guarantee referential completeness of the schema.

    Every FK must point at an entity that exists in the specification:
    remap known danglers to a domain-appropriate substitute, otherwise drop
    the FK constraint (keeping a plain integer column).
    """
    names = {e["name"] for e in entities}
    for ent in entities:
        for field in ent.get("fields", []):
            if field.get("type") != "fk" or not field.get("ref"):
                continue
            if field["ref"] in names:
                field["ref_table"] = to_table_name(field["ref"])
                continue
            targets = FK_REMAP.get((ent["name"], field["name"]), [])
            new_ref = next((t for t in targets if t in names), None)
            if new_ref is not None:
                field["ref"] = new_ref
                field["name"] = to_snake(new_ref) + "_id"
                field["ref_table"] = to_table_name(new_ref)
            else:
                field["type"] = "int"
                field.pop("ref", None)
                field.pop("ref_table", None)
    return entities


def to_table_name(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    if s.endswith(("s", "x", "ch", "sh")):
        return s + "es"
    if s.endswith("y") and len(s) > 1 and s[-2] not in "aeiou":
        return s[:-1] + "ies"
    return s + "s"


def to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def to_singular_table(table: str) -> str:
    return singularize(table)


def analyze_requirement(text: str, name: str | None = None) -> dict[str, Any]:
    """Turn a natural-language requirement into a structured specification."""
    domain = detect_domain(text)
    dom = DOMAINS[domain]
    entity_names = extract_entities(text, domain)
    schema = repair_references(build_entity_schema(entity_names))
    roles = extract_roles(text, domain)
    features = extract_features(text, domain)
    project_name = name or suggest_name(dom["app_type"])

    return {
        "name": project_name,
        "app_type": dom["app_type"],
        "domain": domain,
        "summary": text.strip(),
        "users": roles,
        "features": features,
        "entities": schema,
        "security": {
            "authentication": "JWT (email/password)",
            "authorization": "Role-Based Access Control",
            "roles": roles,
            "password_policy": {"min_length": 8, "require_number": True},
        },
        "non_functional": {
            "scalability": "horizontal (stateless API)",
            "availability": "99.9% target",
            "performance": "sub-300ms p95 API responses",
        },
    }


_NAME_PARTS = {
    "ecommerce": ("Shop", "Cart", "Mart"), "healthcare": ("Medi", "Care", "Health"),
    "rental": ("Stay", "Rent", "Nest"), "food_delivery": ("Food", "Meal", "Taste"),
    "blog": ("Blog", "Press", "Word"), "task_management": ("Task", "Flow", "Plan"),
    "learning": ("Learn", "Edu", "Skill"), "finance": ("Fin", "Budget", "Coin"),
    "chat": ("Chat", "Talk", "Ping"), "jobs": ("Job", "Hire", "Work"),
    "real_estate": ("Estate", "Home", "Land"), "events": ("Event", "Ticket", "Fest"),
    "fitness": ("Fit", "Gym", "Pulse"), "generic": ("App", "Web", "Base"),
}
_NAME_SUFFIX = ["ly", "Hub", "Flow", "Stack", "Forge", "Nest", "io", "ify"]


def suggest_name(app_type: str) -> str:
    for key, parts in _NAME_PARTS.items():
        if DOMAINS[key]["app_type"] == app_type:
            import hashlib
            idx = int(hashlib.md5(app_type.encode()).hexdigest(), 16)
            return f"{parts[idx % len(parts)]}{_NAME_SUFFIX[idx % len(_NAME_SUFFIX)]}"
    return "AppForge"


# ---------------------------------------------------------------------------
# Modification analysis ("Add a wishlist feature", "switch to Google login", ...)
# ---------------------------------------------------------------------------

def analyze_modification(instruction: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Classify a natural-language modification request and compute its impact."""
    lower = instruction.lower().strip()
    existing = {e["name"] for e in spec.get("entities", [])}

    # --- intent classification -------------------------------------------------
    if re.search(r"\b(remove|delete|drop)\b", lower):
        intent = "remove"
    elif re.search(r"\b(change|switch|replace|migrate|convert)\b", lower):
        intent = "change"
    elif re.search(r"\b(add|create|introduce|implement|include|support)\b", lower):
        intent = "add"
    else:
        intent = "add"

    result: dict[str, Any] = {
        "intent": intent,
        "instruction": instruction,
        "new_entities": [],
        "removed_entities": [],
        "new_features": [],
        "auth_change": None,
        "affected": {"database": [], "backend": [], "frontend": [], "testing": []},
    }

    # --- auth provider change ---------------------------------------------------
    if intent in ("change", "add") and re.search(
            r"\b(auth|login|sign[ -]?in)\b", lower) and re.search(
            r"\b(google|oauth|github|sso|social)\b", lower):
        provider = "google" if "google" in lower else (
            "github" if "github" in lower else "oauth")
        result["intent"] = "change"
        result["auth_change"] = {"provider": provider,
                                 "from": spec.get("security", {}).get("authentication", "JWT")}
        result["affected"]["backend"] += ["auth router", "security module", "config"]
        result["affected"]["frontend"] += ["Login page", "Register page", "Auth context"]
        result["affected"]["testing"] += ["auth tests"]
        result["affected"]["database"] += ["users table (oauth columns)"]
        return result

    # --- find the target noun phrase -------------------------------------------
    m = re.search(r"\b(?:add|create|introduce|implement|include|support|remove|delete|drop)\b"
                  r"\s+(?:a|an|the|new)?\s*([a-z][a-z\s\-]{1,40}?)\s*"
                  r"(?:feature|functionality|module|support|system|capability|to|for|from|\?|\.|$)",
                  lower)
    target = m.group(1).strip() if m else ""
    target = re.sub(r"\s+", " ", target)

    matched_entities: list[str] = []
    if target:
        words = target.split()
        # head-noun-first matching: the LAST word of an English noun phrase is
        # its head ("product coupons" -> coupons), so try it (and the two-word
        # phrase ending on it) before falling back to earlier words.
        candidates: list[str] = []
        if len(words) >= 2:
            candidates.append(" ".join(words[-2:]))
        candidates.append(words[-1])
        if singularize(words[-1]) != words[-1]:
            candidates.append(singularize(words[-1]))
        for phrase in candidates:
            if phrase in _KEYWORD_INDEX:
                matched_entities.append(_KEYWORD_INDEX[phrase])
                break

    if intent == "remove":
        for ename in matched_entities:
            if ename in existing and ename != "User":
                result["removed_entities"].append(ename)
                tbl = to_table_name(ename)
                result["affected"]["database"].append(f"{tbl} table")
                result["affected"]["backend"] += [f"{ename} model", f"{ename} API",
                                                  f"{ename} service"]
                result["affected"]["frontend"] += [f"{ename} pages", f"{ename} components"]
                result["affected"]["testing"] += [f"{ename} tests"]
        return result

    # default: add
    if matched_entities:
        for ename in matched_entities:
            if ename not in existing:
                result["new_entities"].append(ename)
                for comp in _COMPANIONS.get(ename, []):
                    if comp not in existing and comp not in result["new_entities"]:
                        result["new_entities"].append(comp)
        feature_name = " ".join(w.capitalize() for w in target.split())
        result["new_features"].append(feature_name)
    elif target:
        # derive a generic entity from the noun phrase
        noun = target.split()[-1]
        ename = title_name(singularize(noun))
        if ename and ename not in existing and len(ename) > 2:
            result["new_entities"].append(ename)
            result["generic_entity"] = ename
            result["new_features"].append(" ".join(w.capitalize() for w in target.split()))

    for ename in result["new_entities"]:
        tbl = to_table_name(ename)
        result["affected"]["database"].append(f"{tbl} table")
        result["affected"]["backend"] += [f"{ename} model", f"{ename} API", f"{ename} service"]
        result["affected"]["frontend"] += [f"{ename} page", f"{ename} components"]
        result["affected"]["testing"] += [f"{ename} tests"]

    if not result["new_entities"] and not result["removed_entities"]:
        # treat as a pure feature flag on existing entities
        result["new_features"].append(instruction.strip().rstrip(".").capitalize())
        result["affected"]["frontend"].append("feature UI")
        result["affected"]["backend"].append("feature endpoints")
        result["affected"]["testing"].append("feature tests")
    return result


def generic_entity_fields(name: str) -> list[dict[str, Any]]:
    """Sensible default fields for an entity we have no catalog entry for."""
    return [
        dict(ID_FIELD), f("owner_id", "fk", ref="User", ref_table="users"),
        f("name"), f("description", "text", nullable=True),
        f("status", default="active"), dict(CREATED),
    ]
