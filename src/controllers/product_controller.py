from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from src.core.auth import require_admin_user
from src.core.errors import ErrorResponse
from src.core.logger import logger
from src.models.product import ProductCreate, ProductDB, ProductUpdate
from src.utils.validators import validate_object_id


async def search_products(
    collection,
    search_text,
    category=None,
    min_price=None,
    max_price=None,
    tags=None,
    skip=0,
    limit=20,
):
    """
    Search products by text in name and description fields.
    Supports additional filtering by category, price range, and tags.

    Args:
        collection: MongoDB collection instance
        search_text: Text to search for in name, description, tags, and brand
        category: Optional category filter (case-insensitive)
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        tags: Optional list of tags to filter by
        skip: Number of results to skip for pagination
        limit: Maximum number of results to return

    Returns:
        dict: Search results with products, pagination info, and total count

    Raises:
        ErrorResponse: If search text is empty or database error occurs
    """
    try:
        # Validate search text
        if not search_text or not search_text.strip():
            logger.warning(
                "Empty search text provided", extra={"event": "search_products_empty"}
            )
            raise ErrorResponse("Search text cannot be empty", status_code=400)

        # Build the search query for active products only
        query = {"is_active": True}

        # Text search using regex for name and description
        search_pattern = {
            "$regex": search_text.strip(),
            "$options": "i",
        }  # Case-insensitive
        query["$or"] = [
            {"name": search_pattern},
            {"description": search_pattern},
            {"tags": search_pattern},  # Also search in tags
            {"brand": search_pattern},  # Also search in brand
        ]

        # Add additional filters
        if category:
            query["category"] = {
                "$regex": f"^{category}$",
                "$options": "i",
            }  # Case-insensitive category match
        if min_price is not None or max_price is not None:
            price_query = {}
            if min_price is not None:
                price_query["$gte"] = min_price
            if max_price is not None:
                price_query["$lte"] = max_price
            query["price"] = price_query
        if tags:
            query["tags"] = {"$in": tags}

        # Execute search with pagination
        cursor = collection.find(query).skip(skip).limit(limit)
        products = [product_doc_to_model(doc) async for doc in cursor]

        # Get total count for pagination info
        total_count = await collection.count_documents(query)

        return {
            "products": products,
            "total_count": total_count,
            "current_page": (skip // limit) + 1 if limit > 0 else 1,
            "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
        }

    except PyMongoError as e:
        logger.error(
            f"MongoDB error during search: {e}",
            extra={"event": "mongodb_error", "search_text": search_text},
        )
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def list_products(
    collection,
    category=None,
    min_price=None,
    max_price=None,
    tags=None,
    skip=0,
    limit=20,
):
    """
    List products with optional filtering and pagination.

    Args:
        collection: MongoDB collection instance
        category: Optional category filter (case-insensitive)
        min_price: Optional minimum price filter
        max_price: Optional maximum price filter
        tags: Optional list of tags to filter by
        skip: Number of results to skip for pagination
        limit: Maximum number of results to return

    Returns:
        dict: Product list with pagination info and total count

    Raises:
        ErrorResponse: If database error occurs
    """
    try:
        # Build query for active products only
        query = {"is_active": True}

        # Apply optional filters
        if category:
            query["category"] = {
                "$regex": f"^{category}$",
                "$options": "i",
            }  # Case-insensitive category match
        if min_price is not None or max_price is not None:
            price_query = {}
            if min_price is not None:
                price_query["$gte"] = min_price
            if max_price is not None:
                price_query["$lte"] = max_price
            query["price"] = price_query
        if tags:
            query["tags"] = {"$in": tags}

        # Execute query with pagination
        cursor = collection.find(query).skip(skip).limit(limit)
        products = [product_doc_to_model(doc) async for doc in cursor]

        # Get total count for pagination info
        total_count = await collection.count_documents(query)

        return {
            "products": products,
            "total_count": total_count,
            "current_page": (skip // limit) + 1 if limit > 0 else 1,
            "total_pages": (total_count + limit - 1) // limit if limit > 0 else 1,
        }

    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}", extra={"event": "mongodb_error"})
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def get_product(product_id, collection):
    """
    Retrieve a single product by ID.

    Args:
        product_id: Product ID (string representation of ObjectId)
        collection: MongoDB collection instance

    Returns:
        ProductDB: Product object if found

    Raises:
        ErrorResponse: If product not found or invalid ID format
    """
    try:
        # Validate and convert product ID to ObjectId
        obj_id = validate_object_id(product_id)

        # Find product in database
        doc = await collection.find_one({"_id": obj_id})
        if not doc:
            logger.warning(
                f"Product not found: {product_id}",
                extra={"event": "get_product", "product_id": product_id},
            )
            raise ErrorResponse("Product not found", status_code=404)

        # Log successful retrieval
        logger.info(
            f"Fetched product {product_id}",
            extra={"event": "get_product", "product_id": product_id},
        )
        return product_doc_to_model(doc)
    except (PyMongoError, ValueError) as e:
        logger.error(
            f"Error fetching product: {e}",
            extra={"event": "get_product_error", "product_id": product_id},
        )
        raise ErrorResponse("Invalid product ID or database error.", status_code=400)


async def create_product(product: ProductCreate, collection, acting_user=None):
    """
    Create a new product in the database.

    Args:
        product: ProductCreate object containing product data
        collection: MongoDB collection instance
        acting_user: User performing the operation (must have admin role)

    Returns:
        ProductDB: Created product object

    Raises:
        ErrorResponse: If user is not admin, SKU already exists, or validation fails
    """
    try:
        # Validate admin permissions
        require_admin_user(acting_user)

        # Prevent duplicate SKU
        if product.sku:
            existing = await collection.find_one(
                {"sku": product.sku, "is_active": True}
            )
            if existing:
                logger.warning(
                    f"Duplicate SKU: {product.sku}",
                    extra={"event": "duplicate_sku", "sku": product.sku},
                )
                raise ErrorResponse(
                    "A product with this SKU already exists.", status_code=400
                )

        # Validate business rules
        if product.price < 0:
            raise ErrorResponse("Price must be non-negative.", status_code=400)

        # Prepare product data for insertion
        data = product.dict()
        data["created_at"] = datetime.now(timezone.utc)
        data["updated_at"] = datetime.now(timezone.utc)
        data["is_active"] = True
        data["history"] = []

        # Insert product into database
        result = await collection.insert_one(data)

        # Retrieve and return created product
        doc = await collection.find_one({"_id": result.inserted_id})
        logger.info(
            f"Created product {result.inserted_id}",
            extra={"event": "create_product", "product_id": str(result.inserted_id)},
        )
        return product_doc_to_model(doc)
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}", extra={"event": "mongodb_error"})
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def update_product(
    product_id, product: ProductUpdate, collection, acting_user=None
):
    """
    Update an existing product with change tracking.

    Args:
        product_id: Product ID to update
        product: ProductUpdate object containing fields to update
        collection: MongoDB collection instance
        acting_user: User performing the operation (must have admin role)

    Returns:
        ProductDB: Updated product object

    Raises:
        ErrorResponse: If user is not admin, product not found, or validation fails
    """
    try:
        # Validate admin permissions
        require_admin_user(acting_user)

        # Validate and convert product ID
        obj_id = validate_object_id(product_id)

        # Extract only fields that were actually set
        update_data = {k: v for k, v in product.dict(exclude_unset=True).items()}
        if not update_data:
            logger.warning(
                "No fields to update",
                extra={"event": "update_product", "product_id": product_id},
            )
            raise ErrorResponse("No fields to update", status_code=400)

        # Validate business rules
        if "price" in update_data and update_data["price"] < 0:
            raise ErrorResponse("Price must be non-negative.", status_code=400)
        # Inventory management is handled by inventory-service

        # Prevent duplicate SKU
        if "sku" in update_data:
            existing = await collection.find_one(
                {"sku": update_data["sku"], "_id": {"$ne": obj_id}, "is_active": True}
            )
            if existing:
                logger.warning(
                    f"Duplicate SKU: {update_data['sku']}",
                    extra={"event": "duplicate_sku", "sku": update_data["sku"]},
                )
                raise ErrorResponse(
                    "A product with this SKU already exists.", status_code=400
                )

        # Get current product for change tracking
        doc = await collection.find_one({"_id": obj_id})
        if not doc:
            raise ErrorResponse("Product not found", status_code=404)

        # Track history of changes
        changes = {k: v for k, v in update_data.items() if k in doc and doc[k] != v}
        if changes and acting_user:
            history_entry = {
                "updated_by": acting_user["user_id"],
                "updated_at": datetime.now(timezone.utc),
                "changes": changes,
            }
            update_data.setdefault("history", doc.get("history", [])).append(
                history_entry
            )

        # Add update timestamp
        update_data["updated_at"] = datetime.now(timezone.utc)

        # Perform update
        result = await collection.update_one({"_id": obj_id}, {"$set": update_data})
        if result.matched_count == 0:
            logger.warning(
                f"Product not found: {product_id}",
                extra={"event": "update_product", "product_id": product_id},
            )
            raise ErrorResponse("Product not found", status_code=404)

        # Retrieve and return updated product
        doc = await collection.find_one({"_id": obj_id})
        logger.info(
            f"Updated product {product_id}",
            extra={"event": "update_product", "product_id": product_id},
        )
        return product_doc_to_model(doc)
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}", extra={"event": "mongodb_error"})
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def delete_product(product_id, collection, acting_user=None):
    """
    Soft delete a product (set is_active to False).

    Args:
        product_id: Product ID to delete
        collection: MongoDB collection instance
        acting_user: User performing the operation (must have admin role)

    Returns:
        None

    Raises:
        ErrorResponse: If user is not admin or product not found
    """
    try:
        # Validate admin permissions
        require_admin_user(acting_user)

        # Validate and convert product ID
        obj_id = validate_object_id(product_id)

        # Check if product exists
        doc = await collection.find_one({"_id": obj_id})
        if not doc:
            raise ErrorResponse("Product not found", status_code=404)

        # Perform soft delete
        result = await collection.update_one(
            {"_id": obj_id},
            {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
        )

        if result.matched_count == 0:
            raise ErrorResponse("Product not found", status_code=404)

        # Log successful deletion
        logger.info(
            f"Soft deleted product {product_id}",
            extra={"event": "soft_delete_product", "product_id": product_id},
        )
        return None
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}", extra={"event": "mongodb_error"})
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def reactivate_product(product_id, collection, acting_user=None):
    """
    Reactivate a soft-deleted product with SKU validation.

    Args:
        product_id: Product ID to reactivate
        collection: MongoDB collection instance
        acting_user: User performing the operation (must have admin role)

    Returns:
        ProductDB: Reactivated product object

    Raises:
        ErrorResponse: If user is not admin, product not found, already
                      active, or SKU conflict
    """
    try:
        # Validate admin permissions
        require_admin_user(acting_user)

        # Validate and convert product ID
        obj_id = validate_object_id(product_id)

        # Find the product (including inactive ones)
        doc = await collection.find_one({"_id": obj_id})
        if not doc:
            logger.warning(
                f"Product not found: {product_id}",
                extra={"event": "reactivate_product", "product_id": product_id},
            )
            raise ErrorResponse("Product not found", status_code=404)

        # Check if product is already active
        if doc.get("is_active", True):
            logger.warning(
                f"Product already active: {product_id}",
                extra={"event": "reactivate_product", "product_id": product_id},
            )
            raise ErrorResponse("Product is already active", status_code=400)

        # Validate SKU uniqueness before reactivation (if product has SKU)
        if doc.get("sku"):
            existing = await collection.find_one(
                {"sku": doc["sku"], "_id": {"$ne": obj_id}, "is_active": True}
            )
            if existing:
                logger.warning(
                    f"Cannot reactivate - SKU conflict: {doc['sku']}",
                    extra={
                        "event": "reactivate_product_sku_conflict",
                        "product_id": product_id,
                        "sku": doc["sku"],
                    },
                )
                raise ErrorResponse(
                    f"Cannot reactivate: Another active product already uses "
                    f"SKU '{doc['sku']}'",
                    status_code=400,
                )

        # Reactivate the product with history tracking
        if acting_user:
            history_entry = {
                "updated_by": acting_user["user_id"],
                "updated_at": datetime.now(timezone.utc),
                "changes": {"is_active": True, "action": "reactivated"},
            }
            # Use $set for other fields and $push for history
            result = await collection.update_one(
                {"_id": obj_id},
                {
                    "$set": {
                        "is_active": True,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    "$push": {"history": history_entry},
                },
            )
        else:
            # Simple reactivation without history
            result = await collection.update_one(
                {"_id": obj_id},
                {"$set": {"is_active": True, "updated_at": datetime.now(timezone.utc)}},
            )

        if result.matched_count == 0:
            raise ErrorResponse("Product not found", status_code=404)

        # Fetch and return the reactivated product
        doc = await collection.find_one({"_id": obj_id})
        logger.info(
            f"Reactivated product {product_id}",
            extra={
                "event": "reactivate_product",
                "product_id": product_id,
                "reactivated_by": acting_user["user_id"] if acting_user else None,
            },
        )
        return product_doc_to_model(doc)

    except PyMongoError as e:
        logger.error(
            f"MongoDB error during reactivation: {e}",
            extra={"event": "mongodb_error", "product_id": product_id},
        )
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


def product_doc_to_model(doc):
    """
    Convert MongoDB document to ProductDB model.

    Args:
        doc: MongoDB document dictionary

    Returns:
        ProductDB: Product model object
    """
    return ProductDB(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description"),
        price=doc["price"],
        # Removed in_stock field - inventory management is handled by inventory-service
        category=doc.get("category"),
        brand=doc.get("brand"),
        sku=doc.get("sku"),
        images=doc.get("images", []),
        tags=doc.get("tags", []),
        attributes=doc.get("attributes", {}),
        variants=doc.get("variants", []),
        average_rating=doc.get("average_rating", 0),
        num_reviews=doc.get("num_reviews", 0),
        reviews=doc.get("reviews", []),
        created_by=doc["created_by"],
        updated_by=doc.get("updated_by"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
    )
