import csv
import io
import json
from datetime import datetime
from typing import List, Optional
from pymongo.errors import PyMongoError
from src.models.product import ProductCreate, ProductUpdate, ProductDB
from src.core.errors import ErrorResponse
from src.core.logger import logger
from src.utils.validators import validate_object_id
from .product_controller import update_product, delete_product

async def bulk_create_products(products: List[ProductCreate], collection, acting_user=None):
    if not acting_user or "admin" not in acting_user.get("roles", []):
        raise ErrorResponse("Only admin users can create products.", status_code=403)
    skus = [p.sku for p in products if p.sku]
    if len(skus) != len(set(skus)):
        raise ErrorResponse("Duplicate SKUs in input.", status_code=400)
    existing = await collection.find({"sku": {"$in": skus}, "is_active": True}).to_list(length=None)
    if existing:
        existing_skus = [e["sku"] for e in existing]
        raise ErrorResponse(f"SKUs already exist: {existing_skus}", status_code=400)
    docs = []
    for product in products:
        if product.price < 0 or product.in_stock < 0:
            raise ErrorResponse("Price and stock must be non-negative.", status_code=400)
        data = product.dict()
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        data["is_active"] = True
        data["history"] = []
        docs.append(data)
    result = await collection.insert_many(docs)
    inserted = await collection.find({"_id": {"$in": result.inserted_ids}}).to_list(length=None)
    logger.info(f"Bulk created {len(result.inserted_ids)} products", extra={"event": "bulk_create_products"})
    return [ProductDB(**doc) for doc in inserted]

async def bulk_update_products(updates: List[dict], collection, acting_user=None):
    if not acting_user or "admin" not in acting_user.get("roles", []):
        raise ErrorResponse("Only admin users can update products.", status_code=403)
    updated = []
    for upd in updates:
        product_id = upd.pop("id", None)
        if not product_id:
            continue
        product = ProductUpdate(**upd)
        try:
            updated_product = await update_product(product_id, product, collection, acting_user)
            updated.append(updated_product)
        except ErrorResponse as e:
            logger.warning(f"Bulk update failed for {product_id}: {e.detail}")
            continue
    logger.info(f"Bulk updated {len(updated)} products", extra={"event": "bulk_update_products"})
    return updated

async def bulk_delete_products(ids: List[str], collection, acting_user=None):
    if not acting_user or "admin" not in acting_user.get("roles", []):
        raise ErrorResponse("Only admin users can delete products.", status_code=403)
    deleted = 0
    for product_id in ids:
        try:
            await delete_product(product_id, collection, acting_user)
            deleted += 1
        except ErrorResponse as e:
            logger.warning(f"Bulk delete failed for {product_id}: {e.detail}")
            continue
    logger.info(f"Bulk soft deleted {deleted} products", extra={"event": "bulk_delete_products"})
    return {"deleted": deleted}

async def import_products(file_content: bytes, filetype: str, collection):
    if filetype == "csv":
        f = io.StringIO(file_content.decode())
        reader = csv.DictReader(f)
        products = [ProductCreate(**row) for row in reader]
    elif filetype == "json":
        data = json.loads(file_content)
        products = [ProductCreate(**item) for item in data]
    else:
        raise ErrorResponse("Unsupported file type", status_code=400)
    return await bulk_create_products(products, collection)

async def export_products(collection, filetype: str = "json", filters: Optional[dict] = None):
    query = filters or {"is_active": True}
    products = await collection.find(query).to_list(length=None)
    if filetype == "csv":
        if not products:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=products[0].keys())
        writer.writeheader()
        for prod in products:
            writer.writerow(prod)
        return output.getvalue()
    elif filetype == "json":
        return json.dumps(products, default=str)
    else:
        raise ErrorResponse("Unsupported file type", status_code=400)
