#!/usr/bin/env python3

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv


class ProductDatabaseCleaner:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB connection string from environment
        self.mongodb_uri = os.getenv("MONGODB_URI")
        self.db_name = os.getenv("DATABASE_NAME") or os.getenv("MONGODB_DB_NAME")
        
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI must be set in environment or .env file")
        
        if not self.db_name:
            raise ValueError("DATABASE_NAME or MONGODB_DB_NAME must be set in environment or .env file")
        
        self.client = None
        self.db = None

    async def connect(self):
        """Establish MongoDB connection"""
        print(f"Connecting to MongoDB database '{self.db_name}'...")
        self.client = AsyncIOMotorClient(self.mongodb_uri)
        self.db = self.client[self.db_name]
        
        # Test connection
        await self.db.command('ping')
        print("Successfully connected to MongoDB!")

    async def clear_all_data(self):
        """Clear all product service data"""
        print("Clearing all product service data...")

        try:
            collections = await self.db.list_collection_names()
            
            if not collections:
                print("No collections found in database")
                return
            
            for collection_name in collections:
                result = await self.db[collection_name].delete_many({})
                print(f"Deleted {result.deleted_count} documents from '{collection_name}' collection")

            print("All product service data cleared successfully!")
        except Exception as error:
            print(f"Error clearing product data: {error}")
            raise error

    async def drop_all_collections(self):
        """Drop all MongoDB collections"""
        print("Dropping all product service collections...")

        try:
            collections = await self.db.list_collection_names()
            
            if not collections:
                print("No collections found in database")
                return
            
            for collection_name in collections:
                await self.db[collection_name].drop()
                print(f"Dropped collection: {collection_name}")

            print("All product service collections dropped successfully!")
        except Exception as error:
            print(f"Error dropping product collections: {error}")
            raise error

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")


async def main():
    load_dotenv()
    cleaner = ProductDatabaseCleaner()
    operation = sys.argv[1] if len(sys.argv) > 1 else "clear"

    try:
        print("=" * 50)
        print("Product Service Database Cleaner")
        print("=" * 50)

        await cleaner.connect()

        if operation == "drop":
            await cleaner.drop_all_collections()
        else:
            await cleaner.clear_all_data()

        print("=" * 50)
        print(f"Product database {operation} completed!")
        print("=" * 50)
    except Exception as error:
        print(f"Product database {operation} failed: {error}")
        exit(1)
    finally:
        await cleaner.close()


if __name__ == "__main__":
    asyncio.run(main())
