#!/usr/bin/env python3

import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor


class ProductDatabaseCleaner:
    def __init__(self):
        self.connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", 5432),
            database=os.getenv("DB_NAME", "aioutlet_products"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
        )
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

    def clear_all_data(self):
        print("Clearing all product service data...")

        try:
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
            print("All product service data cleared successfully!")
        except Exception as error:
            print(f"Error clearing product data: {error}")
            self.connection.rollback()
            raise error

    def drop_all_tables(self):
        print("Dropping all product service tables...")

        try:
            drop_queries = [
                "DROP TABLE IF EXISTS products.review_votes CASCADE;",
                "DROP TABLE IF EXISTS products.reviews CASCADE;",
                "DROP TABLE IF EXISTS products.collection_products CASCADE;",
                "DROP TABLE IF EXISTS products.collections CASCADE;",
                "DROP TABLE IF EXISTS products.product_attributes CASCADE;",
                "DROP TABLE IF EXISTS products.attributes CASCADE;",
                "DROP TABLE IF EXISTS products.product_variants CASCADE;",
                "DROP TABLE IF EXISTS products.products CASCADE;",
                "DROP TABLE IF EXISTS products.vendors CASCADE;",
                "DROP TABLE IF EXISTS products.categories CASCADE;",
                "DROP SCHEMA IF EXISTS products CASCADE;",
            ]

            for query in drop_queries:
                self.cursor.execute(query)
                print(f"Executed: {query}")

            self.connection.commit()
            print("All product service tables dropped successfully!")
        except Exception as error:
            print(f"Error dropping product tables: {error}")
            self.connection.rollback()
            raise error

    def close(self):
        self.cursor.close()
        self.connection.close()


if __name__ == "__main__":
    cleaner = ProductDatabaseCleaner()
    operation = sys.argv[1] if len(sys.argv) > 1 else "clear"

    try:
        if operation == "drop":
            cleaner.drop_all_tables()
        else:
            cleaner.clear_all_data()

        print(f"Product database {operation} completed!")
    except Exception as error:
        print(f"Product database {operation} failed: {error}")
        exit(1)
    finally:
        cleaner.close()
