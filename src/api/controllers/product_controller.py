from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from src.shared.core.auth import require_admin_user
from src.shared.core.errors import ErrorResponse
from src.shared.core.logger import logger
from src.shared.models.product import ProductCreate, ProductDB, ProductUpdate
from src.shared.utils.validators import validate_object_id


async def search_products(
    collection,
    search_text,
    department=None,
    category=None,
    subcategory=None,
    min_price=None,
    max_price=None,
    tags=None,
    skip=0,
    limit=20,
):
    """
    Search products by text in name and description fields.
    Supports additional filtering by hierarchical taxonomy, price range, and tags.

    Args:
        collection: MongoDB collection instance
        search_text: Text to search for in name, description, tags, and brand
        department: Optional department filter (Level 1: Women, Men, Kids, etc.)
        category: Optional category filter (Level 2: Clothing, Accessories, etc.)
        subcategory: Optional subcategory filter (Level 3: Tops, Laptops, etc.)
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
                "Empty search text provided", metadata={"event": "search_products_empty"}
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

        # Add hierarchical taxonomy filters
        if department:
            query["department"] = {
                "$regex": f"^{department}$",
                "$options": "i",
            }  # Case-insensitive department match
        if category:
            query["category"] = {
                "$regex": f"^{category}$",
                "$options": "i",
            }  # Case-insensitive category match
        if subcategory:
            query["subcategory"] = {
                "$regex": f"^{subcategory}$",
                "$options": "i",
            }  # Case-insensitive subcategory match
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
            metadata={"event": "mongodb_error", "search_text": search_text},
        )
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def get_trending_categories(collection, limit=5):
    """
    Get trending categories based on product popularity algorithm.
    
    Trending score calculation per category:
    - Product count in category
    - Average rating across all products
    - Total reviews across all products
    - Trending score = (avg_rating * total_reviews * product_count)
    
    Args:
        collection: MongoDB collection instance
        limit: Maximum number of trending categories to return (default: 5)
    
    Returns:
        list[dict]: List of trending categories with metadata sorted by score
        
    Raises:
        ErrorResponse: If database error occurs
    """
    try:
        # Aggregation pipeline to calculate trending categories
        pipeline = [
            # Filter: only active products
            {
                "$match": {
                    "is_active": True,
                    "category": {"$exists": True, "$ne": None, "$ne": ""}
                }
            },
            # Group by category and calculate metrics
            {
                "$group": {
                    "_id": "$category",
                    "product_count": {"$sum": 1},
                    "avg_rating": {"$avg": "$average_rating"},
                    "total_reviews": {"$sum": "$num_reviews"},
                    "in_stock_count": {
                        "$sum": {"$cond": [{"$gt": ["$num_reviews", 0]}, 1, 0]}
                    },
                    # Get one featured product from category (highest rated)
                    "featured_product": {
                        "$first": {
                            "name": "$name",
                            "price": "$price",
                            "images": "$images",
                            "average_rating": "$average_rating"
                        }
                    }
                }
            },
            # Calculate trending score
            {
                "$addFields": {
                    "trending_score": {
                        "$multiply": [
                            {"$ifNull": ["$avg_rating", 0]},
                            {"$ifNull": ["$total_reviews", 0]},
                            "$product_count"
                        ]
                    }
                }
            },
            # Sort by trending score (highest first)
            {"$sort": {"trending_score": -1}},
            # Limit results
            {"$limit": limit},
            # Format output
            {
                "$project": {
                    "_id": 0,
                    "name": "$_id",
                    "product_count": 1,
                    "in_stock_count": 1,
                    "avg_rating": {"$round": ["$avg_rating", 1]},
                    "total_reviews": 1,
                    "trending_score": {"$round": ["$trending_score", 0]},
                    "featured_product": 1
                }
            }
        ]
        
        # Execute aggregation pipeline
        cursor = collection.aggregate(pipeline)
        categories = [doc async for doc in cursor]
        
        logger.info(
            f"Fetched {len(categories)} trending categories",
            metadata={"event": "get_trending_categories", "count": len(categories)}
        )
        
        return categories
        
    except PyMongoError as e:
        logger.error(
            f"MongoDB error fetching trending categories: {e}",
            metadata={"event": "mongodb_error", "error": str(e)}
        )
        raise ErrorResponse(f"Database error: {str(e)}", status_code=500)
    except Exception as e:
        logger.error(
            f"Unexpected error fetching trending categories: {e}",
            metadata={"event": "trending_categories_error", "error": str(e), "error_type": type(e).__name__}
        )
        raise ErrorResponse(f"Error fetching trending categories: {str(e)}", status_code=500)


async def get_trending_products(collection, limit=4):
    """
    Get trending products based on data-driven algorithm.
    
    Trending score calculation:
    - Base score: (average_rating * num_reviews)
    - Recency boost: Products created in last 30 days get 1.5x multiplier
    - Minimum threshold: At least 3 reviews required to be considered trending
    
    Args:
        collection: MongoDB collection instance
        limit: Maximum number of trending products to return (default: 4)
    
    Returns:
        list[ProductDB]: List of trending products sorted by score
        
    Raises:
        ErrorResponse: If database error occurs
    """
    try:
        # Calculate date 30 days ago for recency boost
        thirty_days_ago = datetime.now(timezone.utc).timestamp() - (30 * 24 * 60 * 60)
        
        # Aggregation pipeline to calculate trending scores
        pipeline = [
            # Filter: only active products with at least 3 reviews
            {
                "$match": {
                    "is_active": True,
                    "num_reviews": {"$gte": 3}
                }
            },
            # Add computed fields
            {
                "$addFields": {
                    # Base trending score: rating * reviews
                    "base_score": {
                        "$multiply": ["$average_rating", "$num_reviews"]
                    },
                    # Check if product is recent (created in last 30 days)
                    "is_recent": {
                        "$gte": [
                            {"$toLong": "$created_at"},
                            thirty_days_ago * 1000  # Convert to milliseconds
                        ]
                    }
                }
            },
            # Calculate final trending score with recency boost
            {
                "$addFields": {
                    "trending_score": {
                        "$cond": {
                            "if": "$is_recent",
                            "then": {"$multiply": ["$base_score", 1.5]},  # 50% boost for recent
                            "else": "$base_score"
                        }
                    }
                }
            },
            # Sort by trending score (highest first)
            {"$sort": {"trending_score": -1}},
            # Limit results
            {"$limit": limit}
        ]
        
        # Execute aggregation pipeline
        cursor = collection.aggregate(pipeline)
        products = [product_doc_to_model(doc) async for doc in cursor]
        
        logger.info(
            f"Fetched {len(products)} trending products",
            metadata={"event": "get_trending_products", "count": len(products)}
        )
        
        return products
        
    except PyMongoError as e:
        logger.error(
            f"MongoDB error fetching trending products: {e}",
            metadata={"event": "mongodb_error", "error": str(e)}
        )
        raise ErrorResponse(f"Database error: {str(e)}", status_code=500)
    except Exception as e:
        logger.error(
            f"Unexpected error fetching trending products: {e}",
            metadata={"event": "trending_error", "error": str(e), "error_type": type(e).__name__}
        )
        raise ErrorResponse(f"Error fetching trending products: {str(e)}", status_code=500)


async def list_products(
    collection,
    department=None,
    category=None,
    subcategory=None,
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
        department: Optional department filter (Level 1: Women, Men, Kids, etc.)
        category: Optional category filter (Level 2: Clothing, Accessories, etc.)
        subcategory: Optional subcategory filter (Level 3: Tops, Laptops, etc.)
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

        # Apply hierarchical taxonomy filters
        if department:
            query["department"] = {
                "$regex": f"^{department}$",
                "$options": "i",
            }  # Case-insensitive department match
        if category:
            query["category"] = {
                "$regex": f"^{category}$",
                "$options": "i",
            }  # Case-insensitive category match
        if subcategory:
            query["subcategory"] = {
                "$regex": f"^{subcategory}$",
                "$options": "i",
            }  # Case-insensitive subcategory match
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
        logger.error(f"MongoDB error: {e}", metadata={"event": "mongodb_error"})
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
                metadata={"event": "get_product", "product_id": product_id},
            )
            raise ErrorResponse("Product not found", status_code=404)

        # Log successful retrieval
        logger.info(
            f"Fetched product {product_id}",
            metadata={"event": "get_product", "product_id": product_id},
        )
        return product_doc_to_model(doc)
    except (PyMongoError, ValueError) as e:
        logger.error(
            f"Error fetching product: {e}",
            metadata={"event": "get_product_error", "product_id": product_id},
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
                    metadata={"event": "duplicate_sku", "sku": product.sku},
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
            metadata={"event": "create_product", "product_id": str(result.inserted_id)}
        )
        return product_doc_to_model(doc)
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}", metadata={"event": "mongodb_error"})
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
                metadata={"event": "update_product", "product_id": product_id},
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
                    metadata={"event": "duplicate_sku", "sku": update_data["sku"]},
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
                metadata={"event": "update_product", "product_id": product_id},
            )
            raise ErrorResponse("Product not found", status_code=404)

        # Retrieve and return updated product
        doc = await collection.find_one({"_id": obj_id})
        logger.info(
            f"Updated product {product_id}",
            metadata={"event": "update_product", "product_id": product_id}
        )
        return product_doc_to_model(doc)
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}", metadata={"event": "mongodb_error"})
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
            metadata={"event": "soft_delete_product", "product_id": product_id}
        )
        return None
    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}", metadata={"event": "mongodb_error"})
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
                metadata={"event": "reactivate_product", "product_id": product_id},
            )
            raise ErrorResponse("Product not found", status_code=404)

        # Check if product is already active
        if doc.get("is_active", True):
            logger.warning(
                f"Product already active: {product_id}",
                metadata={"event": "reactivate_product", "product_id": product_id},
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
                    metadata={
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
            metadata={
                "event": "reactivate_product",
                "product_id": product_id,
                "reactivated_by": acting_user["user_id"] if acting_user else None,
            },
        )
        return product_doc_to_model(doc)

    except PyMongoError as e:
        logger.error(
            f"MongoDB error during reactivation: {e}",
            metadata={"event": "mongodb_error", "product_id": product_id},
        )
        raise ErrorResponse(
            "Database connection error. Please try again later.", status_code=503
        )


async def get_admin_stats(collection):
    """
    Get product statistics for admin dashboard.
    
    Args:
        collection: MongoDB collection instance
    
    Returns:
        dict: Statistics including total, active, lowStock, and outOfStock counts
        
    Raises:
        ErrorResponse: If database error occurs
    """
    try:
        logger.info("Fetching product statistics for admin dashboard")
        
        # Get total products count
        total = await collection.count_documents({})
        
        # Get active products count (is_active = True)
        active = await collection.count_documents({"is_active": True})
        
        # Note: Product service doesn't manage stock - that's in inventory service
        # These will return 0, but we keep the structure for consistency with BFF expectations
        low_stock = 0
        out_of_stock = 0
        
        stats = {
            "total": total,
            "active": active,
            "lowStock": low_stock,
            "outOfStock": out_of_stock
        }
        
        logger.info(
            "Product statistics fetched successfully",
            metadata={
                "businessEvent": "ADMIN_STATS_FETCHED",
                "stats": stats
            }
        )
        
        return stats
        
    except PyMongoError as e:
        logger.error(
            f"Failed to fetch product statistics: {str(e)}",
            metadata={"businessEvent": "ADMIN_STATS_ERROR", "error": str(e)}
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
        brand=doc.get("brand"),
        sku=doc.get("sku"),
        # Hierarchical taxonomy fields
        department=doc.get("department"),
        category=doc.get("category"),
        subcategory=doc.get("subcategory"),
        product_type=doc.get("productType"),  # Note: MongoDB uses productType, model uses product_type
        # Media and metadata
        images=doc.get("images", []),
        tags=doc.get("tags", []),
        # Product variations
        colors=doc.get("colors", []),
        sizes=doc.get("sizes", []),
        # Product specifications
        specifications=doc.get("specifications", {}),
        # Reviews and ratings (aggregate only)
        average_rating=doc.get("average_rating", 0),
        num_reviews=doc.get("num_reviews", 0),
        # Audit trail
        created_by=doc.get("created_by", "system"),
        updated_by=doc.get("updated_by"),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        updated_at=doc.get("updated_at", datetime.now(timezone.utc)),
        is_active=doc.get("is_active", True),
        history=doc.get("history", []),
    )
