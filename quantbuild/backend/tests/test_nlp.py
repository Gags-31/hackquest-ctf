"""Requirement-understanding engine tests."""
from app.core import nlp


def test_ecommerce_requirement():
    spec = nlp.analyze_requirement(
        "Build an e-commerce platform where customers can browse products, "
        "add items to a cart, make payments and track their orders.")
    assert spec["app_type"] == "E-Commerce Platform"
    names = {e["name"] for e in spec["entities"]}
    assert {"User", "Product", "Cart", "Order", "Payment"} <= names
    assert "Customer" in spec["users"]
    assert any("cart" in f.lower() or "Cart" in f for f in spec["features"])


def test_healthcare_requirement():
    spec = nlp.analyze_requirement(
        "Create an online healthcare appointment platform where patients can "
        "register, search doctors, view available slots and book appointments.")
    assert spec["app_type"] == "Healthcare Appointment Platform"
    names = {e["name"] for e in spec["entities"]}
    assert {"User", "Doctor", "Patient", "Appointment"} <= names
    assert "Patient" in spec["users"] and "Doctor" in spec["users"]


def test_referential_integrity_is_repaired():
    """Payment without Order must be remapped (events domain) — no dangling FKs."""
    spec = nlp.analyze_requirement(
        "Build an event ticketing platform where organizers create events and "
        "attendees browse events, book tickets and pay online.")
    names = {e["name"] for e in spec["entities"]}
    for ent in spec["entities"]:
        for field in ent["fields"]:
            if field.get("type") == "fk":
                assert field["ref"] in names, f"dangling FK {ent['name']}.{field['name']}"


def test_companion_entities_added():
    spec = nlp.analyze_requirement("Build a shop with a cart and products.")
    names = {e["name"] for e in spec["entities"]}
    assert "CartItem" in names  # companion of Cart


def test_table_naming():
    assert nlp.to_table_name("Category") == "categories"
    assert nlp.to_table_name("OrderItem") == "order_items"
    assert nlp.to_table_name("Availability") == "availabilities"
    assert nlp.to_table_name("Task") == "tasks"


def test_modification_add_feature():
    spec = nlp.analyze_requirement("Build an e-commerce platform with products and a cart.")
    mod = nlp.analyze_modification("Add a wishlist feature", spec)
    assert mod["intent"] == "add"
    assert "Wishlist" in mod["new_entities"]
    assert "WishlistItem" in mod["new_entities"]
    assert mod["affected"]["database"] and mod["affected"]["backend"]


def test_modification_add_generic_entity():
    spec = nlp.analyze_requirement("Build an e-commerce platform with products.")
    mod = nlp.analyze_modification("Add product coupons", spec)
    assert mod["intent"] == "add"
    assert any(e == "Coupon" for e in mod["new_entities"])


def test_modification_remove():
    spec = nlp.analyze_requirement("Build a shop with products, cart and reviews.")
    mod = nlp.analyze_modification("Remove the reviews", spec)
    assert mod["intent"] == "remove"
    assert "Review" in mod["removed_entities"]


def test_modification_auth_change():
    spec = nlp.analyze_requirement("Build a shop with products.")
    mod = nlp.analyze_modification(
        "Change the login system from email/password to Google authentication", spec)
    assert mod["auth_change"]["provider"] == "google"
