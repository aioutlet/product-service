"""
Unit tests for bulk import models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.bulk_import import (
    ImportStatus,
    ImportMode,
    ValidationSeverity,
    ValidationError as ImportValidationError,
    ImportJobProgress,
    ImportJob,
    ImportJobSummary,
    ImportJobHistory,
    TemplateColumn,
    TemplateConfig,
    DownloadTemplateRequest,
    ImportJobStatusResponse,
    ImageUploadMethod,
    ImageValidationResult
)


class TestImportStatus:
    """Test ImportStatus enum."""
    
    def test_all_status_values_exist(self):
        """Test all expected status values are defined."""
        assert ImportStatus.PENDING == "pending"
        assert ImportStatus.VALIDATING == "validating"
        assert ImportStatus.PROCESSING == "processing"
        assert ImportStatus.COMPLETED == "completed"
        assert ImportStatus.FAILED == "failed"
        assert ImportStatus.PARTIAL == "partial"
        assert ImportStatus.CANCELLED == "cancelled"


class TestImportMode:
    """Test ImportMode enum."""
    
    def test_import_modes(self):
        """Test import mode values."""
        assert ImportMode.ALL_OR_NOTHING == "all_or_nothing"
        assert ImportMode.PARTIAL == "partial"


class TestValidationError:
    """Test ValidationError model."""
    
    def test_create_validation_error(self):
        """Test creating a validation error."""
        error = ImportValidationError(
            row_number=5,
            field_name="price",
            error_code="INVALID_PRICE",
            error_message="Price must be non-negative",
            severity=ValidationSeverity.ERROR
        )
        
        assert error.row_number == 5
        assert error.field_name == "price"
        assert error.error_code == "INVALID_PRICE"
        assert error.severity == ValidationSeverity.ERROR
    
    def test_validation_error_with_suggestion(self):
        """Test validation error with suggested correction."""
        error = ImportValidationError(
            row_number=10,
            field_name="status",
            error_code="INVALID_STATUS",
            error_message="Invalid status value",
            severity=ValidationSeverity.ERROR,
            suggested_correction="Use one of: active, draft, archived"
        )
        
        assert error.suggested_correction == "Use one of: active, draft, archived"
    
    def test_validation_error_with_current_value(self):
        """Test validation error with current value."""
        error = ImportValidationError(
            row_number=15,
            field_name="sku",
            error_code="DUPLICATE_SKU",
            error_message="SKU already exists",
            severity=ValidationSeverity.ERROR,
            current_value="TEST-123"
        )
        
        assert error.current_value == "TEST-123"


class TestImportJobProgress:
    """Test ImportJobProgress model."""
    
    def test_create_progress(self):
        """Test creating progress tracker."""
        progress = ImportJobProgress(
            total_rows=100,
            processed_rows=50,
            successful_rows=45,
            failed_rows=5
        )
        
        assert progress.total_rows == 100
        assert progress.processed_rows == 50
        assert progress.successful_rows == 45
        assert progress.failed_rows == 5
    
    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        progress = ImportJobProgress(
            total_rows=100,
            processed_rows=50,
            successful_rows=45,
            failed_rows=5
        )
        
        # Should calculate 50% processed
        assert progress.percentage == 50.0
    
    def test_progress_percentage_zero_total(self):
        """Test progress percentage with zero total rows."""
        progress = ImportJobProgress(
            total_rows=0,
            processed_rows=0,
            successful_rows=0,
            failed_rows=0
        )
        
        assert progress.percentage == 0.0
    
    def test_progress_percentage_complete(self):
        """Test progress percentage when complete."""
        progress = ImportJobProgress(
            total_rows=100,
            processed_rows=100,
            successful_rows=100,
            failed_rows=0
        )
        
        assert progress.percentage == 100.0


class TestImportJob:
    """Test ImportJob model."""
    
    def test_create_import_job(self):
        """Test creating an import job."""
        job = ImportJob(
            job_id="job-123",
            filename="products.xlsx",
            status=ImportStatus.PENDING,
            mode=ImportMode.PARTIAL,
            created_by="user-456"
        )
        
        assert job.job_id == "job-123"
        assert job.filename == "products.xlsx"
        assert job.status == ImportStatus.PENDING
        assert job.mode == ImportMode.PARTIAL
        assert job.created_by == "user-456"
    
    def test_import_job_with_progress(self):
        """Test import job with progress tracking."""
        progress = ImportJobProgress(
            total_rows=50,
            processed_rows=25,
            successful_rows=20,
            failed_rows=5
        )
        
        job = ImportJob(
            job_id="job-123",
            filename="products.xlsx",
            status=ImportStatus.PROCESSING,
            mode=ImportMode.PARTIAL,
            created_by="user-456",
            progress=progress
        )
        
        assert job.progress.total_rows == 50
        assert job.progress.processed_rows == 25
        assert job.progress.percentage == 50.0
    
    def test_import_job_with_validation_errors(self):
        """Test import job with validation errors."""
        errors = [
            ImportValidationError(
                row_number=5,
                field_name="price",
                error_code="INVALID_PRICE",
                error_message="Price must be non-negative",
                severity=ValidationSeverity.ERROR
            ),
            ImportValidationError(
                row_number=10,
                field_name="sku",
                error_code="DUPLICATE_SKU",
                error_message="SKU already exists",
                severity=ValidationSeverity.ERROR
            )
        ]
        
        job = ImportJob(
            job_id="job-123",
            filename="products.xlsx",
            status=ImportStatus.FAILED,
            mode=ImportMode.ALL_OR_NOTHING,
            created_by="user-456",
            validation_errors=errors
        )
        
        assert len(job.validation_errors) == 2
        assert job.validation_errors[0].error_code == "INVALID_PRICE"
        assert job.validation_errors[1].error_code == "DUPLICATE_SKU"
    
    def test_import_job_with_imported_products(self):
        """Test import job with imported product IDs."""
        job = ImportJob(
            job_id="job-123",
            filename="products.xlsx",
            status=ImportStatus.COMPLETED,
            mode=ImportMode.PARTIAL,
            created_by="user-456",
            imported_product_ids=["prod-1", "prod-2", "prod-3"]
        )
        
        assert len(job.imported_product_ids) == 3
        assert "prod-1" in job.imported_product_ids
    
    def test_import_job_timestamps(self):
        """Test import job timestamps."""
        now = datetime.utcnow()
        
        job = ImportJob(
            job_id="job-123",
            filename="products.xlsx",
            status=ImportStatus.COMPLETED,
            mode=ImportMode.PARTIAL,
            created_by="user-456",
            created_at=now,
            started_at=now,
            completed_at=now
        )
        
        assert job.created_at == now
        assert job.started_at == now
        assert job.completed_at == now


class TestTemplateColumn:
    """Test TemplateColumn model."""
    
    def test_create_template_column(self):
        """Test creating a template column."""
        column = TemplateColumn(
            name="SKU*",
            field="sku",
            data_type="string",
            required=True,
            example_value="PROD-001"
        )
        
        assert column.name == "SKU*"
        assert column.field == "sku"
        assert column.data_type == "string"
        assert column.required is True
        assert column.example_value == "PROD-001"
    
    def test_column_with_validation_rules(self):
        """Test column with validation rules."""
        column = TemplateColumn(
            name="Price*",
            field="price",
            data_type="number",
            required=True,
            validation_rules="Min: 0, Max: 1000000",
            example_value=99.99
        )
        
        assert column.validation_rules == "Min: 0, Max: 1000000"
    
    def test_column_with_allowed_values(self):
        """Test column with allowed values."""
        column = TemplateColumn(
            name="Status",
            field="status",
            data_type="string",
            required=False,
            allowed_values=["active", "draft", "archived"],
            example_value="active"
        )
        
        assert len(column.allowed_values) == 3
        assert "active" in column.allowed_values


class TestTemplateConfig:
    """Test TemplateConfig model."""
    
    def test_create_template_config(self):
        """Test creating template configuration."""
        columns = [
            TemplateColumn(
                name="SKU*",
                field="sku",
                data_type="string",
                required=True,
                example_value="PROD-001"
            ),
            TemplateColumn(
                name="Name*",
                field="name",
                data_type="string",
                required=True,
                example_value="Test Product"
            )
        ]
        
        config = TemplateConfig(
            category="Clothing",
            columns=columns,
            include_examples=True
        )
        
        assert config.category == "Clothing"
        assert len(config.columns) == 2
        assert config.include_examples is True


class TestImportJobSummary:
    """Test ImportJobSummary model."""
    
    def test_create_job_summary(self):
        """Test creating job summary."""
        now = datetime.utcnow()
        
        summary = ImportJobSummary(
            job_id="job-123",
            filename="products.xlsx",
            status=ImportStatus.COMPLETED,
            mode=ImportMode.PARTIAL,
            created_by="user-456",
            created_at=now,
            total_rows=100,
            successful_rows=95,
            failed_rows=5
        )
        
        assert summary.job_id == "job-123"
        assert summary.filename == "products.xlsx"
        assert summary.total_rows == 100
        assert summary.successful_rows == 95
        assert summary.failed_rows == 5


class TestImportJobHistory:
    """Test ImportJobHistory model."""
    
    def test_create_job_history(self):
        """Test creating job history."""
        now = datetime.utcnow()
        
        summaries = [
            ImportJobSummary(
                job_id="job-1",
                filename="products1.xlsx",
                status=ImportStatus.COMPLETED,
                mode=ImportMode.PARTIAL,
                created_by="user-456",
                created_at=now,
                total_rows=50,
                successful_rows=50,
                failed_rows=0
            ),
            ImportJobSummary(
                job_id="job-2",
                filename="products2.xlsx",
                status=ImportStatus.FAILED,
                mode=ImportMode.ALL_OR_NOTHING,
                created_by="user-456",
                created_at=now,
                total_rows=100,
                successful_rows=0,
                failed_rows=100
            )
        ]
        
        history = ImportJobHistory(
            jobs=summaries,
            total=2,
            page=1,
            page_size=20,
            has_more=False
        )
        
        assert len(history.jobs) == 2
        assert history.total == 2
        assert history.page == 1
        assert history.has_more is False


class TestImageValidationResult:
    """Test ImageValidationResult model."""
    
    def test_valid_image(self):
        """Test valid image result."""
        result = ImageValidationResult(
            is_valid=True,
            url="https://example.com/image.jpg"
        )
        
        assert result.is_valid is True
        assert result.url == "https://example.com/image.jpg"
        assert result.error_message is None
    
    def test_invalid_image(self):
        """Test invalid image result."""
        result = ImageValidationResult(
            is_valid=False,
            error_message="Invalid image format"
        )
        
        assert result.is_valid is False
        assert result.error_message == "Invalid image format"
