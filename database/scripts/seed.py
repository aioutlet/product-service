#!/usr/bin/env python3

import json
import os

import psycopg2
from psycopg2.extras import RealDictCursor


class ProductDatabaseSeeder:
    def __init__(self):
        self.connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME", "aioutlet_products"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
        )
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def run_migrations(self):
        print("Running product service migrations...")

        migration_files = [
            "001_create_product_tables.sql",
            "002_add_product_extensions.sql",
        ]

        for file in migration_files:
            migration_path = os.path.join(
                os.path.dirname(__file__), "..", "migrations", file
            )
            with open(migration_path, "r") as f:
                migration = f.read()

            print(f"Running migration: {file}")
            self.cursor.execute(migration)
            self.connection.commit()

    def seed_data(self):
        print("Seeding product service data...")

        try:
            # Clear existing data
            self.clear_data()

            # Seed in correct order (respecting foreign keys)
            self.seed_categories()
            self.seed_vendors()
            self.seed_products()
            self.seed_reviews()

            print("Product service data seeding completed successfully!")
        except Exception as error:
            print(f"Error seeding product data: {error}")
            self.connection.rollback()
            raise error

    def clear_data(self):
        print("Clearing existing product data...")

        clear_queries = [
            "DELETE FROM products.review_votes;",
            "DELETE FROM products.reviews;",
            "DELETE FROM products.collection_products;",
            "DELETE FROM products.collections;",
            "DELETE FROM products.product_attributes;",
            "DELETE FROM products.attributes;",
            "DELETE FROM products.product_variants;",
            "DELETE FROM products.products;",
            "DELETE FROM products.vendors;",
            "DELETE FROM products.categories;",
        ]

        for query in clear_queries:
            self.cursor.execute(query)
            print(f"Executed: {query}")

        self.connection.commit()

    def seed_categories(self):
        categories_path = os.path.join(
            os.path.dirname(__file__), "..", "seeds", "categories.json"
        )
        with open(categories_path, "r") as f:
            categories = json.load(f)

        for category in categories:
            self.cursor.execute(
                """
                INSERT INTO products.categories (
                    id, name, slug, description, parent_id, image_url,
                    is_active, sort_order, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    category["id"],
                    category["name"],
                    category["slug"],
                    category["description"],
                    category["parent_id"],
                    category["image_url"],
                    category["is_active"],
                    category["sort_order"],
                    category["created_at"],
                    category["updated_at"],
                ),
            )

        self.connection.commit()
        print(f"Seeded {len(categories)} categories")

    def seed_vendors(self):
        vendors_path = os.path.join(
            os.path.dirname(__file__), "..", "seeds", "vendors.json"
        )
        with open(vendors_path, "r") as f:
            vendors = json.load(f)

        for vendor in vendors:
            self.cursor.execute(
                """
                INSERT INTO products.vendors (
                    id, name, slug, description, website_url, logo_url,
                    contact_email, contact_phone, address, is_verified,
                    is_active, rating, total_products, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    vendor["id"],
                    vendor["name"],
                    vendor["slug"],
                    vendor["description"],
                    vendor["website_url"],
                    vendor["logo_url"],
                    vendor["contact_email"],
                    vendor["contact_phone"],
                    json.dumps(vendor["address"]),
                    vendor["is_verified"],
                    vendor["is_active"],
                    vendor["rating"],
                    vendor["total_products"],
                    vendor["created_at"],
                    vendor["updated_at"],
                ),
            )

        self.connection.commit()
        print(f"Seeded {len(vendors)} vendors")

    def seed_products(self):
        products_path = os.path.join(
            os.path.dirname(__file__), "..", "seeds", "products.json"
        )
        with open(products_path, "r") as f:
            products = json.load(f)

        for product in products:
            self.cursor.execute(
                """
                INSERT INTO products.products (
                    id, name, slug, description, short_description, sku, barcode,
                    category_id, vendor_id, price, compare_price, cost_price,
                    currency, weight, dimensions, images, tags, status,
                    visibility, featured, digital, downloadable, track_inventory,
                    allow_backorders, requires_shipping, tax_class, meta_title,
                    meta_description, meta_keywords, rating, rating_count,
                    total_sales, view_count, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """,
                (
                    product["id"],
                    product["name"],
                    product["slug"],
                    product["description"],
                    product["short_description"],
                    product["sku"],
                    product["barcode"],
                    product["category_id"],
                    product["vendor_id"],
                    product["price"],
                    product["compare_price"],
                    product["cost_price"],
                    product["currency"],
                    product["weight"],
                    (
                        json.dumps(product["dimensions"])
                        if product["dimensions"]
                        else None
                    ),
                    product["images"],
                    product["tags"],
                    product["status"],
                    product["visibility"],
                    product["featured"],
                    product["digital"],
                    product["downloadable"],
                    product["track_inventory"],
                    product["allow_backorders"],
                    product["requires_shipping"],
                    product["tax_class"],
                    product["meta_title"],
                    product["meta_description"],
                    product["meta_keywords"],
                    product["rating"],
                    product["rating_count"],
                    product["total_sales"],
                    product["view_count"],
                    product["created_at"],
                    product["updated_at"],
                ),
            )

        self.connection.commit()
        print(f"Seeded {len(products)} products")

    def seed_reviews(self):
        reviews_path = os.path.join(
            os.path.dirname(__file__), "..", "seeds", "reviews.json"
        )
        with open(reviews_path, "r") as f:
            reviews = json.load(f)

        for review in reviews:
            self.cursor.execute(
                """
                INSERT INTO products.reviews (
                    id, product_id, user_id, rating, title, content, images,
                    is_verified_purchase, is_approved, helpful_count,
                    total_votes, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    review["id"],
                    review["product_id"],
                    review["user_id"],
                    review["rating"],
                    review["title"],
                    review["content"],
                    review["images"],
                    review["is_verified_purchase"],
                    review["is_approved"],
                    review["helpful_count"],
                    review["total_votes"],
                    review["created_at"],
                    review["updated_at"],
                ),
            )

        self.connection.commit()
        print(f"Seeded {len(reviews)} reviews")

    def close(self):
        self.cursor.close()
        self.connection.close()


if __name__ == "__main__":
    seeder = ProductDatabaseSeeder()

    try:
        seeder.run_migrations()
        seeder.seed_data()
        print("Product database setup completed!")
    except Exception as error:
        print(f"Product database setup failed: {error}")
        exit(1)
    finally:
        seeder.close()
