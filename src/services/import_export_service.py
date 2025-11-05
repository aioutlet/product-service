"""
Import/Export Service - Handles product data import and export.

This service manages importing products from CSV/JSON files
and exporting product data to various formats.
"""

import csv
import json
import io
from typing import List, Optional
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from src.repositories.product_repository import ProductRepository
from src.core.logger import logger
from src.core.errors import ErrorResponse
from src.models.product import ProductDB
from src.dependencies.auth import CurrentUser


class ImportExportService:
    """Service for product import/export operations."""
    
    def __init__(self, repository: ProductRepository):
        """
        Initialize import/export service.
        
        Args:
            repository: Product repository for data access
        """
        self.repository = repository
    
    async def import_products(
        self,
        content: str,
        filetype: str,
        acting_user: Optional[CurrentUser] = None,
        correlation_id: Optional[str] = None
    ) -> List[ProductDB]:
        """
        Import products from CSV or JSON file.
        
        Args:
            content: File content as string
            filetype: File type ('csv' or 'json')
            acting_user: User performing operation
            correlation_id: Request correlation ID
            
        Returns:
            List of imported products
            
        Raises:
            ErrorResponse: If validation fails or format is invalid
        """
        if not acting_user or not acting_user.has_role("admin"):
            raise ErrorResponse("Only admin users can import products.", status_code=403)
        
        imported = []
        
        if filetype == "csv":
            # Parse CSV
            try:
                reader = csv.DictReader(io.StringIO(content))
                for row in reader:
                    # Check for duplicate SKU
                    if row.get("sku"):
                        existing = await self.repository.find_by_sku(row["sku"])
                        if existing:
                            logger.warning(
                                f"Skipping duplicate SKU: {row['sku']}",
                                correlation_id=correlation_id
                            )
                            continue
                    
                    # Build product document
                    doc = {
                        "name": row.get("name"),
                        "description": row.get("description", ""),
                        "price": float(row.get("price", 0)),
                        "category": row.get("category"),
                        "brand": row.get("brand", ""),
                        "sku": row.get("sku"),
                        "tags": row.get("tags", "").split(",") if row.get("tags") else [],
                        "images": row.get("images", "").split(",") if row.get("images") else [],
                        "attributes": json.loads(row.get("attributes", "{}")),
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                        "is_active": True,
                        "history": [],
                        "created_by": acting_user.user_id if acting_user else None
                    }
                    
                    # Insert product
                    result = await self.repository.collection.insert_one(doc)
                    doc["_id"] = result.inserted_id
                    imported.append(ProductDB(**doc))
            
            except UnicodeDecodeError:
                raise ErrorResponse("Invalid CSV encoding.", status_code=400)
            except ValueError as e:
                raise ErrorResponse(f"Invalid CSV data: {str(e)}", status_code=400)
            except PyMongoError as e:
                logger.error(f"Database error during import: {str(e)}", correlation_id=correlation_id)
                raise ErrorResponse("Import failed.", status_code=500)
        
        elif filetype == "json":
            # Parse JSON
            try:
                products = json.loads(content)
                if not isinstance(products, list):
                    raise ErrorResponse("JSON must be an array.", status_code=400)
                
                for product_data in products:
                    # Check for duplicate SKU
                    if product_data.get("sku"):
                        existing = await self.repository.find_by_sku(product_data["sku"])
                        if existing:
                            logger.warning(
                                f"Skipping duplicate SKU: {product_data['sku']}",
                                correlation_id=correlation_id
                            )
                            continue
                    
                    # Build product document
                    doc = {
                        "name": product_data.get("name"),
                        "description": product_data.get("description", ""),
                        "price": float(product_data.get("price", 0)),
                        "category": product_data.get("category"),
                        "brand": product_data.get("brand", ""),
                        "sku": product_data.get("sku"),
                        "tags": product_data.get("tags", []),
                        "images": product_data.get("images", []),
                        "attributes": product_data.get("attributes", {}),
                        "created_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc),
                        "is_active": True,
                        "history": [],
                        "created_by": acting_user.user_id if acting_user else None
                    }
                    
                    # Insert product
                    result = await self.repository.collection.insert_one(doc)
                    doc["_id"] = result.inserted_id
                    imported.append(ProductDB(**doc))
            
            except json.JSONDecodeError:
                raise ErrorResponse("Invalid JSON format.", status_code=400)
            except ValueError as e:
                raise ErrorResponse(f"Invalid JSON data: {str(e)}", status_code=400)
            except PyMongoError as e:
                logger.error(f"Database error during import: {str(e)}", correlation_id=correlation_id)
                raise ErrorResponse("Import failed.", status_code=500)
        
        else:
            raise ErrorResponse(f"Unsupported file type: {filetype}", status_code=400)
        
        logger.info(
            f"Imported {len(imported)} products from {filetype}",
            correlation_id=correlation_id,
            metadata={"count": len(imported), "filetype": filetype}
        )
        
        return imported
    
    async def export_products(
        self,
        filetype: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Export all active products to CSV or JSON format.
        
        Args:
            filetype: Export format ('csv' or 'json')
            correlation_id: Request correlation ID
            
        Returns:
            Exported data as string
            
        Raises:
            ErrorResponse: If format is unsupported
        """
        # Fetch all active products
        products = await self.repository.collection.find(
            {"is_active": True}
        ).to_list(length=None)
        
        if filetype == "json":
            # JSON export
            output = []
            for doc in products:
                # Convert datetime to ISO string
                doc["created_at"] = doc["created_at"].isoformat() if doc.get("created_at") else None
                doc["updated_at"] = doc["updated_at"].isoformat() if doc.get("updated_at") else None
                # Convert ObjectId to string
                doc["_id"] = str(doc["_id"])
                output.append(doc)
            
            result = json.dumps(output, indent=2)
            
            logger.info(
                f"Exported {len(products)} products to JSON",
                correlation_id=correlation_id,
                metadata={"count": len(products)}
            )
            
            return result
        
        elif filetype == "csv":
            # CSV export
            output = io.StringIO()
            
            if products:
                # Define CSV columns
                fieldnames = [
                    "_id", "name", "description", "price", "category", "brand",
                    "sku", "tags", "images", "attributes", "created_at", "updated_at"
                ]
                
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for doc in products:
                    # Convert complex fields to strings
                    row = {
                        "_id": str(doc["_id"]),
                        "name": doc.get("name", ""),
                        "description": doc.get("description", ""),
                        "price": doc.get("price", 0),
                        "category": doc.get("category", ""),
                        "brand": doc.get("brand", ""),
                        "sku": doc.get("sku", ""),
                        "tags": ",".join(doc.get("tags", [])),
                        "images": ",".join(doc.get("images", [])),
                        "attributes": json.dumps(doc.get("attributes", {})),
                        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else "",
                        "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else ""
                    }
                    writer.writerow(row)
            
            result = output.getvalue()
            
            logger.info(
                f"Exported {len(products)} products to CSV",
                correlation_id=correlation_id,
                metadata={"count": len(products)}
            )
            
            return result
        
        else:
            raise ErrorResponse(f"Unsupported file type: {filetype}", status_code=400)
    
    async def export_products_filtered(
        self,
        filters: dict,
        filetype: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Export filtered products to CSV or JSON format.
        
        Args:
            filters: MongoDB query filters
            filetype: Export format ('csv' or 'json')
            correlation_id: Request correlation ID
            
        Returns:
            Exported data as string
        """
        # Fetch filtered products
        products = await self.repository.collection.find(filters).to_list(length=None)
        
        if filetype == "json":
            output = []
            for doc in products:
                doc["created_at"] = doc["created_at"].isoformat() if doc.get("created_at") else None
                doc["updated_at"] = doc["updated_at"].isoformat() if doc.get("updated_at") else None
                doc["_id"] = str(doc["_id"])
                output.append(doc)
            
            result = json.dumps(output, indent=2)
            logger.info(
                f"Exported {len(products)} filtered products to JSON",
                correlation_id=correlation_id,
                metadata={"count": len(products)}
            )
            return result
        
        elif filetype == "csv":
            output = io.StringIO()
            
            if products:
                fieldnames = [
                    "_id", "name", "description", "price", "category", "brand",
                    "sku", "tags", "images", "attributes", "created_at", "updated_at"
                ]
                
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for doc in products:
                    row = {
                        "_id": str(doc["_id"]),
                        "name": doc.get("name", ""),
                        "description": doc.get("description", ""),
                        "price": doc.get("price", 0),
                        "category": doc.get("category", ""),
                        "brand": doc.get("brand", ""),
                        "sku": doc.get("sku", ""),
                        "tags": ",".join(doc.get("tags", [])),
                        "images": ",".join(doc.get("images", [])),
                        "attributes": json.dumps(doc.get("attributes", {})),
                        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else "",
                        "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else ""
                    }
                    writer.writerow(row)
            
            result = output.getvalue()
            logger.info(
                f"Exported {len(products)} filtered products to CSV",
                correlation_id=correlation_id,
                metadata={"count": len(products)}
            )
            return result
        
        else:
            raise ErrorResponse(f"Unsupported file type: {filetype}", status_code=400)
