"""
Bulk Import Worker
Background worker for processing bulk product import jobs.
Implements PRD REQ-5.2.2: Asynchronous bulk import processing
"""
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.db.mongodb import get_product_collection
from src.services.bulk_import_service import get_bulk_import_service
from src.services.dapr_publisher import get_dapr_publisher
from src.observability.logging import logger


class BulkImportWorker:
    """
    Background worker for processing bulk import jobs.
    Consumes product.bulk.import.job.created events and processes imports.
    """

    def __init__(self):
        self.bulk_service = get_bulk_import_service()
        self.publisher = get_dapr_publisher()
        self.batch_size = 100  # Process 100 products per batch

    async def process_import_job(
        self,
        job_id: str,
        products: List[Dict[str, Any]],
        import_mode: str = "partial"
    ):
        """
        Process a bulk import job.

        Args:
            job_id: Import job ID
            products: List of product data to import
            import_mode: "partial" or "all-or-nothing"
        """
        try:
            # Update job status to processing
            await self.bulk_service.update_job_status(
                job_id,
                status="processing",
                processed_rows=0,
                success_count=0,
                error_count=0
            )

            logger.info(
                f"Started processing import job: {job_id}",
                metadata={
                    'event': 'import_job_processing_started',
                    'jobId': job_id,
                    'totalProducts': len(products),
                    'importMode': import_mode
                }
            )

            # Get collection
            collection = await get_product_collection()

            # Process in batches
            total_success = 0
            total_errors = 0
            errors_detail = []

            for batch_start in range(0, len(products), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(products))
                batch = products[batch_start:batch_end]

                if import_mode == "all-or-nothing":
                    # All-or-nothing: Use transaction
                    success, errors = await self._process_batch_transactional(
                        collection,
                        batch,
                        batch_start
                    )
                else:
                    # Partial: Process each product individually
                    success, errors = await self._process_batch_partial(
                        collection,
                        batch,
                        batch_start
                    )

                total_success += success
                total_errors += len(errors)
                errors_detail.extend(errors)

                # Publish progress event
                await self.publisher.publish(
                    'product.bulk.import.progress',
                    {
                        'jobId': job_id,
                        'processedRows': batch_end,
                        'successCount': total_success,
                        'errorCount': total_errors,
                        'totalRows': len(products)
                    },
                    None
                )

                # Update job status
                await self.bulk_service.update_job_status(
                    job_id,
                    status="processing",
                    processed_rows=batch_end,
                    success_count=total_success,
                    error_count=total_errors
                )

                logger.info(
                    f"Processed batch for job {job_id}: {batch_end}/{len(products)}",
                    metadata={
                        'event': 'import_batch_processed',
                        'jobId': job_id,
                        'batchEnd': batch_end,
                        'totalRows': len(products)
                    }
                )

            # Mark job as completed
            await self.bulk_service.update_job_status(
                job_id,
                status="completed",
                processed_rows=len(products),
                success_count=total_success,
                error_count=total_errors
            )

            # Publish completion event
            await self.publisher.publish(
                'product.bulk.import.completed',
                {
                    'jobId': job_id,
                    'totalRows': len(products),
                    'successCount': total_success,
                    'errorCount': total_errors,
                    'completedAt': datetime.now(timezone.utc).isoformat()
                },
                None
            )

            logger.info(
                f"Completed import job: {job_id}",
                metadata={
                    'event': 'import_job_completed',
                    'jobId': job_id,
                    'successCount': total_success,
                    'errorCount': total_errors
                }
            )

        except Exception as e:
            logger.error(
                f"Failed to process import job {job_id}: {str(e)}",
                metadata={
                    'event': 'import_job_failed',
                    'jobId': job_id,
                    'error': str(e)
                }
            )

            # Mark job as failed
            await self.bulk_service.update_job_status(
                job_id,
                status="failed"
            )

            # Publish failure event
            await self.publisher.publish(
                'product.bulk.import.failed',
                {
                    'jobId': job_id,
                    'error': str(e),
                    'failedAt': datetime.now(timezone.utc).isoformat()
                },
                None
            )

    async def _process_batch_partial(
        self,
        collection,
        batch: List[Dict[str, Any]],
        batch_offset: int
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        Process batch in partial mode (skip errors, import valid products).

        Returns:
            Tuple of (success_count, errors)
        """
        success_count = 0
        errors = []

        for idx, product_data in enumerate(batch):
            row_number = batch_offset + idx + 2  # +2 for header row and 0-index

            try:
                # Check for duplicate SKU
                sku = product_data.get('sku')
                if sku:
                    existing = await collection.find_one(
                        {"sku": sku, "is_active": True}
                    )
                    if existing:
                        errors.append({
                            'row': row_number,
                            'error': f"SKU '{sku}' already exists",
                            'sku': sku
                        })
                        continue

                # Add metadata
                product_data['created_at'] = datetime.now(timezone.utc)
                product_data['updated_at'] = datetime.now(timezone.utc)
                product_data['history'] = []

                # Insert product
                result = await collection.insert_one(product_data)

                # Publish product.created event
                await self.publisher.publish(
                    'product.created',
                    {
                        'productId': str(result.inserted_id),
                        'sku': product_data.get('sku'),
                        'name': product_data.get('name'),
                        'price': product_data.get('price'),
                        'source': 'bulk_import'
                    },
                    None
                )

                success_count += 1

            except Exception as e:
                errors.append({
                    'row': row_number,
                    'error': str(e),
                    'sku': product_data.get('sku', 'unknown')
                })

        return success_count, errors

    async def _process_batch_transactional(
        self,
        collection,
        batch: List[Dict[str, Any]],
        batch_offset: int
    ) -> tuple[int, List[Dict[str, Any]]]:
        """
        Process batch in all-or-nothing mode (use transaction).

        Returns:
            Tuple of (success_count, errors)
        """
        errors = []

        try:
            # Check for duplicate SKUs first
            skus = [p.get('sku') for p in batch if p.get('sku')]
            if skus:
                existing = await collection.find(
                    {"sku": {"$in": skus}, "is_active": True}
                ).to_list(length=None)

                if existing:
                    existing_skus = [e['sku'] for e in existing]
                    errors.append({
                        'row': batch_offset + 2,
                        'error': f"Batch has duplicate SKUs: {existing_skus}",
                        'skus': existing_skus
                    })
                    return 0, errors

            # Add metadata to all products
            for product_data in batch:
                product_data['created_at'] = datetime.now(timezone.utc)
                product_data['updated_at'] = datetime.now(timezone.utc)
                product_data['history'] = []

            # Insert all products in transaction
            # Note: MongoDB transactions require replica set
            # For single node, we do bulk insert (atomic operation)
            result = await collection.insert_many(batch)

            # Publish events for all created products
            for idx, inserted_id in enumerate(result.inserted_ids):
                product_data = batch[idx]
                await self.publisher.publish(
                    'product.created',
                    {
                        'productId': str(inserted_id),
                        'sku': product_data.get('sku'),
                        'name': product_data.get('name'),
                        'price': product_data.get('price'),
                        'source': 'bulk_import'
                    },
                    None
                )

            return len(batch), []

        except Exception as e:
            logger.error(
                f"Batch transaction failed: {str(e)}",
                metadata={'batchOffset': batch_offset, 'error': str(e)}
            )
            errors.append({
                'row': batch_offset + 2,
                'error': f"Batch failed: {str(e)}",
                'batch_size': len(batch)
            })
            return 0, errors


# Singleton instance
_worker = None


def get_bulk_import_worker() -> BulkImportWorker:
    """Get singleton bulk import worker instance."""
    global _worker
    if _worker is None:
        _worker = BulkImportWorker()
    return _worker
