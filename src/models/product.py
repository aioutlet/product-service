"""Product model and related schemas"""
from datetime import datetime, UTC
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from src.models.restrictions import ProductRestrictions
from src.models.attribute_schema import ProductAttributes

def utc_now():
    return datetime.now(UTC)

class Taxonomy(BaseModel):
    department: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    product_type: Optional[str] = None

class ProductImage(BaseModel):
    url: str
    alt: Optional[str] = None
    is_primary: bool = False
    order: int = 1

class ProductBadge(BaseModel):
    type: str
    label: str
    priority: int = 0
    source: str = "manual"
    assigned_at: datetime = Field(default_factory=utc_now)

class SEOMetadata(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None

class Restrictions(BaseModel):
    """Legacy restrictions model - deprecated, use ProductRestrictions instead"""
    age_restricted: bool = False
    shipping_restrictions: List[str] = Field(default_factory=list)
    hazardous_material: bool = False

class ReviewAggregates(BaseModel):
    average_rating: float = 0.0
    total_review_count: int = 0
    rating_distribution: Dict[str, int] = Field(default_factory=dict)
    last_updated: Optional[datetime] = None

class AvailabilityStatus(BaseModel):
    status: str = "unknown"
    available_quantity: int = 0
    last_updated: Optional[datetime] = None

class QAStats(BaseModel):
    total_questions: int = 0
    answered_questions: int = 0
    last_updated: Optional[datetime] = None

class ProductHistoryEntry(BaseModel):
    updated_by: str
    updated_at: datetime
    changes: Dict[str, str]

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    long_description: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    sku: Optional[str] = None
    brand: Optional[str] = None
    status: str = "active"
    
    taxonomy: Optional[Taxonomy] = None
    department: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    product_type: Optional[str] = None
    
    variation_type: Optional[str] = None
    parent_id: Optional[str] = None
    variation_attributes: List[str] = Field(default_factory=list)
    child_skus: List[str] = Field(default_factory=list)
    child_count: int = 0
    
    # Legacy attributes (flat dict - deprecated, use structured_attributes instead)
    attributes: Dict[str, str] = Field(default_factory=dict)
    specifications: Dict[str, str] = Field(default_factory=dict)
    
    # Structured attributes (new)
    structured_attributes: Optional[ProductAttributes] = Field(
        None,
        description="Structured product attributes with validation"
    )
    
    images: List[ProductImage] = Field(default_factory=list)
    image_url: Optional[str] = None
    
    tags: List[str] = Field(default_factory=list)
    search_keywords: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    
    # Size chart reference
    size_chart_id: Optional[str] = Field(None, description="ID of the associated size chart")
    
    badges: List[ProductBadge] = Field(default_factory=list)
    seo: Optional[SEOMetadata] = None
    restrictions: Optional[Restrictions] = None
    
    review_aggregates: Optional[ReviewAggregates] = None
    availability_status: Optional[AvailabilityStatus] = None
    qa_stats: Optional[QAStats] = None
    
    created_by: str
    updated_by: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    is_active: bool = True
    history: List[ProductHistoryEntry] = Field(default_factory=list)

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    created_by: str
    description: Optional[str] = Field(None, max_length=500)
    long_description: Optional[str] = None
    compare_at_price: Optional[float] = Field(None, gt=0)
    sku: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    status: str = Field("active", pattern="^(active|draft|archived)$")
    taxonomy: Optional[Taxonomy] = None
    department: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    product_type: Optional[str] = None
    variation_type: Optional[str] = Field(None, pattern="^(parent|child|standalone)$")
    parent_id: Optional[str] = None
    variation_attributes: List[str] = Field(default_factory=list)
    attributes: Dict[str, str] = Field(default_factory=dict)
    specifications: Dict[str, str] = Field(default_factory=dict)
    structured_attributes: Optional[ProductAttributes] = None
    images: List[ProductImage] = Field(default_factory=list)
    image_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    search_keywords: List[str] = Field(default_factory=list)
    colors: List[str] = Field(default_factory=list)
    sizes: List[str] = Field(default_factory=list)
    seo: Optional[SEOMetadata] = None
    restrictions: Optional[Restrictions] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    long_description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    compare_at_price: Optional[float] = Field(None, gt=0)
    sku: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(active|draft|archived)$")
    taxonomy: Optional[Taxonomy] = None
    department: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    product_type: Optional[str] = None
    variation_type: Optional[str] = Field(None, pattern="^(parent|child|standalone)$")
    parent_id: Optional[str] = None
    variation_attributes: Optional[List[str]] = None
    child_skus: Optional[List[str]] = None
    attributes: Optional[Dict[str, str]] = None
    specifications: Optional[Dict[str, str]] = None
    structured_attributes: Optional[ProductAttributes] = None
    images: Optional[List[ProductImage]] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    search_keywords: Optional[List[str]] = None
    colors: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    badges: Optional[List[ProductBadge]] = None
    seo: Optional[SEOMetadata] = None
    restrictions: Optional[Restrictions] = None
    updated_by: Optional[str] = None
    updated_at: datetime = Field(default_factory=utc_now)

class ProductDB(ProductBase):
    id: str = Field(..., alias="_id")
    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

class ProductSearchResponse(BaseModel):
    products: List[ProductDB]
    total_count: int
    current_page: int
    total_pages: int
    page_size: int = 20
