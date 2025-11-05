"""
Bulk Import Models

Models for Excel import, template generation, and import job tracking.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ImportStatus(str, Enum):
    """Import job status"""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some rows succeeded, some failed
    CANCELLED = "cancelled"


class ImportMode(str, Enum):
    """Import processing mode"""
    ALL_OR_NOTHING = "all_or_nothing"  # Rollback if any row fails
    PARTIAL = "partial"  # Skip invalid rows, import valid ones


class ValidationSeverity(str, Enum):
    """Validation error severity"""
    ERROR = "error"  # Blocks import
    WARNING = "warning"  # Allows import with warning
    INFO = "info"  # Informational only


class ValidationError(BaseModel):
    """Validation error for a single row"""
    row_number: int = Field(..., description="Row number in Excel file (1-indexed)")
    field_name: Optional[str] = Field(None, description="Field with error")
    error_code: str = Field(..., description="Error code for categorization")
    error_message: str = Field(..., description="Human-readable error description")
    severity: ValidationSeverity = Field(default=ValidationSeverity.ERROR)
    suggested_correction: Optional[str] = Field(None, description="Suggested fix")
    current_value: Optional[Any] = Field(None, description="Current invalid value")
    
    class Config:
        use_enum_values = True


class ImportJobProgress(BaseModel):
    """Progress tracking for import job"""
    total_rows: int = Field(..., description="Total rows to process")
    processed_rows: int = Field(default=0, description="Rows processed so far")
    successful_rows: int = Field(default=0, description="Successfully imported rows")
    failed_rows: int = Field(default=0, description="Failed rows")
    skipped_rows: int = Field(default=0, description="Skipped rows (e.g., duplicates)")
    current_row: Optional[int] = Field(None, description="Currently processing row")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    @property
    def percentage(self) -> float:
        """Calculate completion percentage"""
        if self.total_rows == 0:
            return 0.0
        return round((self.processed_rows / self.total_rows) * 100, 2)


class ImportJob(BaseModel):
    """Import job record"""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original uploaded filename")
    file_path: Optional[str] = Field(None, description="Temporary file storage path")
    file_size: int = Field(default=0, description="File size in bytes")
    mode: ImportMode = Field(default=ImportMode.PARTIAL)
    status: ImportStatus = Field(default=ImportStatus.PENDING)
    category: Optional[str] = Field(None, description="Product category for template")
    
    # User tracking
    created_by: str = Field(..., description="User ID who initiated import")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # Progress tracking
    progress: ImportJobProgress = Field(default=None)
    
    # Validation results
    validation_errors: List[ValidationError] = Field(default_factory=list)
    validation_warnings: List[ValidationError] = Field(default_factory=list)
    
    # Results
    imported_product_ids: List[str] = Field(default_factory=list, description="IDs of imported products")
    error_report_path: Optional[str] = Field(None, description="Path to error report file")
    summary_message: Optional[str] = Field(None, description="Import summary message")
    
    # Metadata
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def __init__(self, **data):
        # Initialize progress if not provided
        if 'progress' not in data or data['progress'] is None:
            data['progress'] = ImportJobProgress(total_rows=0)
        super().__init__(**data)
    
    class Config:
        use_enum_values = True


class ImportJobSummary(BaseModel):
    """Summary of import job for listing"""
    job_id: str
    filename: str
    status: ImportStatus
    mode: ImportMode
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime]
    total_rows: int
    successful_rows: int
    failed_rows: int
    summary_message: Optional[str]
    
    class Config:
        use_enum_values = True


class ImportJobHistory(BaseModel):
    """Import job history response"""
    jobs: List[ImportJobSummary]
    total: int
    page: int
    page_size: int
    has_more: bool


class TemplateColumn(BaseModel):
    """Excel template column definition"""
    name: str = Field(..., description="Column header name")
    field: str = Field(..., description="Product field mapping")
    data_type: str = Field(..., description="Data type (string, number, boolean, date)")
    required: bool = Field(default=False, description="Is column required")
    description: Optional[str] = Field(None, description="Column description/help text")
    validation_rules: Optional[str] = Field(None, description="Validation rules")
    example_value: Optional[Any] = Field(None, description="Example value")
    allowed_values: Optional[List[str]] = Field(None, description="List of allowed values")
    min_value: Optional[float] = Field(None, description="Minimum value for numbers")
    max_value: Optional[float] = Field(None, description="Maximum value for numbers")
    max_length: Optional[int] = Field(None, description="Maximum string length")
    regex_pattern: Optional[str] = Field(None, description="Regex validation pattern")


class TemplateConfig(BaseModel):
    """Template configuration for category"""
    category: str = Field(..., description="Product category")
    version: str = Field(default="1.0", description="Template version")
    columns: List[TemplateColumn] = Field(..., description="Column definitions")
    instructions: Optional[str] = Field(None, description="Template usage instructions")
    example_rows: int = Field(default=3, description="Number of example rows to include")


class DownloadTemplateRequest(BaseModel):
    """Request to download Excel template"""
    category: str = Field(..., description="Product category for template")
    include_examples: bool = Field(default=True, description="Include example rows")


class UploadImportFileRequest(BaseModel):
    """Request to upload import file"""
    mode: ImportMode = Field(default=ImportMode.PARTIAL)
    category: Optional[str] = Field(None, description="Product category")
    validate_only: bool = Field(default=False, description="Only validate, don't import")


class ImportJobStatusResponse(BaseModel):
    """Import job status response"""
    job: ImportJob
    can_retry: bool = Field(..., description="Whether job can be retried")
    error_report_url: Optional[str] = Field(None, description="URL to download error report")


class RetryImportRequest(BaseModel):
    """Request to retry failed import"""
    fix_errors: bool = Field(default=False, description="Whether errors were fixed")
    updated_file: bool = Field(default=False, description="Whether new file uploaded")


class BulkUpdateRequest(BaseModel):
    """Request for bulk update via Excel"""
    operation: str = Field(..., description="Operation type: price_update, attribute_update, status_change")
    updates: List[Dict[str, Any]] = Field(..., description="List of update operations")


class BulkUpdateResponse(BaseModel):
    """Response for bulk update"""
    success_count: int
    failure_count: int
    total_count: int
    updated_product_ids: List[str]
    errors: List[ValidationError]
    summary: str


class ImageUploadMethod(str, Enum):
    """Image upload method"""
    URL = "url"  # Image URLs in Excel file
    ZIP = "zip"  # ZIP file with images


class ImageValidationResult(BaseModel):
    """Image validation result"""
    sku: str
    image_index: int
    filename: str
    valid: bool
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    dimensions: Optional[Dict[str, int]] = None  # width, height
    format: Optional[str] = None  # JPEG, PNG, WebP
    
    class Config:
        use_enum_values = True
