import csv
import io
import json
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from src.core.errors import ErrorResponse
from src.core.logger import logger
from src.models.product import ProductDB


async def import_products(content: bytes, filetype: str, collection, acting_user=None):
    """
    Import products from CSV or JSON file content.

    Args:
        content: File content as bytes
        filetype: File format ("csv" or "json")
        collection: MongoDB collection instance
        acting_user: User performing the import (optional)

    Returns:
        List[ProductDB]: List of successfully imported products

    Raises:
        ErrorResponse: If file type unsupported, format invalid, or database error
    """
    try:
        # Validate file type
        if filetype not in ["csv", "json"]:
            raise ErrorResponse(
                "Unsupported file type. Only CSV and JSON are supported.",
                status_code=400,
            )

        products_data = []

        if filetype == "csv":
            # Parse CSV content
            content_str = content.decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(content_str))

            for row in csv_reader:
                # Convert CSV row to product data
                product_data = {
                    "name": row.get("name", "").strip(),
                    "description": row.get("description", "").strip(),
                    "price": float(row.get("price", 0)),
                    # Inventory management is handled by inventory-service
                    "category": row.get("category", "").strip(),
                    "brand": row.get("brand", "").strip(),
                    "sku": row.get("sku", "").strip(),
                    "tags": [
                        tag.strip()
                        for tag in row.get("tags", "").split(",")
                        if tag.strip()
                    ],
                    "images": [
                        img.strip()
                        for img in row.get("images", "").split(",")
                        if img.strip()
                    ],
                    "attributes": (
                        json.loads(row.get("attributes", "{}"))
                        if row.get("attributes")
                        else {}
                    ),
                }

                # Validate required fields and business rules
                if not product_data["name"] or product_data["price"] < 0:
                    logger.warning(
                        f"Invalid product data in CSV: {product_data}",
                        metadata={"event": "import_validation_error"},
                    )
                    continue

                products_data.append(product_data)

        elif filetype == "json":
            # Parse JSON content
            content_str = content.decode("utf-8")
            json_data = json.loads(content_str)

            # Validate JSON structure
            if isinstance(json_data, list):
                products_data = json_data
            else:
                raise ErrorResponse(
                    "JSON file must contain an array of products.", status_code=400
                )

        # Validate we have products to import
        if not products_data:
            raise ErrorResponse("No valid products found in the file.", status_code=400)

        # Import products to database
        imported_products = []
        for product_data in products_data:
            try:
                # Check for duplicate SKU
                if product_data.get("sku"):
                    existing = await collection.find_one(
                        {"sku": product_data["sku"], "is_active": True}
                    )
                    if existing:
                        logger.warning(
                            f"Skipping duplicate SKU: {product_data['sku']}",
                            metadata={"event": "duplicate_sku_import"},
                        )
                        continue

                # Add metadata and defaults
                product_data["created_at"] = datetime.now(timezone.utc)
                product_data["updated_at"] = datetime.now(timezone.utc)
                product_data["is_active"] = True
                product_data["history"] = []
                product_data["created_by"] = (
                    acting_user["user_id"] if acting_user else "system"
                )
                product_data["variants"] = product_data.get("variants", [])

                # Insert product into database
                result = await collection.insert_one(product_data)
                doc = await collection.find_one({"_id": result.inserted_id})
                imported_products.append(product_doc_to_model(doc))

            except Exception as e:
                logger.error(
                    f"Error importing product: {e}",
                    metadata={"event": "import_product_error", "product": product_data},
                )
                continue

        # Log successful import
        logger.info(
            f"Imported {len(imported_products)} products",
            metadata={"event": "import_products", "count": len(imported_products)}
        )
        return imported_products

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}", metadata={"event": "json_parse_error"})
        raise ErrorResponse("Invalid JSON format in file.", status_code=400)
    except UnicodeDecodeError as e:
        logger.error(f"File encoding error: {e}", metadata={"event": "encoding_error"})
        raise ErrorResponse(
            "File encoding error. Please ensure the file is UTF-8 encoded.",
            status_code=400,
        )
    except PyMongoError as e:
        logger.error(
            f"MongoDB error during import: {e}", metadata={"event": "mongodb_error"}
        )
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def export_products(collection, filetype: str = "json"):
    """
    Export products in JSON or CSV format.

    Args:
        collection: MongoDB collection instance
        filetype: Export format ("json" or "csv")

    Returns:
        str: Exported product data as formatted string

    Raises:
        ErrorResponse: If file type unsupported or database error
    """
    try:
        # Validate export format
        if filetype not in ["csv", "json"]:
            raise ErrorResponse(
                "Unsupported export type. Only CSV and JSON are supported.",
                status_code=400,
            )

        # Fetch all active products from database
        cursor = collection.find({"is_active": True})
        products = []

        try:
            async for doc in cursor:
                products.append(doc)
        except Exception as e:
            logger.error(
                f"Error fetching products from database: {e}",
                metadata={"event": "export_fetch_error"},
            )
            raise ErrorResponse(
                "Error fetching products from database.", status_code=500
            )

        logger.info(
            f"Found {len(products)} products to export",
            metadata={"event": "export_products_found", "count": len(products)},
        )

        if filetype == "json":
            # Convert to JSON format with proper serialization
            try:
                for product in products:
                    # Convert ObjectId to string for JSON serialization
                    product["_id"] = str(product["_id"])

                    # Handle datetime objects properly
                    if isinstance(product.get("created_at"), datetime):
                        product["created_at"] = product["created_at"].isoformat()
                    else:
                        product["created_at"] = product.get(
                            "created_at", datetime.now(timezone.utc)
                        ).isoformat()

                    if isinstance(product.get("updated_at"), datetime):
                        product["updated_at"] = product["updated_at"].isoformat()
                    else:
                        product["updated_at"] = product.get(
                            "updated_at", datetime.now(timezone.utc)
                        ).isoformat()

                    # Handle datetime objects in history
                    if "history" in product and isinstance(product["history"], list):
                        for history_entry in product["history"]:
                            if isinstance(history_entry.get("updated_at"), datetime):
                                history_entry["updated_at"] = history_entry[
                                    "updated_at"
                                ].isoformat()

                return json.dumps(products, indent=2)
            except Exception as e:
                logger.error(
                    f"Error converting products to JSON: {e}",
                    metadata={"event": "export_json_error"},
                )
                raise ErrorResponse(
                    "Error formatting products as JSON.", status_code=500
                )

        elif filetype == "csv":
            # Create CSV content
            output = io.StringIO()
            try:
                if products:
                    # Define CSV headers (inventory handled by inventory-service)
                    headers = [
                        "id",
                        "name",
                        "description",
                        "price",
                        "category",
                        "brand",
                        "sku",
                        "tags",
                        "images",
                        "attributes",
                        "created_by",
                        "created_at",
                        "updated_at",
                    ]

                    writer = csv.DictWriter(output, fieldnames=headers)
                    writer.writeheader()

                    # Convert each product to CSV row
                    for product in products:
                        try:
                            row = {
                                "id": str(product["_id"]),
                                "name": product.get("name", ""),
                                "description": product.get("description", ""),
                                "price": product.get("price", 0),
                                # Inventory management handled by inventory-service
                                "category": product.get("category", ""),
                                "brand": product.get("brand", ""),
                                "sku": product.get("sku", ""),
                                "tags": ",".join(product.get("tags", [])),
                                "images": ",".join(product.get("images", [])),
                                "attributes": json.dumps(product.get("attributes", {})),
                                "created_by": product.get("created_by", ""),
                                "created_at": (
                                    product.get("created_at").isoformat()
                                    if isinstance(product.get("created_at"), datetime)
                                    else str(product.get("created_at", ""))
                                ),
                                "updated_at": (
                                    product.get("updated_at").isoformat()
                                    if isinstance(product.get("updated_at"), datetime)
                                    else str(product.get("updated_at", ""))
                                ),
                            }
                            writer.writerow(row)
                        except Exception as e:
                            logger.error(
                                f"Error processing product for CSV: {e}",
                                metadata={
                                    "event": "export_csv_product_error",
                                    "product_id": str(product.get("_id", "unknown")),
                                },
                            )
                            continue

                return output.getvalue()
            except Exception as e:
                logger.error(
                    f"Error creating CSV content: {e}",
                    metadata={"event": "export_csv_error"},
                )
                raise ErrorResponse(
                    "Error formatting products as CSV.", status_code=500
                )

        # Log successful export
        logger.info(
            f"Exported {len(products)} products as {filetype}",
            metadata={
                "event": "export_products",
                "count": len(products),
                "format": filetype,
            },
        )

    except ErrorResponse:
        # Re-raise our custom errors
        raise
    except PyMongoError as e:
        logger.error(
            f"MongoDB error during export: {e}", metadata={"event": "mongodb_error"}
        )
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )
    except Exception as e:
        logger.error(
            f"Unexpected error during export: {e}",
            metadata={"event": "export_unexpected_error"},
        )
        raise ErrorResponse(
            "An unexpected error occurred during export.", status_code=500
        )


def product_doc_to_model(doc):
    """
    Convert MongoDB document to ProductDB model.

    Args:
        doc: MongoDB document dictionary

    Returns:
        ProductDB: Product model object with all fields populated
    """
    return ProductDB(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description"),
        price=doc["price"],
        brand=doc.get("brand"),
        sku=doc.get("sku"),
        # Hierarchical taxonomy fields
        department=doc.get("department"),
        category=doc.get("category"),
        subcategory=doc.get("subcategory"),
        product_type=doc.get("productType"),
        # Media and metadata
        images=doc.get("images", []),
        tags=doc.get("tags", []),
        # Product variations
        colors=doc.get("colors", []),
        sizes=doc.get("sizes", []),
        # Product specifications
        specifications=doc.get("specifications", {}),
        # Audit trail
        created_by=doc.get("created_by", "system"),
        updated_by=doc.get("updated_by"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
        is_active=doc.get("is_active", True),
        history=doc.get("history", []),
    )
