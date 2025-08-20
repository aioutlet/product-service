import csv
import io
import json
from datetime import datetime
from typing import List, Optional

from src.core.errors import ErrorResponse
from src.core.logger import logger
from src.models.product import ProductCreate, ProductDB, ProductUpdate

from .product_controller import delete_product, update_product


async def bulk_create_products(
    products: List[ProductCreate], collection, acting_user=None
):
    """
    Create multiple products in a single batch operation.

    Args:
        products: List of ProductCreate objects to be created
        collection: MongoDB collection instance
        acting_user: User performing the operation (must have admin role)

    Returns:
        List[ProductDB]: List of created product objects

    Raises:
        ErrorResponse: If user is not admin, SKUs are duplicated, or validation fails
    """
    # Validate admin permissions
    if not acting_user or "admin" not in acting_user.get("roles", []):
        raise ErrorResponse("Only admin users can create products.", status_code=403)

    # Check for duplicate SKUs in input
    skus = [p.sku for p in products if p.sku]
    if len(skus) != len(set(skus)):
        raise ErrorResponse("Duplicate SKUs in input.", status_code=400)

    # Check for existing SKUs in database
    existing = await collection.find({"sku": {"$in": skus}, "is_active": True}).to_list(
        length=None
    )
    if existing:
        existing_skus = [e["sku"] for e in existing]
        raise ErrorResponse(f"SKUs already exist: {existing_skus}", status_code=400)

    # Prepare documents for insertion
    docs = []
    for product in products:
        # Validate business rules
        if product.price < 0:
            raise ErrorResponse("Price must be non-negative.", status_code=400)

        # Transform and enrich product data
        data = product.dict()
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        data["is_active"] = True
        data["history"] = []
        docs.append(data)

    # Perform bulk insert
    result = await collection.insert_many(docs)

    # Retrieve inserted documents
    inserted = await collection.find({"_id": {"$in": result.inserted_ids}}).to_list(
        length=None
    )

    # Log successful operation
    logger.info(
        f"Bulk created {len(result.inserted_ids)} products",
        extra={"event": "bulk_create_products"},
    )

    return [ProductDB(**doc) for doc in inserted]


async def bulk_update_products(updates: List[dict], collection, acting_user=None):
    """
    Update multiple products in a single batch operation.

    Args:
        updates: List of dictionaries containing product ID and update data
        collection: MongoDB collection instance
        acting_user: User performing the operation (must have admin role)

    Returns:
        List[ProductDB]: List of successfully updated product objects

    Raises:
        ErrorResponse: If user is not admin

    Note:
        Individual update failures are logged but don't stop the batch operation
    """
    # Validate admin permissions
    if not acting_user or "admin" not in acting_user.get("roles", []):
        raise ErrorResponse("Only admin users can update products.", status_code=403)

    updated = []
    for upd in updates:
        # Extract product ID from update data
        product_id = upd.pop("id", None)
        if not product_id:
            continue

        # Create ProductUpdate object
        product = ProductUpdate(**upd)

        try:
            # Attempt to update individual product
            updated_product = await update_product(
                product_id, product, collection, acting_user
            )
            updated.append(updated_product)
        except ErrorResponse as e:
            # Log individual failures but continue processing
            logger.warning(f"Bulk update failed for {product_id}: {e.detail}")
            continue

    # Log successful operation
    logger.info(
        f"Bulk updated {len(updated)} products", extra={"event": "bulk_update_products"}
    )

    return updated


async def bulk_delete_products(ids: List[str], collection, acting_user=None):
    """
    Soft delete multiple products in a single batch operation.

    Args:
        ids: List of product IDs to be deleted
        collection: MongoDB collection instance
        acting_user: User performing the operation (must have admin role)

    Returns:
        dict: Dictionary containing count of deleted products

    Raises:
        ErrorResponse: If user is not admin

    Note:
        Individual delete failures are logged but don't stop the batch operation
    """
    # Validate admin permissions
    if not acting_user or "admin" not in acting_user.get("roles", []):
        raise ErrorResponse("Only admin users can delete products.", status_code=403)

    deleted = 0
    for product_id in ids:
        try:
            # Attempt to delete individual product (soft delete)
            await delete_product(product_id, collection, acting_user)
            deleted += 1
        except ErrorResponse as e:
            # Log individual failures but continue processing
            logger.warning(f"Bulk delete failed for {product_id}: {e.detail}")
            continue

    # Log successful operation
    logger.info(
        f"Bulk soft deleted {deleted} products", extra={"event": "bulk_delete_products"}
    )

    return {"deleted": deleted}


async def import_products(file_content: bytes, filetype: str, collection):
    """
    Import products from uploaded file (CSV or JSON format).

    Args:
        file_content: Raw file content as bytes
        filetype: File format ("csv" or "json")
        collection: MongoDB collection instance

    Returns:
        List[ProductDB]: List of imported product objects

    Raises:
        ErrorResponse: If file type is unsupported or file parsing fails
    """
    # Parse file content based on type
    if filetype == "csv":
        # Parse CSV file content
        f = io.StringIO(file_content.decode())
        reader = csv.DictReader(f)
        products = [ProductCreate(**row) for row in reader]
    elif filetype == "json":
        # Parse JSON file content
        data = json.loads(file_content)
        products = [ProductCreate(**item) for item in data]
    else:
        raise ErrorResponse("Unsupported file type", status_code=400)

    # Use bulk create to import products
    return await bulk_create_products(products, collection)


async def export_products(
    collection, filetype: str = "json", filters: Optional[dict] = None
):
    """
    Export products to specified format with optional filtering.

    Args:
        collection: MongoDB collection instance
        filetype: Export format ("csv" or "json")
        filters: Optional MongoDB query filters

    Returns:
        str: Exported data as string in requested format

    Raises:
        ErrorResponse: If file type is unsupported
    """
    # Apply filters or default to active products only
    query = filters or {"is_active": True}

    # Retrieve products from database
    products = await collection.find(query).to_list(length=None)

    # Format output based on requested type
    if filetype == "csv":
        # Handle empty result set
        if not products:
            return ""

        # Generate CSV output
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=products[0].keys())
        writer.writeheader()
        for prod in products:
            writer.writerow(prod)
        return output.getvalue()
    elif filetype == "json":
        # Generate JSON output with datetime serialization
        return json.dumps(products, default=str)
    else:
        raise ErrorResponse("Unsupported file type", status_code=400)
