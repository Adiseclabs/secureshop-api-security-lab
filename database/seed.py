"""
database/seed.py
------------------
Fake sample data for the local lab. Everything here is fictional -
no real names, emails, or business data.
"""

from database.db import db
from models.user import User
from models.product import Product
from models.order import Order


def seed_data():
    if User.query.first():
        return  # already seeded

    # --- Users (fake data only) ---
    admin = User(name="Ava Administrator", email="admin@secureshop.local", role="admin",
                 phone="555-0100", address="1 Fictional Ave, Sampleton")
    admin.set_password("AdminPass123")

    user1 = User(name="Jordan Rivera", email="jordan.rivera@secureshop.local", role="user",
                 phone="555-0101", address="12 Sample St, Fictionville")
    user1.set_password("UserPass123")

    user2 = User(name="Casey Morgan", email="casey.morgan@secureshop.local", role="user",
                 phone="555-0102", address="34 Example Rd, Placeholder City")
    user2.set_password("UserPass456")

    db.session.add_all([admin, user1, user2])
    db.session.commit()

    # --- Products (fake catalog) ---
    products = [
        Product(name="Wireless Mouse", description="Ergonomic 2.4GHz wireless mouse.",
                price=19.99, stock=150, sku="SS-MOU-001"),
        Product(name="Mechanical Keyboard", description="Tenkeyless mechanical keyboard, blue switches.",
                price=59.99, stock=80, sku="SS-KEY-002"),
        Product(name="USB-C Hub", description="7-in-1 USB-C hub with HDMI and card reader.",
                price=34.50, stock=120, sku="SS-HUB-003"),
        Product(name="Laptop Stand", description="Aluminum adjustable laptop stand.",
                price=27.00, stock=60, sku="SS-STA-004"),
        Product(name="Webcam 1080p", description="Full HD webcam with privacy shutter.",
                price=45.25, stock=40, sku="SS-CAM-005"),
        Product(name="Noise-Cancelling Headphones", description="Over-ear ANC headphones.",
                price=89.99, stock=25, sku="SS-AUD-006"),
    ]
    db.session.add_all(products)
    db.session.commit()

    # --- Sample orders belonging to different users ---
    order1 = Order(user_id=user1.id, product_id=products[0].id, quantity=2,
                    total_price=round(products[0].price * 2, 2), status="placed")
    order2 = Order(user_id=user2.id, product_id=products[1].id, quantity=1,
                    total_price=products[1].price, status="shipped")
    order3 = Order(user_id=user1.id, product_id=products[4].id, quantity=1,
                    total_price=products[4].price, status="delivered")

    db.session.add_all([order1, order2, order3])
    db.session.commit()

    print("Seed data created:")
    print("  Admin  -> admin@secureshop.local / AdminPass123")
    print("  User 1 -> jordan.rivera@secureshop.local / UserPass123")
    print("  User 2 -> casey.morgan@secureshop.local / UserPass456")
