# Product Service - Product Requirements Document

## Overview

- **Service**: Product Service
- **Domain**: Product Catalog Management
- **Purpose**: Manage the product catalog for AIOutlet e-commerce platform, including product CRUD operations, search, and product discovery features.
- **Pattern**: Publisher & Consumer (publishes product events, consumes review/inventory/analytics events)
- **Owner**: Product Team
- **Last Updated**: November 3, 2025

## Business Context

Product Service is the central source of truth for all product information in the AIOutlet platform. It provides product data to the Web UI for customer browsing, to the Admin UI for catalog management, and to other services (Order, Inventory, Review) for their operations.

**Data Synchronization**: Product Service maintains denormalized data from other services (review aggregates, inventory availability, sales metrics) for optimal read performance. This data is kept eventually consistent through event consumption.

## Table of Contents

### Functional Requirements

1. [Product Management (CRUD Operations)](#1-product-management-crud-operations)
2. [Product Discovery & Search](#2-product-discovery--search)
3. [Event-Driven Integration](#3-event-driven-integration)
   - [Events Published (Outbound)](#req-31-events-published-outbound-integration)
   - [Events Consumed (Inbound)](#req-32-events-consumed-inbound-integration)
4. [Data Consistency & Validation](#4-data-consistency--validation)
5. [Administrative Features](#5-administrative-features-admin-only-operations)
   - [Statistics & Reporting](#req-51-product-statistics--reporting)
   - [Bulk Product Operations](#req-52-bulk-product-operations-amazon-style)
   - [Badge Management](#req-53-badge-management-manual-control)
   - [Size Chart Management](#req-54-size-chart-management)
   - [Restrictions & Compliance](#req-55-product-restrictions--compliance)
   - [Admin Permissions](#req-56-admin-permissions--audit)
6. [Inter-Service Communication](#6-inter-service-communication)
7. [Product Variations](#7-product-variations-parent-child-relationships)
8. [Enhanced Product Attributes](#8-enhanced-product-attributes--specifications)
9. [Product SEO & Discoverability](#9-product-seo--discoverability)
10. [Product Media Enhancement](#10-product-media-enhancement)
11. [Product Q&A Integration](#11-product-qa-integration)

### Non-Functional Requirements

- [Performance](#performance)
- [Reliability](#reliability)
- [Scalability](#scalability)
- [Security](#security)
  - [Authentication](#nfr-41-authentication)
  - [Authorization](#nfr-42-authorization)
  - [Input Validation](#nfr-43-input-validation)
  - [RBAC](#nfr-44-role-based-access-control-rbac)
  - [Secrets Management](#nfr-45-secrets-management)
- [Configuration Management](#configuration-management)
- [Observability](#observability)
  - [Distributed Tracing](#nfr-51-distributed-tracing)
  - [Logging](#nfr-52-logging)
  - [Metrics](#nfr-53-metrics)
  - [Health Checks](#nfr-54-health-checks)

### Technical Specifications

- [Data Model](#data-model) - MongoDB document schema
- [API Contracts](#api-contracts) - REST endpoints
- [Event Schemas](#event-schemas-framework-agnostic) - Pub/Sub events

### Reference

- [External Dependencies](#external-dependencies)
- [Success Criteria](#success-criteria)
- [Constraints & Assumptions](#constraints--assumptions)

---

## Functional Requirements

### 1. Product Management (CRUD Operations)

#### REQ-1.1: Create Products

- System MUST support creating new products with the following required fields:
  - Product name
  - Description
  - Price
  - SKU (Stock Keeping Unit)
  - Brand
- System MUST support optional hierarchical taxonomy fields:
  - Department (Level 1: Women, Men, Kids, Home, etc.)
  - Category (Level 2: Clothing, Shoes, Accessories, etc.)
  - Subcategory (Level 3: Tops, Dresses, Sneakers, etc.)
  - Product Type (Level 4: T-Shirts, Blouses, etc.)
- System MUST support optional product metadata:
  - Images (array of URLs)
  - Tags (array of strings for search/filtering)
  - Colors available
  - Sizes available
  - Product specifications (key-value pairs)

#### REQ-1.2: Update Products

- System MUST allow updating any product field except the product ID
- System MUST track all changes in product history with:
  - Who made the change (user ID)
  - When the change was made (timestamp)
  - What fields were changed (before/after values)
- System MUST validate that price remains non-negative on updates

#### REQ-1.3: Soft Delete Products

- System MUST support soft-deleting products (set is_active=false)
- System MUST retain all product data for audit purposes
- Deleted products MUST NOT appear in customer-facing searches or listings
- System MUST allow reactivating previously deleted products

#### REQ-1.4: Prevent Duplicate SKUs

- System MUST enforce unique SKU constraint across all active products
- System MUST validate SKU uniqueness on product creation
- System MUST validate SKU uniqueness on product updates
- System MUST validate SKU uniqueness when reactivating deleted products

### 2. Product Discovery & Search

#### REQ-2.1: Text Search

- System MUST support searching products by text across:
  - Product name
  - Product description
  - Tags
  - Brand name
- Search MUST be case-insensitive
- Search MUST support partial text matching
- Search MUST only return active products

#### REQ-2.2: Hierarchical Filtering

- System MUST support filtering by department
- System MUST support filtering by category (within a department)
- System MUST support filtering by subcategory (within a category)
- Filters MUST work in combination (department + category + subcategory)

#### REQ-2.3: Price Range Filtering

- System MUST support filtering by minimum price
- System MUST support filtering by maximum price
- System MUST support filtering by price range (min and max together)

#### REQ-2.4: Tag-Based Filtering

- System MUST support filtering products by tags
- System MUST support matching any tag in a provided list

#### REQ-2.5: Pagination & Large Dataset Handling

**Basic Pagination (Offset-Based)**:

- System MUST support paginated results for all list/search operations
- System MUST accept query parameters:
  - `page`: Page number (1-indexed, default: 1)
  - `limit` or `page_size`: Items per page (default: 20, max: 100)
- System MUST return pagination metadata:
  - `total`: Total count of matching items
  - `page`: Current page number
  - `limit`: Items per page
  - `total_pages`: Total number of pages
  - `has_next`: Boolean indicating if more pages exist
  - `has_previous`: Boolean indicating if previous page exists
- Default page size MUST be configurable per endpoint (search: 20, recommendations: 4, categories: 10)

**Cursor-Based Pagination (Efficient for Large Datasets)**:

- System MUST support cursor-based pagination for search results with > 1,000 items
- System MUST accept query parameters:
  - `cursor`: Opaque pagination token (base64 encoded)
  - `limit`: Items per page (default: 20, max: 100)
- System MUST return cursor metadata:
  - `next_cursor`: Token for next page (null if no more results)
  - `previous_cursor`: Token for previous page (null if first page)
  - `has_more`: Boolean indicating if more results exist
- Cursor MUST encode last item's sort key (e.g., timestamp + ID for uniqueness)
- Cursor-based pagination MUST NOT calculate total count (performance optimization)

**Deep Pagination Protection**:

- Offset-based pagination MUST be limited to first 10,000 results (page <= 500 with limit=20)
- Requests for pages beyond limit MUST return 400 Bad Request with message: "Use cursor-based pagination for deep pagination"
- Search results MUST encourage refinement (filters, sorting) instead of deep pagination

**Pagination for Specific Features**:

1. **Product Variations** (REQ-8):

   - Parent product with 1,000 variations MUST support pagination
   - Default: 50 variations per page
   - Endpoint: `GET /api/products/{parentId}/variations?page=1&limit=50`

2. **Bulk Import Job History** (REQ-7):

   - Import job list MUST be paginated (default: 20 jobs per page)
   - Import error report MUST be paginated if > 1,000 errors

3. **Product Badges** (REQ-10):

   - Products with badges list MUST be paginated
   - Badge assignment history MUST be paginated (audit purposes)

4. **Search Results with Facets** (REQ-9.4):
   - Facet values with > 100 options MUST be paginated (e.g., "Show more brands")
   - Facet pagination: First 10 shown, load more on demand

**Performance Requirements**:

- Pagination queries MUST use database indexes to avoid full table scans (covered in NFR-1.3)
- Offset-based pagination MUST complete within 200ms for pages 1-100
- Cursor-based pagination MUST complete within 150ms regardless of result position
- Total count calculation MUST be cached for 30 seconds for same query

**Infinite Scroll Support (for UI)**:

- API MUST support `cursor` parameter for stateless infinite scroll
- Each response MUST include `next_cursor` for loading next batch
- UI can load pages 1, 2, 3... continuously without re-fetching previous pages

#### REQ-2.6: Trending Products

- System MUST provide an endpoint to retrieve recently added products
- Default limit MUST be 4 products
- NOTE: Full trending logic (incorporating ratings, reviews, sales) MUST be implemented in Web BFF by aggregating data from Product Service and Review Service

#### REQ-2.7: Top Categories

- System MUST provide an endpoint to retrieve top categories by product count
- Default limit MUST be 5 categories
- System MUST return category metadata including product count and featured product
- NOTE: Full trending logic (incorporating ratings, reviews) MUST be implemented in Web BFF

### 3. Event-Driven Integration

Product Service follows a **Publisher & Consumer** pattern, both publishing events for downstream services and consuming events from upstream services to maintain denormalized data.

#### REQ-3.1: Events Published (Outbound Integration)

**Purpose**: Notify other services of product catalog changes for their business logic.

**Event Publishing Principles**:

- Event publishing MUST NOT block API responses (fire-and-forget pattern)
- Event publishing failures MUST be logged but MUST NOT cause API operations to fail
- Events MUST include correlation ID for distributed tracing
- All events published via Dapr Pub/Sub (broker-agnostic)

**REQ-3.1.1: Product Created Event**

- When a product is successfully created, system MUST publish a `product.created` event
- Event MUST include:
  - Product ID
  - Product name
  - Price
  - Category information
  - SKU
  - Created timestamp
  - User who created the product (if available)

**REQ-3.1.2: Product Updated Event**

- When a product is successfully updated, system MUST publish a `product.updated` event
- Event MUST include:
  - Product ID
  - Updated fields (only fields that changed)
  - Updated timestamp
  - User who updated the product (if available)

**REQ-3.1.3: Product Deleted Event**

- When a product is soft-deleted, system MUST publish a `product.deleted` event
- Event MUST include:
  - Product ID
  - Deletion type (soft delete indicator)
  - Deleted timestamp
  - User who deleted the product (if available)

**REQ-3.1.4: Product Price Changed Event**

- When product price is updated, system MUST publish a `product.price.changed` event
- Event MUST include:
  - Product ID
  - Old price
  - New price
  - Changed timestamp

**REQ-3.1.5: Back in Stock Event**

- When product transitions from "Out of Stock" to "In Stock", system MUST publish `product.back.in.stock` event
- Event consumed by Notification Service for customer alerts

**REQ-3.1.6: Badge Assignment Events**

- When badge is auto-assigned, system MUST publish `product.badge.auto.assigned` event
- When badge is auto-removed, system MUST publish `product.badge.auto.removed` event

**REQ-3.1.7: Bulk Import Events**

- When bulk import job is created, system MUST publish `product.bulk.import.job.created` event (consumed by own worker)
- During import, system MUST publish `product.bulk.import.progress` events (every 10 seconds)
- When import completes, system MUST publish `product.bulk.import.completed` or `product.bulk.import.failed` event

**Event Consumers** (Services that consume Product Service events):

- **Audit Service**: All product events for audit logging
- **Notification Service**: price.changed, back.in.stock events for customer notifications
- **Order Service**: Validates product existence before order creation
- **Search Service** (future): Indexes product changes for search optimization

---

#### REQ-3.2: Events Consumed (Inbound Integration)

**Purpose**: Maintain denormalized data from other services for optimal read performance and reduced latency.

**Event Consumption Principles**:

- All consumed data follows **eventual consistency** model (not transactional)
- Denormalized data MAY be stale for 5-30 seconds
- Event handlers MUST be idempotent (handle duplicate events gracefully)
- Event processing MUST NOT block publisher services
- All event subscriptions via Dapr Pub/Sub (broker-agnostic)

**REQ-3.2.1: Review Data Synchronization**

**Event Sources**: Review Service

**Events Consumed**:

- `review.created` - New review submitted
- `review.updated` - Review rating/content changed
- `review.deleted` - Review removed

**Denormalized Data Maintained**:

- Average rating (1-5 stars, decimal precision)
- Total review count
- Rating distribution (5-star count, 4-star count, 3-star, 2-star, 1-star)
- Verified purchase review count

**Requirements**:

- Aggregate data MUST be updated within **5 seconds** of review event receipt
- Product API responses MUST include review aggregates in product detail
- Search/filter MUST support sorting by average rating
- Search/filter MUST support filtering by minimum rating (e.g., 4+ stars only)
- System MUST handle review deletion gracefully (recalculate aggregates)

---

**REQ-3.2.2: Inventory Availability Synchronization**

**Event Sources**: Inventory Service

**Events Consumed**:

- `inventory.stock.updated` - Stock quantity changed
- `inventory.reserved` - Inventory reserved for order
- `inventory.released` - Reserved inventory released

**Denormalized Data Maintained**:

- **In Stock**: Available quantity > 0
- **Low Stock**: Available quantity > 0 AND available quantity <= low stock threshold (default: 10)
- **Out of Stock**: Available quantity = 0
- **Pre-Order**: Available date is in the future
- **Discontinued**: Product marked as discontinued by Inventory Service

**Requirements**:

- Availability status MUST be updated within **10 seconds** of inventory event
- Availability status MUST be reflected in search results immediately after update
- Product variations MUST track availability per child SKU
- Search/filter MUST support filtering by availability status
- Out of stock products MAY be shown with "Notify Me" option (UI decision)
- System MUST publish `product.back.in.stock` event when transitioning from "Out of Stock" to "In Stock"

---

**REQ-3.2.3: Sales Metrics & Badge Automation**

**Event Sources**: Analytics Service

**Events Consumed**:

- `analytics.product.sales.updated` - Sales volume metrics updated
- `analytics.product.views.updated` - Product views metrics updated
- `analytics.product.conversions.updated` - Conversion rate metrics updated

**Automated Badge Assignment**:

**Best Seller Badge**:

- Auto-assign to top 100 products in category by sales volume (last 30 days)
- Auto-remove when product drops below top 100
- Refresh every 1 hour

**Trending Badge**:

- Auto-assign when product views increase by 50%+ in last 7 days vs prior 7 days
- Auto-remove when view growth drops below 30%
- Refresh every 1 hour

**Hot Deal Badge**:

- Auto-assign when conversion rate > category average + 20%
- Auto-remove when conversion rate drops below category average + 10%
- Refresh every 6 hours

**Requirements**:

- Badge assignment MUST be fully automated (no manual admin action required)
- Badge expiration MUST auto-refresh based on current metrics
- System MUST publish `product.badge.auto.assigned` event when auto-assigning badges
- System MUST publish `product.badge.auto.removed` event when auto-removing badges
- Admin MUST be able to view badge assignment criteria and current metrics

---

**REQ-3.2.4: Q&A Statistics Synchronization**

**Event Sources**: Q&A Service

**Events Consumed**:

- `product.question.created` - New question submitted
- `product.answer.created` - Question answered
- `product.question.deleted` - Question removed

**Denormalized Data Maintained**:

- Total question count
- Answered question count

**Requirements**:

- Q&A stats MUST be updated within **5 seconds** of Q&A event receipt
- Product detail pages MUST display question count
- System MUST NOT store full question/answer content (managed by Q&A Service)

---

**REQ-3.2.5: Bulk Import Background Processing**

**Event Sources**: Self (Product Service)

**Events Consumed**:

- `product.bulk.import.job.created` - Bulk import job initiated by API

**Background Worker Pattern**:

- Worker MUST NOT block API responses (fire-and-forget pattern)
- Worker MUST process imports in batches (100 products per batch)
- Progress update after each batch completion
- Commit strategy: Per batch (partial success allowed in "partial-import" mode)

**Error Handling**:

- **Validation errors**: Skip row, log error, continue processing
- **Database errors**: Retry 3 times with exponential backoff, then fail
- **Fatal errors**: Stop processing, mark job as failed

**Job Cancellation**:

- Admin can cancel in-progress import jobs
- Worker checks cancellation flag every batch
- Partial results preserved (already imported products not rolled back)

**Progress Events Published**:

- `product.bulk.import.progress` - Every 10 seconds with current count
- `product.bulk.import.completed` - When job finishes successfully
- `product.bulk.import.failed` - When job fails fatally
- `product.bulk.import.cancelled` - When admin cancels job

**Scalability**:

- Worker MUST be horizontally scalable (multiple worker instances)
- Job assignment MUST use distributed locking (prevent duplicate processing)

### 4. Data Consistency & Validation

#### REQ-4.1: Price Validation

- Product price MUST be non-negative (>= 0)
- System MUST validate price on create and update operations

#### REQ-4.2: Required Field Validation

- System MUST validate that all required fields are provided on creation
- System MUST return clear error messages for validation failures

#### REQ-4.3: SKU Format Validation

- System MUST validate SKU format if business rules are defined
- System MUST accept alphanumeric SKUs

#### REQ-4.4: Data Persistence

- All product operations (create, update, delete) MUST be immediately consistent
- Product reads MUST always return the most recent data

### 5. Administrative Features (Admin-Only Operations)

This section consolidates all administrative operations for catalog management, including bulk operations, manual badge assignment, size chart management, and compliance configuration.

#### REQ-5.1: Product Statistics & Reporting

- System MUST provide an endpoint returning:
  - Total products count
  - Active products count
  - Inactive products count
- NOTE: Stock-related statistics (low stock, out of stock) are managed by Inventory Service
- System MUST maintain complete history of all product changes
- History MUST include timestamp, user, and changed fields
- History MUST be retrievable via API

#### REQ-5.2: Bulk Product Operations (Amazon-Style)

See also REQ-3.2.5 for background worker implementation details.

**REQ-5.2.1: Template Download**

- System MUST provide downloadable Excel template for bulk product import
- Templates MUST be category-specific (e.g., "Clothing Template", "Electronics Template")
- Template MUST include:
  - All required and optional fields with descriptions
  - Field validation rules and constraints
  - Example rows with sample data
  - Column headers matching product attributes
- Template MUST support product variation import (parent-child relationships)
- System MUST provide template version control for backward compatibility

**REQ-5.2.2: Bulk Product Import**

- System MUST support importing products from Excel (.xlsx, .xls) files
- System MUST validate all rows before processing any imports
- System MUST provide detailed validation error report with:
  - Row number, field name, error description, suggested correction
- System MUST support partial import mode (skip invalid rows, import valid ones)
- System MUST support all-or-nothing mode (rollback if any row fails)
- Import MUST support up to 10,000 products per file
- Import MUST be processed asynchronously (background job)
- System MUST provide real-time progress updates during import
- System MUST notify admin when import completes (success/failure)
- System MUST generate import summary report

**REQ-5.2.3: Image Handling for Bulk Import**

- System MUST support two image upload methods:
  - **Method 1**: Image URLs in import file (direct CDN links)
  - **Method 2**: Separate bulk image upload via ZIP file
- For ZIP upload, system MUST match filenames to SKUs automatically: `{SKU}-{sequence}.{ext}`
- System MUST validate image formats (JPEG, PNG, WebP), sizes (max 10MB), and count (max 10 per product)

**REQ-5.2.4: Import Status Tracking**

- Admin MUST be able to view import job history with:
  - Job ID, status, filename, timestamps, row counts, user info
- System MUST provide downloadable error reports for failed imports
- System MUST allow retrying failed imports
- Import history MUST be preserved for 90+ days for audit

**REQ-5.2.5: Bulk Update Operations**

- System MUST support bulk price/attribute updates via Excel
- System MUST support bulk status changes (activate/deactivate)
- Bulk updates MUST follow same validation as bulk import
- System MUST publish events for each updated product

#### REQ-5.3: Badge Management (Manual Control)

**Note**: Automated badge assignment via analytics is covered in REQ-3.2.3

**REQ-5.3.1: Manual Badge Assignment**

- Admin MUST be able to manually assign/remove badges
- Admin MUST be able to set badge expiration dates
- Admin MUST be able to override auto-assigned badges
- System MUST allow bulk badge assignment
- System MUST maintain badge history
- Badge operations MUST NOT trigger product.updated events (use badge-specific events)

**REQ-5.3.2: Badge Types & Properties**

Supported badge types: Best Seller (auto), New Arrival (auto), Limited Time Deal (manual), Featured (manual), Trending (auto), Exclusive (manual), Low Stock (auto), Back in Stock (auto), Pre-Order (manual), Clearance (manual), Eco-Friendly (manual), Custom (manual)

Each badge MUST have:

- Type, display text, style, priority, validity period, visibility rules, scope, source (manual/auto)

**REQ-5.3.3: Badge Monitoring**

- Admin MUST be able to view all products with specific badge
- Admin MUST be able to view auto-assignment criteria
- Admin MUST receive alerts when badges expire

#### REQ-5.4: Size Chart Management

**REQ-5.4.1: Size Chart Creation & Assignment**

- Admin MUST be able to create/update size charts per category
- Size charts MUST support multiple formats: Image (PNG, JPG), PDF, Structured JSON
- Size charts MUST support regional sizing: US, EU, UK, Asian
- Size charts MUST be reusable across categories
- Product variations MUST reference parent's size chart
- Product API MUST include size chart reference

**REQ-5.4.2: Size Chart Templates**

- System SHOULD provide standard templates for common categories
- Admin MUST be able to customize templates
- System MUST version control size charts

#### REQ-5.5: Product Restrictions & Compliance

**REQ-5.5.1: Age Restrictions**

- Admin MUST be able to set age restrictions: None, 18+, 21+, Custom
- Age-restricted products MUST be filtered if user age unknown
- Product API MUST return age restriction

**REQ-5.5.2: Shipping Restrictions**

- Admin MUST be able to configure: Hazmat, Oversized, Perishable, International restricted, Regional restricted, Ground only
- Restrictions MUST be exposed to Order Service
- Products MUST display shipping limitation messages

**REQ-5.5.3: Regional Availability**

- Admin MUST be able to configure: Available countries, states/provinces, regions
- Products MUST be filtered by customer location
- Regional availability MUST integrate with shipping restrictions

**REQ-5.5.4: Compliance Metadata**

- Admin MUST be able to add: Certifications, safety warnings, ingredient disclosures, country of origin, warranty
- Compliance data MUST be searchable and displayed on product pages
- System MUST validate required compliance fields by category

#### REQ-5.6: Admin Permissions & Audit

- All admin operations MUST require admin role
- System MUST validate permissions before operations
- All admin operations MUST be logged with: user ID, operation type, timestamp, IP, changed data
- Audit logs MUST be immutable and retrievable for compliance

### 6. Inter-Service Communication

#### REQ-6.1: Product Existence Check

- System MUST provide endpoint for other services to verify if a product exists
- Check MUST only return true for active products
- Endpoint MUST be optimized for low latency (used frequently)

### 7. Product Variations (Parent-Child Relationships)

#### REQ-8.1: Variation Structure

- System MUST support parent-child product relationships
- Parent product MUST define:
  - Variation theme (e.g., "Color-Size", "Style-Color", "Size")
  - Common attributes shared by all children
  - Base product information (name, description, brand, category)
- Child products (variations) MUST have:
  - Unique SKU
  - Specific variation attributes (e.g., color=Black, size=L)
  - Individual price (can differ from parent)
  - Individual images (variation-specific)
  - Reference to parent product ID
- System MUST support up to 1,000 variations per parent product
- System MUST support multiple variation themes:
  - Single-dimension: Color only, Size only, Style only
  - Two-dimension: Color-Size, Style-Color, Size-Material
  - Custom: Any combination of attributes

#### REQ-8.2: Variation Attributes

- System MUST support standard variation attributes:
  - Color (with color code/hex value)
  - Size (with size chart reference)
  - Style (design variation)
  - Material (fabric/composition)
  - Scent (for applicable products)
  - Flavor (for food products)
  - Custom attributes (category-specific)
- Each variation attribute MUST have:
  - Display name (customer-facing)
  - Internal value (system reference)
  - Sort order (for consistent display)

#### REQ-8.3: Variation Inheritance

- Child products MUST inherit from parent:
  - Brand
  - Department/Category/Subcategory
  - Base description (can be extended)
  - Tags (can be extended)
  - Product specifications (can be overridden)
- Child products MUST NOT inherit:
  - SKU (must be unique)
  - Price (variation-specific)
  - Images (variation-specific)
  - Stock quantity (managed by Inventory Service)

#### REQ-8.4: Variation Display and Selection

- System MUST return all available variations when querying parent product
- System MUST support filtering variations by attribute values
- System MUST indicate availability status for each variation
- System MUST provide variation matrix for API consumers:
  ```json
  {
    "parentId": "parent-123",
    "variations": [
      { "sku": "child-1", "color": "Black", "size": "S", "available": true },
      { "sku": "child-2", "color": "Black", "size": "M", "available": true }
    ]
  }
  ```
- Search results MAY return either parent products or individual variations based on search context

#### REQ-8.5: Variation Management

- Admin MUST be able to create parent product with variations in single operation
- Admin MUST be able to add new variations to existing parent
- Admin MUST be able to update variation attributes
- Admin MUST be able to remove variations (soft delete)
- System MUST validate variation uniqueness (no duplicate color-size combinations)
- Bulk import MUST support parent-child relationship specification

### 8. Enhanced Product Attributes & Specifications

#### REQ-8.1: Structured Attribute Schema

- System MUST support category-specific attribute schemas
- Each category MUST define:
  - Required attributes
  - Optional attributes
  - Attribute data types (string, number, boolean, list, object)
  - Validation rules (min/max, allowed values, regex patterns)
- System MUST validate product attributes against category schema on create/update
- System MUST provide API to retrieve category attribute schema

#### REQ-8.2: Common Attribute Categories

System MUST support these standard attribute categories:

**Physical Dimensions**:

- Length, Width, Height (with units: inches, cm, meters)
- Weight (with units: pounds, kg, grams)
- Volume (with units: liters, gallons, ml)

**Materials & Composition**:

- Primary material
- Secondary materials
- Material percentages (for blends)
- Certifications (organic, fair-trade, etc.)

**Care Instructions**:

- Washing instructions (machine/hand wash, temperature)
- Drying instructions (tumble dry, air dry, dry clean)
- Ironing instructions
- Special care notes

**Product Features**:

- Feature list (bullet points)
- Technology features (for electronics)
- Comfort features (for apparel)
- Safety features

**Technical Specifications**:

- Model number
- Year released
- Country of origin
- Manufacturer part number
- GTIN/UPC/EAN codes
- Warranty information

**Sustainability & Ethics**:

- Eco-friendly certifications
- Recycled content percentage
- Carbon footprint data
- Ethical sourcing information

#### REQ-9.3: Category-Specific Attributes

System MUST support specialized attributes for major categories:

**Clothing**:

- Fit type (Regular, Slim, Relaxed, Oversized)
- Neckline style (Crew, V-neck, Collar, etc.)
- Sleeve length (Short, Long, 3/4, Sleeveless)
- Rise (for pants: Low, Mid, High)
- Pattern (Solid, Striped, Printed, etc.)
- Occasion (Casual, Formal, Athletic, etc.)
- Season (Spring, Summer, Fall, Winter, All-season)

**Electronics**:

- Brand and model
- Processor/chipset
- Memory/storage capacity
- Display specifications (size, resolution, type)
- Connectivity options (WiFi, Bluetooth, ports)
- Battery capacity and life
- Operating system
- Color options
- Warranty duration

**Home & Furniture**:

- Room type (Living room, Bedroom, Kitchen, etc.)
- Assembly required (Yes/No)
- Number of pieces
- Style (Modern, Traditional, Rustic, etc.)
- Upholstery material
- Load capacity/weight limit

**Beauty & Personal Care**:

- Skin type (Oily, Dry, Combination, Sensitive)
- Ingredient highlights
- Fragrance type
- SPF rating (for sunscreen)
- Volume/quantity
- Expiration/shelf life

#### REQ-9.4: Attribute-Based Search and Filtering

- System MUST support filtering products by any defined attribute
- System MUST support multi-select attribute filtering (e.g., multiple colors, multiple sizes)
- System MUST provide faceted search results showing:
  - Available attribute values
  - Count of products for each attribute value
  - Applied filters
- System MUST support attribute-based sorting
- Attribute filters MUST work in combination with text search and category filters

#### REQ-9.5: Attribute Validation

- System MUST validate attribute values against schema constraints
- System MUST reject invalid attribute values with clear error messages
- System MUST provide suggested values for attributes with predefined lists
- System MUST support custom validation rules per category

### 9. Product SEO & Discoverability

#### REQ-9.1: SEO Metadata

Each product MUST support:

- **Meta Title**: SEO-optimized page title (60-70 characters recommended)
- **Meta Description**: Search engine description (150-160 characters recommended)
- **Meta Keywords**: Relevant search keywords (comma-separated)
- **URL Slug**: SEO-friendly URL identifier (e.g., `premium-cotton-t-shirt-black`)
- **Canonical URL**: Primary URL for the product (prevents duplicate content issues)
- **Open Graph Tags**: Social media sharing metadata
  - OG Title
  - OG Description
  - OG Image URL
  - OG Type (product)
- **Structured Data**: Schema.org Product markup support

#### REQ-11.2: URL Slug Generation

- System MUST auto-generate URL slug from product name on creation
- Slug MUST be:
  - Lowercase
  - Alphanumeric with hyphens (no spaces or special characters)
  - Unique across all products
  - Maximum 100 characters
- Admin MUST be able to customize slug manually
- System MUST validate slug uniqueness
- System MUST maintain slug history for redirects (if slug changes)

#### REQ-11.3: Search Indexing Support

- System MUST provide fields optimized for search engine indexing:
  - Primary keywords (most important search terms)
  - Secondary keywords (related terms)
  - Long-tail keywords (specific search phrases)
- System MUST support custom meta tag injection for advanced SEO
- System MUST provide sitemap generation support for product URLs

#### REQ-11.4: Product Discoverability

- System MUST maintain product discoverability score based on:
  - Completeness of product information (all fields filled)
  - Quality of images (number and resolution)
  - Richness of description (word count, formatting)
  - Attribute completeness (all category attributes defined)
  - Review count and ratings (from Review Service integration)
- Score MUST be available via API for search ranking
- Admin MUST be able to view discoverability score and improvement suggestions

#### REQ-11.5: Multi-Language SEO Support

- System MUST support storing SEO metadata in multiple languages
- Each language variant MUST have:
  - Translated meta title
  - Translated meta description
  - Language-specific URL slug
  - Language-specific canonical URL
- System MUST support language fallback (default to primary language if translation missing)

**Note**: Full multi-language product content is future scope; this requirement focuses on SEO metadata only

#### REQ-11.6: SEO Best Practices Validation

- System SHOULD validate SEO metadata against best practices:
  - Meta title length warning (> 70 characters)
  - Meta description length warning (> 160 characters)
  - Duplicate meta titles across products
  - Missing meta descriptions
  - Slug readability score
- System SHOULD provide SEO health dashboard for admins

### 10. Product Media Enhancement

#### REQ-10.1: Product Videos

- System MUST support product video URLs (in addition to images)
- System MUST support video sources:
  - YouTube URLs (embedded player)
  - Vimeo URLs (embedded player)
  - Direct CDN URLs (MP4, WebM formats)
  - Amazon S3/Azure Blob Storage URLs
- Each product MUST support up to 5 videos
- Videos MUST be ordered:
  - Primary video (position 0)
  - Secondary videos (positions 1-4)
- Video metadata MUST include:
  - URL (required)
  - Video source type (youtube, vimeo, cdn)
  - Thumbnail URL (optional, auto-generated from video if possible)
  - Duration in seconds (optional)
  - Title/description (optional)
- Product API MUST return videos in order
- Admin MUST be able to reorder videos via drag-and-drop (UI feature)
- Videos MUST be validated for accessibility (URL returns 200 OK)

#### REQ-13.2: Enhanced Image Support

- System MUST support up to 10 images per product (increased from current limit)
- Images MUST support multiple resolutions:
  - Thumbnail (150x150)
  - Medium (600x600)
  - Large (1500x1500)
  - Original (full resolution)
- Image metadata MUST include:
  - Alt text (for accessibility and SEO)
  - Caption (optional)
  - Image type (product shot, lifestyle, infographic, size guide)
- 360° product view images MUST be supported (sequence of images for rotation)

### 11. Product Q&A Integration

#### REQ-11.1: Q&A Data Denormalization

- System MUST store denormalized Q&A count per product
- System MUST consume `product.question.created` events from Q&A Service
- System MUST consume `product.question.deleted` events from Q&A Service
- System MUST consume `product.answer.created` events from Q&A Service
- System MUST maintain:
  - Total question count
  - Answered question count
  - Unanswered question count
- Q&A counts MUST be updated within 30 seconds of Q&A event
- Product API MUST return Q&A counts in product detail response
- Search results MAY display Q&A count (UI decision)

#### REQ-14.2: Q&A Search Integration

- System MUST index Q&A text for product search (if provided in events)
- Customer search SHOULD return products where query matches:
  - Product name/description (primary)
  - Product Q&A questions/answers (secondary boost)
- Admin MUST be able to see which Q&A content is indexed per product

## Non-Functional Requirements

### Performance

#### NFR-1.1: API Response Times

- Read operations (get, list, search) MUST respond within 200ms (p95)
- Write operations (create, update, delete) MUST respond within 500ms (p95)
- Event publishing MUST NOT add more than 50ms to API response time

#### NFR-1.2: Throughput

- System MUST handle 1,000 requests per second during normal load
- System MUST handle 5,000 requests per second during peak load (sales events)

#### NFR-1.3: Database Performance

- Product searches MUST be optimized with database indexes
- Text search MUST use database text indexes where available
- Pagination queries MUST be optimized to avoid full table scans

### Reliability

#### NFR-2.1: Availability

- System MUST maintain 99.9% uptime
- Planned maintenance windows MUST be communicated in advance

#### NFR-2.2: Error Handling

- All errors MUST be logged with context (product ID, operation, user)
- Errors MUST return appropriate HTTP status codes
- Error messages MUST be clear and actionable

#### NFR-2.3: Event Publishing Resilience

- Event publishing failures MUST NOT cause product operations to fail
- Failed event publishes MUST be retried automatically (handled by messaging infrastructure)
- All event publishing attempts MUST be logged

#### NFR-2.4: Database Resilience

- System MUST handle temporary database connection failures gracefully
- System MUST return 503 Service Unavailable on database connection errors
- Database connection pool MUST be configured for resilience

### Scalability

#### NFR-3.1: Horizontal Scaling

- Service MUST be stateless to support horizontal scaling
- Multiple instances MUST be able to run concurrently
- No instance-specific state MUST be maintained

#### NFR-3.2: Data Growth

- System MUST efficiently handle 1 million+ products
- Performance MUST NOT degrade significantly with catalog growth
- Database indexes MUST be optimized for large datasets

### Security

#### NFR-4.1: Authentication

- All API endpoints MUST validate JWT tokens
- Invalid or expired tokens MUST result in 401 Unauthorized

#### NFR-4.2: Authorization

- Admin operations MUST verify admin role from JWT token
- Non-admin users MUST receive 403 Forbidden for admin operations

#### NFR-4.3: Input Validation

- All user inputs MUST be validated and sanitized
- SQL injection and NoSQL injection MUST be prevented
- Product ID validation MUST prevent injection attacks

#### NFR-4.4: Role-Based Access Control (RBAC)

**Roles:**

- **Customer**: General public users (unauthenticated or authenticated customers)

  - Read access to active products only
  - Can view product details, search, filter by attributes
  - No access to admin operations
  - No access to soft-deleted or draft products
  - No access to admin-only endpoints

- **Admin**: System administrators with full control over product catalog
  - Full CRUD on products (create, read, update, delete)
  - Manage product variations, attributes, and media
  - Bulk import/export operations (REQ-5.2)
  - Assign and manage manual badges (REQ-5.3)
  - Configure size charts (REQ-5.4)
  - Configure product restrictions and compliance settings (REQ-5.5)
  - View product statistics and reports (REQ-5.1)
  - Access audit logs (REQ-5.6)
  - Manage badge automation rules
  - Permanent product deletion (hard delete)
  - System configuration access

**Permission Matrix:**

| Operation                            | Customer | Admin |
| ------------------------------------ | -------- | ----- |
| GET /products (active only)          | ✅       | ✅    |
| GET /products/:id (active)           | ✅       | ✅    |
| GET /products (with status filter)   | ❌       | ✅    |
| GET /products/:id (draft/deleted)    | ❌       | ✅    |
| POST /products                       | ❌       | ✅    |
| PUT /products/:id                    | ❌       | ✅    |
| PATCH /products/:id                  | ❌       | ✅    |
| DELETE /products/:id (soft)          | ❌       | ✅    |
| DELETE /products/:id (hard)          | ❌       | ✅    |
| POST /products/bulk/import           | ❌       | ✅    |
| GET /products/bulk/status/:jobId     | ❌       | ✅    |
| GET /products/statistics             | ❌       | ✅    |
| POST /products/:id/badges            | ❌       | ✅    |
| DELETE /products/:id/badges/:badgeId | ❌       | ✅    |
| POST /products/:id/restrictions      | ❌       | ✅    |
| POST /products/:id/variations        | ❌       | ✅    |
| GET /audit/products                  | ❌       | ✅    |

**Implementation Requirements:**

- JWT token MUST include `role` claim (either "customer" or "admin")
- Authorization middleware MUST check role before granting access
- API responses MUST return 403 Forbidden for insufficient permissions
- All admin endpoints MUST log user ID and action for audit trail
- Unauthenticated requests default to "customer" role (read-only public access)

#### NFR-4.5: Secrets Management

**Sensitive Data:**

Product Service handles the following sensitive configuration:

- **Database Credentials**: MongoDB connection string (username, password, host, port)
- **JWT Signing Keys**: Public keys for JWT token verification
- **Message Broker Credentials**: RabbitMQ/Event broker authentication
- **External API Keys**: Third-party service integrations (if any)

**Requirements:**

- Secrets MUST NOT be stored in source code or committed to version control
- Secrets MUST be injected at runtime via environment variables or secrets management service
- Database connection strings MUST use secure protocols (TLS/SSL)
- Secrets MUST be rotated periodically (recommended: every 90 days)
- Logging MUST NOT expose secrets (mask credentials in logs)
- Error messages MUST NOT leak sensitive configuration details

**Recommended Implementation:**

- Use Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault for secret storage
- Mount secrets as environment variables in container/pod configuration
- Use Kubernetes Secrets or Docker Secrets for orchestration environments
- Implement secret rotation without service downtime

### Configuration Management

#### NFR-4.6: External Configuration

**Configuration Categories:**

1. **Application Configuration** (can be externalized):

   - Server port, host binding
   - Log levels (debug, info, warning, error)
   - CORS allowed origins
   - Rate limiting thresholds
   - Pagination defaults (page sizes per endpoint)
   - Cache TTL values
   - Worker thread pool sizes

2. **Database Configuration**:

   - MongoDB connection string (from secrets)
   - Connection pool size (min/max)
   - Query timeout values
   - Retry policies (max attempts, backoff strategy)

3. **Event/Messaging Configuration**:

   - Message broker URL (from secrets)
   - Topic/queue names
   - Consumer group IDs
   - Message retry policies
   - Dead letter queue configuration

4. **Feature Flags** (optional):
   - Enable/disable badge automation
   - Enable/disable bulk import
   - Enable/disable denormalized data sync

**Configuration Sources (Priority Order)**:

1. **Environment Variables** (highest priority) - for container/cloud deployments
2. **Configuration Files** (`config.json`, `appsettings.json`) - for local development
3. **Default Values** (lowest priority) - hardcoded fallbacks

**Requirements:**

- Configuration MUST be environment-specific (dev, staging, production)
- Configuration changes MUST NOT require code redeployment
- Sensitive configuration (secrets) MUST be loaded from secure storage
- Configuration validation MUST happen at startup (fail fast on invalid config)
- Service MUST log active configuration on startup (mask secrets)

**Example Environment Variables:**

```bash
# Server
PORT=8003
NODE_ENV=production
LOG_LEVEL=info

# Database (from secrets manager)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/products
MONGODB_POOL_MIN=10
MONGODB_POOL_MAX=50

# Message Broker (from secrets manager)
RABBITMQ_URL=amqp://username:password@broker.example.com:5672
PRODUCT_EVENTS_TOPIC=product.events
CONSUMER_GROUP_ID=product-service

# Feature Flags
ENABLE_BADGE_AUTOMATION=true
ENABLE_BULK_IMPORT=true

# Pagination Defaults
SEARCH_PAGE_SIZE=20
RECOMMENDATIONS_PAGE_SIZE=4
ADMIN_PAGE_SIZE=50
```

### Observability

#### NFR-5.1: Distributed Tracing

- All incoming requests MUST generate or propagate correlation IDs
- All outgoing calls (database, events) MUST include correlation IDs
- System MUST support distributed tracing across service boundaries

#### NFR-5.2: Logging

- All business operations MUST be logged with appropriate context
- Log levels MUST be configurable (debug, info, warning, error)
- Logs MUST use structured format (JSON) for easy parsing
- Logs MUST include:
  - Timestamp (ISO 8601 format)
  - Log level
  - Event type / operation name
  - Correlation ID (request tracking)
  - User ID (if available)
  - Error details (if applicable)
  - Service name / version
  - Environment (dev, staging, prod)

**Correlation ID Requirements:**

- Service MUST check for `X-Correlation-ID` header on incoming requests
- If header exists, use the provided correlation ID
- If header is missing, generate a new UUID v4 correlation ID
- Correlation ID MUST be included in:
  - All log entries for that request
  - All outgoing HTTP calls (as `X-Correlation-ID` header)
  - All published events (in event metadata)
  - All database query logs
  - Response headers (echo back to caller)

**Structured Logging Example:**

```json
{
  "timestamp": "2025-11-03T14:32:10.123Z",
  "level": "info",
  "service": "product-service",
  "version": "1.2.0",
  "environment": "production",
  "correlationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "userId": "user-12345",
  "operation": "CreateProduct",
  "duration": 45,
  "statusCode": 201,
  "message": "Product created successfully",
  "metadata": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "price": 29.99
  }
}
```

**Logging Levels:**

- **DEBUG**: Detailed diagnostic information (disabled in production)
- **INFO**: Business operations, successful operations
- **WARNING**: Validation failures, retryable errors, deprecated API usage
- **ERROR**: System errors, failed operations, exceptions

**What NOT to Log:**

- Passwords, API keys, or secrets
- Complete JWT tokens (log only user ID from token)
- Credit card numbers or PII
- Full database connection strings

#### NFR-5.3: Metrics

- System MUST expose health check endpoints
- System MUST expose metrics for monitoring:
  - **Request Metrics**:
    - Request count by endpoint and HTTP method
    - Request latency by endpoint (p50, p95, p99)
    - Error count by type (4xx, 5xx)
    - Request rate (requests per second)
  - **Database Metrics**:
    - Query performance (execution time)
    - Connection pool utilization
    - Query error rate
    - Document read/write counts
  - **Event Metrics**:
    - Events published (count by event type)
    - Events consumed (count by event type)
    - Event processing latency
    - Event consumer lag
    - Dead letter queue depth
  - **Business Metrics**:
    - Product CRUD operations (count by operation type)
    - Bulk import job success/failure rate
    - Badge assignment/removal counts
    - Search query performance
- Metrics MUST be exposed in Prometheus format
- Metrics endpoint: `/metrics` (accessible without authentication for scraping)

**Alerting Thresholds (Recommendations):**

- Error rate > 5% for 5 minutes → Alert
- P95 latency > 500ms for 5 minutes → Alert
- Event consumer lag > 1000 messages → Alert
- Database connection pool exhausted → Critical Alert
- Health check failures for 2 minutes → Critical Alert

#### NFR-5.4: Health Checks

- System MUST provide /health endpoint for liveness checks
- System MUST provide /health/ready endpoint for readiness checks
- Health check MUST verify database connectivity

## Data Model

### Product Document Schema (MongoDB)

Product Service stores product data in MongoDB with the following structure. This includes both source-of-truth data (owned by Product Service) and denormalized data (synchronized from other services via event consumption).

```json
{
  "_id": "507f1f77bcf86cd799439011",

  // === CORE PRODUCT DATA (Source of Truth) ===
  "name": "Premium Cotton T-Shirt",
  "description": "Comfortable 100% cotton t-shirt with modern fit",
  "longDescription": "This premium cotton t-shirt features...",
  "price": 29.99,
  "compareAtPrice": 39.99,
  "sku": "TS-BLK-001",
  "brand": "TrendyWear",
  "status": "active",

  // === TAXONOMY (Hierarchical Categories) ===
  "taxonomy": {
    "department": "Men",
    "category": "Clothing",
    "subcategory": "Tops",
    "productType": "T-Shirts"
  },

  // === PRODUCT VARIATIONS (Parent-Child) ===
  "variationType": "parent",
  "parentId": null,
  "variationAttributes": ["color", "size"],
  "childSkus": ["TS-BLK-001-S", "TS-BLK-001-M", "TS-BLK-001-L", "TS-RED-001-S", "TS-RED-001-M", "TS-RED-001-L"],
  "childCount": 6,

  // === ATTRIBUTES & SPECIFICATIONS ===
  "attributes": {
    "color": "Black",
    "size": "Medium",
    "material": "100% Cotton",
    "fit": "Regular Fit",
    "care": "Machine wash cold"
  },
  "specifications": [
    { "name": "Weight", "value": "200g", "unit": "grams" },
    { "name": "Fabric", "value": "Jersey Knit", "unit": null }
  ],

  // === MEDIA ===
  "images": [
    {
      "url": "https://cdn.aioutlet.com/products/ts-001-front.jpg",
      "alt": "Front view of black t-shirt",
      "isPrimary": true,
      "order": 1
    },
    {
      "url": "https://cdn.aioutlet.com/products/ts-001-back.jpg",
      "alt": "Back view of black t-shirt",
      "isPrimary": false,
      "order": 2
    }
  ],
  "videos": [
    {
      "url": "https://youtube.com/watch?v=abc123",
      "platform": "youtube",
      "title": "Product Overview",
      "duration": 120
    }
  ],

  // === BADGES & LABELS (Manual + Automated) ===
  "badges": [
    {
      "type": "best-seller",
      "label": "Best Seller",
      "priority": 1,
      "expiresAt": null,
      "source": "auto",
      "assignedAt": "2025-11-01T00:00:00Z"
    },
    {
      "type": "limited-edition",
      "label": "Limited Edition",
      "priority": 2,
      "expiresAt": "2025-12-31T23:59:59Z",
      "source": "manual",
      "assignedBy": "admin-user-123",
      "assignedAt": "2025-11-03T10:00:00Z"
    }
  ],

  // === SEO METADATA ===
  "seo": {
    "metaTitle": "Premium Cotton T-Shirt - Comfortable & Stylish | AIOutlet",
    "metaDescription": "Shop our premium cotton t-shirt...",
    "metaKeywords": ["cotton t-shirt", "men's clothing", "casual wear"],
    "slug": "premium-cotton-tshirt-black",
    "canonicalUrl": "https://aioutlet.com/products/premium-cotton-tshirt-black"
  },

  // === RESTRICTIONS & COMPLIANCE ===
  "restrictions": {
    "ageRestricted": false,
    "minimumAge": null,
    "shippingRestrictions": [],
    "hazardousMaterial": false
  },

  // === SIZE CHART REFERENCE ===
  "sizeChartId": "standard-mens-apparel",

  // === DENORMALIZED DATA (From Other Services) ===

  // From Review Service (REQ-12.1)
  "reviewAggregates": {
    "averageRating": 4.5,
    "totalReviewCount": 128,
    "verifiedPurchaseCount": 95,
    "ratingDistribution": {
      "5": 75,
      "4": 30,
      "3": 15,
      "2": 5,
      "1": 3
    },
    "lastUpdated": "2025-11-03T09:45:00Z"
  },

  // From Inventory Service (REQ-12.2)
  "availabilityStatus": {
    "status": "in-stock",
    "availableQuantity": 150,
    "lowStockThreshold": 10,
    "isLowStock": false,
    "lastUpdated": "2025-11-03T09:50:00Z"
  },

  // From Q&A Service (REQ-14)
  "qaStats": {
    "totalQuestions": 23,
    "answeredQuestions": 20,
    "lastUpdated": "2025-11-03T09:30:00Z"
  },

  // === AUDIT FIELDS ===
  "createdAt": "2025-10-01T10:00:00Z",
  "createdBy": "admin-user-123",
  "updatedAt": "2025-11-03T10:00:00Z",
  "updatedBy": "admin-user-456",
  "version": 5,

  // === SEARCH OPTIMIZATION ===
  "tags": ["cotton", "casual", "men", "summer", "comfortable"],
  "searchKeywords": ["tshirt", "t-shirt", "cotton shirt", "black tee"]
}
```

### Key Design Decisions

#### Denormalized Data Strategy

**Why Denormalize?**

- ✅ **Performance**: Single database query returns complete product data
- ✅ **Reduced Latency**: No need for inter-service calls during read operations
- ✅ **Better Caching**: Cache product with all display data together
- ✅ **Simplified BFF**: Web BFF doesn't need to aggregate data from multiple services

**Trade-offs**:

- ⚠️ **Eventual Consistency**: Denormalized data may be stale for 5-10 seconds
- ⚠️ **Storage Overhead**: Duplicate data across services
- ⚠️ **Sync Complexity**: Must consume events to keep data updated

**What We Denormalize**:

1. **Review Aggregates** (from Review Service) - REQ-12.1

   - Average rating, total count, rating distribution
   - Updated within 5 seconds of review events

2. **Availability Status** (from Inventory Service) - REQ-12.2

   - In stock, low stock, out of stock status
   - Updated within 10 seconds of inventory events

3. **Q&A Statistics** (from Q&A Service) - REQ-14
   - Total questions, answered questions count
   - Updated within 5 seconds of Q&A events

**What We DON'T Denormalize**:

- ❌ **Individual Reviews** - Too large, queried separately
- ❌ **Inventory Transactions** - Real-time data from Inventory Service
- ❌ **Order History** - Managed by Order Service
- ❌ **User Profiles** - Managed by User Service

#### Index Strategy

**Required Indexes**:

```javascript
// Primary Key
{ "_id": 1 }

// Unique SKU
{ "sku": 1 } // unique

// Search & Filter
{ "status": 1, "taxonomy.category": 1, "price": 1 }
{ "status": 1, "reviewAggregates.averageRating": -1 }
{ "status": 1, "createdAt": -1 }

// Text Search
{ "name": "text", "description": "text", "tags": "text", "searchKeywords": "text" }

// Parent-Child Relationships
{ "parentId": 1 }
{ "variationType": 1, "childSkus": 1 }

// Pagination (Cursor-Based)
{ "price": 1, "_id": 1 }
{ "createdAt": -1, "_id": -1 }
{ "reviewAggregates.averageRating": -1, "_id": -1 }

// SEO
{ "seo.slug": 1 } // unique

// Badge Automation
{ "badges.type": 1, "badges.expiresAt": 1 }
```

#### Document Size Considerations

**Estimated Size per Product**:

- Base product data: ~2 KB
- Images (5 URLs): ~0.5 KB
- Attributes & specs: ~1 KB
- Denormalized data: ~0.5 KB
- **Total**: ~4 KB per product

**For 1 Million Products**:

- Total storage: ~4 GB (manageable)
- With indexes: ~6-8 GB

**MongoDB 16MB Document Limit**:

- Current design uses ~4 KB (0.025% of limit)
- Safe margin for future expansion

## API Contracts

### Standard Error Response Format

All API endpoints MUST return errors in the following standardized format:

**Error Response Structure**:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "statusCode": 400,
    "correlationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "timestamp": "2025-11-03T14:32:10.123Z",
    "details": {}
  }
}
```

**Common Error Codes**:

| HTTP Status | Error Code                 | Message                           | When to Use                                                  |
| ----------- | -------------------------- | --------------------------------- | ------------------------------------------------------------ |
| 400         | `INVALID_REQUEST`          | Invalid request parameters        | Malformed request body, missing required fields              |
| 400         | `VALIDATION_ERROR`         | Validation failed                 | Business validation failures (price < 0, invalid SKU format) |
| 400         | `DUPLICATE_SKU`            | SKU already exists                | Attempting to create product with existing SKU               |
| 401         | `UNAUTHORIZED`             | Authentication required           | Missing or invalid JWT token                                 |
| 403         | `FORBIDDEN`                | Insufficient permissions          | User lacks required role (customer accessing admin endpoint) |
| 404         | `PRODUCT_NOT_FOUND`        | Product not found                 | Requested product ID doesn't exist                           |
| 404         | `PARENT_PRODUCT_NOT_FOUND` | Parent product not found          | Invalid parentId in variation creation                       |
| 409         | `CONFLICT`                 | Resource conflict                 | Concurrent update conflict, version mismatch                 |
| 422         | `INVALID_VARIATION`        | Invalid product variation         | Duplicate color-size combination in variations               |
| 422         | `INVALID_PARENT_CHILD`     | Invalid parent-child relationship | Attempting to set child as parent of another product         |
| 429         | `RATE_LIMIT_EXCEEDED`      | Too many requests                 | Rate limit exceeded (handled at BFF/Gateway level)           |
| 500         | `INTERNAL_ERROR`           | Internal server error             | Unexpected server errors                                     |
| 503         | `SERVICE_UNAVAILABLE`      | Service temporarily unavailable   | Database connection failure, circuit breaker open            |

**Error Response Examples**:

**Validation Error (400)**:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Product validation failed",
    "statusCode": 400,
    "correlationId": "abc-123-def-456",
    "timestamp": "2025-11-03T14:32:10.123Z",
    "details": {
      "fields": [
        {
          "field": "price",
          "message": "Price must be greater than 0",
          "value": -10
        },
        {
          "field": "sku",
          "message": "SKU is required",
          "value": null
        }
      ]
    }
  }
}
```

**Product Not Found (404)**:

```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product with ID 507f1f77bcf86cd799439011 not found",
    "statusCode": 404,
    "correlationId": "abc-123-def-456",
    "timestamp": "2025-11-03T14:32:10.123Z"
  }
}
```

**Duplicate SKU (400)**:

```json
{
  "error": {
    "code": "DUPLICATE_SKU",
    "message": "Product with SKU 'TS-BLK-001' already exists",
    "statusCode": 400,
    "correlationId": "abc-123-def-456",
    "timestamp": "2025-11-03T14:32:10.123Z",
    "details": {
      "sku": "TS-BLK-001",
      "existingProductId": "507f1f77bcf86cd799439011"
    }
  }
}
```

**Unauthorized (401)**:

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required. Please provide a valid JWT token",
    "statusCode": 401,
    "correlationId": "abc-123-def-456",
    "timestamp": "2025-11-03T14:32:10.123Z"
  }
}
```

**Forbidden (403)**:

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions. Admin role required",
    "statusCode": 403,
    "correlationId": "abc-123-def-456",
    "timestamp": "2025-11-03T14:32:10.123Z",
    "details": {
      "requiredRole": "admin",
      "userRole": "customer"
    }
  }
}
```

**Service Unavailable (503)**:

```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Product service is temporarily unavailable. Please try again later",
    "statusCode": 503,
    "correlationId": "abc-123-def-456",
    "timestamp": "2025-11-03T14:32:10.123Z",
    "details": {
      "reason": "database_connection_failure",
      "retryAfter": 30
    }
  }
}
```

**Error Response Requirements**:

- All errors MUST include `correlationId` for request tracing
- Error messages MUST be customer-friendly (no stack traces or internal details)
- `details` field is optional and provides additional context for debugging
- Sensitive information MUST NOT be exposed in error messages
- Stack traces MUST only be logged server-side, never returned to clients

---

### Product Creation

**Endpoint**: `POST /api/products`

**Request Body**:

```json
{
  "name": "Premium Cotton T-Shirt",
  "description": "Comfortable 100% cotton t-shirt",
  "price": 29.99,
  "sku": "TS-BLK-001",
  "brand": "ComfortWear",
  "department": "Men",
  "category": "Clothing",
  "subcategory": "Tops",
  "productType": "T-Shirts",
  "images": ["https://example.com/image1.jpg"],
  "tags": ["cotton", "casual", "summer"],
  "colors": ["Black", "White", "Navy"],
  "sizes": ["S", "M", "L", "XL"],
  "specifications": {
    "material": "100% Cotton",
    "care": "Machine washable"
  }
}
```

**Response**: 201 Created

```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Premium Cotton T-Shirt",
  "price": 29.99,
  "created_at": "2025-11-03T10:00:00Z",
  ...
}
```

**Events Published**: `product.created`

### Product Update

**Endpoint**: `PUT /api/products/{id}`

**Request Body**: (any subset of product fields)

```json
{
  "price": 24.99,
  "description": "Updated description"
}
```

**Response**: 200 OK (full product object)

**Events Published**: `product.updated`, `product.price.changed` (if price changed)

### Product Deletion

**Endpoint**: `DELETE /api/products/{id}`

**Response**: 204 No Content

**Events Published**: `product.deleted`

### Product Search (Offset-Based Pagination)

**Endpoint**: `GET /api/products/search`

**Query Parameters**:

```
q: "t-shirt" (text search)
department: "Men"
category: "Clothing"
min_price: 20
max_price: 50
page: 1 (default: 1)
limit: 20 (default: 20, max: 100)
sort: "relevance" | "price-asc" | "price-desc" | "newest" | "rating"
```

**Response**: 200 OK

```json
{
  "products": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "Premium Cotton T-Shirt",
      "price": 29.99,
      "rating": 4.5,
      "reviewCount": 128
    }
  ],
  "pagination": {
    "total": 150,
    "page": 1,
    "limit": 20,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

**Note**: For pages beyond 500, use cursor-based pagination endpoint.

### Product Search (Cursor-Based Pagination - For Deep Pagination)

**Endpoint**: `GET /api/products/search/cursor`

**Query Parameters**:

```
q: "t-shirt"
department: "Men"
category: "Clothing"
min_price: 20
max_price: 50
cursor: "eyJpZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMSIsInNjb3JlIjo0LjV9" (optional)
limit: 20 (default: 20, max: 100)
sort: "price-asc" | "price-desc" | "newest" | "rating"
```

**Response**: 200 OK

```json
{
  "products": [
    {
      "id": "507f1f77bcf86cd799439011",
      "name": "Premium Cotton T-Shirt",
      "price": 29.99
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6IjUwOGYxZjc3YmNmODZjZDc5OTQzOTAyMiIsInByaWNlIjoyNC45OX0=",
    "previous_cursor": null,
    "has_more": true,
    "limit": 20
  }
}
```

**Note**: `next_cursor` is null when no more results. Total count not provided (performance optimization).

### Get Product Variations (Paginated)

**Endpoint**: `GET /api/products/{parentId}/variations`

**Query Parameters**:

```
page: 1
limit: 50 (default: 50, max: 100)
color: "Black" (optional filter)
size: "M" (optional filter)
available: true (optional filter)
```

**Response**: 200 OK

```json
{
  "parentId": "parent-123",
  "variations": [
    {
      "id": "child-1",
      "sku": "TS-BLK-S",
      "color": "Black",
      "size": "S",
      "price": 29.99,
      "available": true
    }
  ],
  "pagination": {
    "total": 1000,
    "page": 1,
    "limit": 50,
    "total_pages": 20,
    "has_next": true,
    "has_previous": false
  }
}
```

### Bulk Product Import

**Endpoint**: `POST /api/products/bulk/import`

**Request**: Multipart form data

```
file: products.xlsx (Excel file)
mode: "validate-only" | "partial-import" | "all-or-nothing"
categoryId: "electronics" (optional, for category-specific validation)
```

**Response**: 202 Accepted (async processing)

```json
{
  "jobId": "import-job-12345",
  "status": "pending",
  "estimatedTime": "2-5 minutes",
  "checkStatusUrl": "/api/products/bulk/jobs/import-job-12345"
}
```

**Events Published**: `product.bulk.import.started`, `product.bulk.import.completed`, `product.bulk.import.failed`

### Download Import Template

**Endpoint**: `GET /api/products/bulk/template`

**Query Parameters**:

```
category: "electronics" | "clothing" | "home" (required)
format: "xlsx" (default)
```

**Response**: 200 OK (Excel file download)

### Bulk Image Upload

**Endpoint**: `POST /api/products/bulk/images`

**Request**: Multipart form data

```
file: images.zip (ZIP file containing images)
```

**Response**: 200 OK

```json
{
  "uploadedImages": [
    {
      "filename": "TS-001-1.jpg",
      "sku": "TS-001",
      "sequence": 1,
      "url": "https://cdn.example.com/products/TS-001-1.jpg",
      "size": 245678,
      "format": "jpeg"
    }
  ],
  "errors": [
    {
      "filename": "invalid.txt",
      "reason": "Unsupported file format"
    }
  ]
}
```

### Check Import Job Status

**Endpoint**: `GET /api/products/bulk/jobs/{jobId}`

**Response**: 200 OK

```json
{
  "jobId": "import-job-12345",
  "status": "completed",
  "startedAt": "2025-11-03T10:00:00Z",
  "completedAt": "2025-11-03T10:03:45Z",
  "stats": {
    "totalRows": 1500,
    "successful": 1480,
    "failed": 20,
    "inProgress": 0
  },
  "errorReportUrl": "/api/products/bulk/jobs/import-job-12345/errors"
}
```

### Download Import Error Report

**Endpoint**: `GET /api/products/bulk/jobs/{jobId}/errors`

**Response**: 200 OK (Excel file with error details)

### Create Product with Variations

**Endpoint**: `POST /api/products/variations`

**Request Body**:

```json
{
  "parent": {
    "name": "Premium Cotton T-Shirt",
    "description": "Comfortable cotton t-shirt in multiple colors and sizes",
    "brand": "ComfortWear",
    "department": "Men",
    "category": "Clothing",
    "subcategory": "Tops",
    "productType": "T-Shirts",
    "variationTheme": "Color-Size",
    "basePrice": 29.99,
    "specifications": {
      "material": "100% Cotton",
      "care": "Machine washable"
    }
  },
  "variations": [
    {
      "sku": "TS-BLK-S",
      "color": "Black",
      "size": "S",
      "price": 29.99,
      "images": ["https://cdn.example.com/TS-BLK-S-1.jpg"]
    },
    {
      "sku": "TS-BLK-M",
      "color": "Black",
      "size": "M",
      "price": 29.99,
      "images": ["https://cdn.example.com/TS-BLK-M-1.jpg"]
    }
  ]
}
```

**Response**: 201 Created

```json
{
  "parentId": "parent-123",
  "parentSku": "TS-PARENT-001",
  "variationCount": 2,
  "variations": [
    {
      "id": "child-1",
      "sku": "TS-BLK-S",
      "color": "Black",
      "size": "S"
    },
    {
      "id": "child-2",
      "sku": "TS-BLK-M",
      "color": "Black",
      "size": "M"
    }
  ]
}
```

**Events Published**: `product.variation.created` (for parent), `product.created` (for each child)

### Get Product Variations

**Endpoint**: `GET /api/products/{parentId}/variations`

**Query Parameters** (optional filters):

```
color: "Black"
size: "M"
available: true
```

**Response**: 200 OK

```json
{
  "parentId": "parent-123",
  "variationTheme": "Color-Size",
  "variations": [
    {
      "id": "child-1",
      "sku": "TS-BLK-S",
      "color": "Black",
      "size": "S",
      "price": 29.99,
      "available": true,
      "images": ["https://cdn.example.com/TS-BLK-S-1.jpg"]
    }
  ]
}
```

### Add Variation to Parent Product

**Endpoint**: `POST /api/products/{parentId}/variations`

**Request Body**:

```json
{
  "sku": "TS-RED-L",
  "color": "Red",
  "size": "L",
  "price": 32.99,
  "images": ["https://cdn.example.com/TS-RED-L-1.jpg"]
}
```

**Response**: 201 Created

**Events Published**: `product.created`, `product.variation.added`

### Assign Badge to Product

**Endpoint**: `POST /api/products/{id}/badges`

**Request Body**:

```json
{
  "badgeType": "best-seller",
  "displayText": "Best Seller",
  "priority": 1,
  "startDate": "2025-11-03T00:00:00Z",
  "endDate": "2025-12-31T23:59:59Z",
  "visible": true
}
```

**Response**: 201 Created

```json
{
  "badgeId": "badge-123",
  "productId": "507f1f77bcf86cd799439011",
  "badgeType": "best-seller",
  "expiresAt": "2025-12-31T23:59:59Z"
}
```

**Events Published**: `product.badge.assigned`

### Remove Badge from Product

**Endpoint**: `DELETE /api/products/{id}/badges/{badgeId}`

**Response**: 204 No Content

**Events Published**: `product.badge.removed`

### Bulk Assign Badge

**Endpoint**: `POST /api/products/badges/bulk`

**Request Body**:

```json
{
  "productIds": ["id-1", "id-2", "id-3"],
  "badge": {
    "badgeType": "limited-time-deal",
    "displayText": "Flash Sale",
    "priority": 1,
    "endDate": "2025-11-10T23:59:59Z"
  }
}
```

**Response**: 200 OK

```json
{
  "assigned": 3,
  "failed": 0
}
```

### Update Product SEO

**Endpoint**: `PUT /api/products/{id}/seo`

**Request Body**:

```json
{
  "metaTitle": "Premium Cotton T-Shirt - Comfortable & Stylish | AIOutlet",
  "metaDescription": "Shop our premium 100% cotton t-shirt. Soft, breathable fabric in multiple colors. Free shipping on orders over $50.",
  "metaKeywords": "cotton t-shirt, men's t-shirt, comfortable clothing",
  "urlSlug": "premium-cotton-t-shirt-black",
  "canonicalUrl": "https://aioutlet.com/products/premium-cotton-t-shirt-black",
  "openGraph": {
    "title": "Premium Cotton T-Shirt",
    "description": "Soft 100% cotton t-shirt",
    "imageUrl": "https://cdn.example.com/TS-001-og.jpg"
  },
  "structuredData": {
    "@type": "Product",
    "name": "Premium Cotton T-Shirt",
    "offers": {
      "@type": "Offer",
      "price": "29.99",
      "priceCurrency": "USD"
    }
  }
}
```

**Response**: 200 OK

**Events Published**: `product.seo.updated`

### Get Category Attribute Schema

**Endpoint**: `GET /api/categories/{categoryId}/attributes`

**Response**: 200 OK

```json
{
  "categoryId": "clothing",
  "categoryName": "Clothing",
  "requiredAttributes": [
    {
      "name": "material",
      "type": "string",
      "description": "Primary material composition"
    },
    {
      "name": "size",
      "type": "list",
      "allowedValues": ["XS", "S", "M", "L", "XL", "XXL"]
    }
  ],
  "optionalAttributes": [
    {
      "name": "fitType",
      "type": "string",
      "allowedValues": ["Regular", "Slim", "Relaxed", "Oversized"]
    },
    {
      "name": "sleeveLength",
      "type": "string",
      "allowedValues": ["Short", "Long", "3/4", "Sleeveless"]
    }
  ]
}
```

### Search Products with Attribute Filters

**Endpoint**: `GET /api/products/search`

**Query Parameters**:

```
q: "t-shirt" (text search)
category: "clothing"
attributes.color: "Black,Navy" (multi-select)
attributes.size: "M,L"
attributes.material: "Cotton"
minPrice: 20
maxPrice: 50
badges: "best-seller,new-arrival"
sort: "price-asc" | "price-desc" | "relevance" | "newest"
page: 1
limit: 20
```

**Response**: 200 OK

```json
{
  "products": [
    /* array of products */
  ],
  "facets": {
    "colors": [
      { "value": "Black", "count": 45 },
      { "value": "Navy", "count": 32 }
    ],
    "sizes": [
      { "value": "S", "count": 38 },
      { "value": "M", "count": 42 }
    ],
    "materials": [
      { "value": "Cotton", "count": 67 },
      { "value": "Polyester", "count": 23 }
    ]
  },
  "appliedFilters": {
    "attributes.color": ["Black", "Navy"],
    "attributes.size": ["M", "L"]
  },
  "total": 150,
  "page": 1,
  "limit": 20
}
```

## Event Schemas (Framework-Agnostic)

All events MUST follow this structure:

```json
{
  "eventType": "product.created|updated|deleted|price.changed",
  "eventId": "uuid-v4",
  "timestamp": "ISO-8601 datetime",
  "source": "product-service",
  "correlationId": "request-correlation-id",
  "data": {
    // Event-specific payload
  }
}
```

### product.created Event

```json
{
  "eventType": "product.created",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "name": "Premium Cotton T-Shirt",
    "price": 29.99,
    "sku": "TS-BLK-001",
    "category": "Clothing",
    "createdAt": "2025-11-03T10:00:00Z",
    "createdBy": "admin-user-123"
  }
}
```

### product.updated Event

```json
{
  "eventType": "product.updated",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "updatedFields": ["price", "description"],
    "updatedAt": "2025-11-03T11:00:00Z",
    "updatedBy": "admin-user-123"
  }
}
```

### product.deleted Event

```json
{
  "eventType": "product.deleted",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "hardDelete": false,
    "deletedAt": "2025-11-03T12:00:00Z",
    "deletedBy": "admin-user-123"
  }
}
```

### product.price.changed Event

```json
{
  "eventType": "product.price.changed",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "oldPrice": 29.99,
    "newPrice": 24.99,
    "changedAt": "2025-11-03T11:00:00Z"
  }
}
```

### product.variation.created Event

```json
{
  "eventType": "product.variation.created",
  "data": {
    "parentId": "parent-123",
    "parentSku": "TS-PARENT-001",
    "variationTheme": "Color-Size",
    "variationCount": 6,
    "createdAt": "2025-11-03T10:00:00Z",
    "createdBy": "admin-user-123"
  }
}
```

### product.variation.added Event

```json
{
  "eventType": "product.variation.added",
  "data": {
    "parentId": "parent-123",
    "childId": "child-7",
    "childSku": "TS-RED-XL",
    "variationAttributes": {
      "color": "Red",
      "size": "XL"
    },
    "addedAt": "2025-11-03T10:00:00Z"
  }
}
```

### product.bulk.import.started Event

```json
{
  "eventType": "product.bulk.import.started",
  "data": {
    "jobId": "import-job-12345",
    "filename": "products-november-2025.xlsx",
    "totalRows": 1500,
    "mode": "partial-import",
    "startedAt": "2025-11-03T10:00:00Z",
    "initiatedBy": "admin-user-123"
  }
}
```

### product.bulk.import.completed Event

```json
{
  "eventType": "product.bulk.import.completed",
  "data": {
    "jobId": "import-job-12345",
    "filename": "products-november-2025.xlsx",
    "stats": {
      "totalRows": 1500,
      "successful": 1480,
      "failed": 20
    },
    "completedAt": "2025-11-03T10:03:45Z",
    "durationSeconds": 225,
    "errorReportUrl": "/api/products/bulk/jobs/import-job-12345/errors"
  }
}
```

### product.bulk.import.failed Event

```json
{
  "eventType": "product.bulk.import.failed",
  "data": {
    "jobId": "import-job-12345",
    "filename": "products-november-2025.xlsx",
    "failureReason": "Database connection lost during processing",
    "processedRows": 450,
    "totalRows": 1500,
    "failedAt": "2025-11-03T10:02:15Z"
  }
}
```

### product.badge.assigned Event

```json
{
  "eventType": "product.badge.assigned",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "badgeId": "badge-123",
    "badgeType": "best-seller",
    "expiresAt": "2025-12-31T23:59:59Z",
    "assignedAt": "2025-11-03T10:00:00Z",
    "assignedBy": "admin-user-123"
  }
}
```

### product.badge.removed Event

```json
{
  "eventType": "product.badge.removed",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "badgeId": "badge-123",
    "badgeType": "best-seller",
    "removedAt": "2025-11-03T10:00:00Z",
    "removedBy": "admin-user-123"
  }
}
```

### product.seo.updated Event

```json
{
  "eventType": "product.seo.updated",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "urlSlug": "premium-cotton-t-shirt-black",
    "previousSlug": "cotton-tshirt-black",
    "updatedAt": "2025-11-03T10:00:00Z",
    "updatedBy": "admin-user-123"
  }
}
```

### product.back.in.stock Event

```json
{
  "eventType": "product.back.in.stock",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "name": "Premium Cotton T-Shirt",
    "availableQuantity": 50,
    "restockedAt": "2025-11-03T10:00:00Z"
  }
}
```

### product.badge.auto.assigned Event

```json
{
  "eventType": "product.badge.auto.assigned",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "badgeType": "best-seller",
    "reason": "Top 100 in category by sales (last 30 days)",
    "metrics": {
      "salesLast30Days": 1250,
      "categoryRank": 15
    },
    "assignedAt": "2025-11-03T10:00:00Z"
  }
}
```

### product.badge.auto.removed Event

```json
{
  "eventType": "product.badge.auto.removed",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "badgeType": "trending",
    "reason": "View growth dropped below 30%",
    "metrics": {
      "viewGrowthPercent": 25
    },
    "removedAt": "2025-11-03T10:00:00Z"
  }
}
```

### product.bulk.import.progress Event

```json
{
  "eventType": "product.bulk.import.progress",
  "data": {
    "jobId": "import-job-12345",
    "processedRows": 500,
    "totalRows": 1500,
    "successfulRows": 485,
    "failedRows": 15,
    "percentComplete": 33,
    "estimatedTimeRemaining": "2 minutes"
  }
}
```

### product.bulk.import.cancelled Event

```json
{
  "eventType": "product.bulk.import.cancelled",
  "data": {
    "jobId": "import-job-12345",
    "processedRows": 750,
    "totalRows": 1500,
    "successfulRows": 720,
    "failedRows": 30,
    "cancelledAt": "2025-11-03T10:05:00Z",
    "cancelledBy": "admin-user-123"
  }
}
```

## Consumed Events (From Other Services)

Product Service consumes the following events to maintain denormalized data:

### review.created Event (from Review Service)

```json
{
  "eventType": "review.created",
  "data": {
    "reviewId": "review-123",
    "productId": "507f1f77bcf86cd799439011",
    "rating": 5,
    "verifiedPurchase": true,
    "createdAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Increment review count, recalculate average rating and rating distribution.

### review.updated Event (from Review Service)

```json
{
  "eventType": "review.updated",
  "data": {
    "reviewId": "review-123",
    "productId": "507f1f77bcf86cd799439011",
    "oldRating": 4,
    "newRating": 5,
    "updatedAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Recalculate average rating and rating distribution.

### review.deleted Event (from Review Service)

```json
{
  "eventType": "review.deleted",
  "data": {
    "reviewId": "review-123",
    "productId": "507f1f77bcf86cd799439011",
    "rating": 5,
    "deletedAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Decrement review count, recalculate average rating and rating distribution.

### inventory.stock.updated Event (from Inventory Service)

```json
{
  "eventType": "inventory.stock.updated",
  "data": {
    "sku": "TS-BLK-001",
    "productId": "507f1f77bcf86cd799439011",
    "availableQuantity": 50,
    "lowStockThreshold": 10,
    "updatedAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Update availability status (In Stock, Low Stock, Out of Stock). If transitioning from Out of Stock to In Stock, publish `product.back.in.stock` event.

### inventory.reserved Event (from Inventory Service)

```json
{
  "eventType": "inventory.reserved",
  "data": {
    "sku": "TS-BLK-001",
    "productId": "507f1f77bcf86cd799439011",
    "reservedQuantity": 2,
    "availableQuantity": 48,
    "reservationId": "reservation-456"
  }
}
```

**Action**: Update availability status if threshold crossed.

### inventory.released Event (from Inventory Service)

```json
{
  "eventType": "inventory.released",
  "data": {
    "sku": "TS-BLK-001",
    "productId": "507f1f77bcf86cd799439011",
    "releasedQuantity": 2,
    "availableQuantity": 50,
    "reservationId": "reservation-456"
  }
}
```

**Action**: Update availability status if threshold crossed.

### analytics.product.sales.updated Event (from Analytics Service)

```json
{
  "eventType": "analytics.product.sales.updated",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "category": "Clothing",
    "salesLast30Days": 1250,
    "categoryRank": 15,
    "calculatedAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Evaluate "Best Seller" badge criteria, auto-assign or auto-remove badge.

### analytics.product.views.updated Event (from Analytics Service)

```json
{
  "eventType": "analytics.product.views.updated",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "viewsLast7Days": 5400,
    "viewsPrior7Days": 3600,
    "viewGrowthPercent": 50,
    "calculatedAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Evaluate "Trending" badge criteria, auto-assign or auto-remove badge.

### analytics.product.conversions.updated Event (from Analytics Service)

```json
{
  "eventType": "analytics.product.conversions.updated",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "category": "Clothing",
    "conversionRate": 0.045,
    "categoryAverageConversionRate": 0.032,
    "calculatedAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Evaluate "Hot Deal" badge criteria, auto-assign or auto-remove badge.

### product.question.created Event (from Q&A Service)

```json
{
  "eventType": "product.question.created",
  "data": {
    "questionId": "question-789",
    "productId": "507f1f77bcf86cd799439011",
    "createdAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Increment question count, increment unanswered question count.

### product.answer.created Event (from Q&A Service)

```json
{
  "eventType": "product.answer.created",
  "data": {
    "answerId": "answer-101",
    "questionId": "question-789",
    "productId": "507f1f77bcf86cd799439011",
    "createdAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Increment answered question count, decrement unanswered question count.

### product.question.deleted Event (from Q&A Service)

```json
{
  "eventType": "product.question.deleted",
  "data": {
    "questionId": "question-789",
    "productId": "507f1f77bcf86cd799439011",
    "hadAnswers": true,
    "deletedAt": "2025-11-03T10:00:00Z"
  }
}
```

**Action**: Decrement question count, decrement answered/unanswered count appropriately.

## Event Delivery Guarantees

- **Delivery**: At-least-once (consumers must handle duplicates)
- **Ordering**: Not guaranteed across different events
- **Durability**: Events MUST be persisted by messaging infrastructure until acknowledged

## External Dependencies

**Data Storage:**

- **MongoDB**: Product catalog storage (primary database)

**Authentication & Authorization:**

- **JWT Auth Service**: For token validation and user context

**Event Infrastructure:**

- **Message Broker**: For publishing and consuming domain events (implementation abstracted via Dapr)

**Event Producers (Services Product Service Consumes From):**

- **Review Service**: Provides review.created, review.updated, review.deleted events for review aggregation
- **Inventory Service**: Provides inventory.stock.updated, inventory.reserved, inventory.released events for availability sync
- **Analytics Service**: Provides analytics.product.sales.updated, analytics.product.views.updated, analytics.product.conversions.updated for badge automation
- **Q&A Service**: Provides product.question.created, product.answer.created, product.question.deleted for Q&A count tracking

**Event Consumers (Services That Consume Product Service Events):**

- **Audit Service**: Consumes all product events for audit logging
- **Notification Service**: Consumes product events for customer notifications (back in stock, price drops, etc.)
- **Order Service**: Validates product existence before order creation
- **Search Service** (future): Will index product changes for search optimization

**Note**: All event integration is implemented via Dapr pub/sub for framework-agnostic, broker-independent messaging.

## Success Criteria

1. ✅ All API endpoints respond within defined SLA (NFR-1.1)
2. ✅ Events reach consuming services (Audit Service, Notification Service, Order Service)
3. ✅ Zero data loss during operations
4. ✅ 100% test coverage for business logic
5. ✅ 99.9% uptime maintained
6. ✅ Can handle 1,000 req/s sustained load
7. ✅ Bulk import can process 10,000 products within 5 minutes
8. ✅ Product variations support up to 1,000 children per parent
9. ✅ Attribute-based search returns results within 300ms (p95)
10. ✅ Badge assignment is reflected in search results within 1 second
11. ✅ SEO metadata is properly indexed by search engines
12. ✅ Review aggregates update within 5 seconds of review events (REQ-12.1)
13. ✅ Inventory availability updates within 10 seconds of inventory events (REQ-12.2)
14. ✅ Automatic badge assignment/removal works correctly based on analytics (REQ-12.3)
15. ✅ Bulk import worker handles failures gracefully without data loss (REQ-12.4)
16. ✅ Consumed events are processed idempotently (duplicate events don't corrupt data)

## Out of Scope

- **Product recommendations**: Handled by separate Recommendation Service
- **Inventory management**: Handled by Inventory Service (stock levels, reservations) - Product Service only stores denormalized availability status
- **Product reviews content**: Handled by Review Service - Product Service only stores aggregate review metrics
- **Product pricing rules**: Dynamic pricing handled by separate Pricing Service
- **Product images/videos storage**: Media storage/CDN handled by separate Media Service (Product Service stores URLs only)
- **Multi-language product content**: Full translations of product names/descriptions (only SEO metadata translations in scope per REQ-11.5)
- **Product comparison feature**: Handled by separate service or UI layer
- **A/B testing for product listings**: Handled by separate experimentation platform
- **Product bundling**: Creating product bundles (future enhancement)
- **Product Q&A content management**: Handled by Q&A Service - Product Service only stores Q&A counts
- **Real-time analytics computation**: Handled by Analytics Service - Product Service consumes pre-computed metrics
- **Payment-related features**: Gift cards, payment methods (handled by Payment Service)
- **Customer-specific features**: Wishlists, recently viewed (handled by User Service or dedicated services)

## Acceptance Criteria for Implementation

### For Developers

1. All REQ-\* requirements (REQ-1 through REQ-16) must be implemented and tested
2. All NFR-\* requirements must be met and validated
3. API contracts must match specifications exactly
4. Event schemas (published and consumed) must match specifications exactly
5. All admin operations must validate user permissions
6. All operations must include proper logging and tracing
7. Bulk import must be implemented as async worker with proper error handling (REQ-12.4)
8. Variation relationships must maintain referential integrity
9. Badge expiration and auto-assignment must be handled automatically (REQ-12.3)
10. SEO URL slugs must be unique and validated
11. Event consumption must follow eventual consistency pattern (REQ-12.x)
12. Denormalized data (reviews, inventory, analytics) must be kept in sync via events

### For QA

1. Load test at 1,000 req/s with < 200ms p95 latency for reads
2. Load test at 500 req/s with < 500ms p95 latency for writes
3. Verify all events are published and received by consumers
4. Verify soft-delete products don't appear in customer searches
5. Verify SKU uniqueness is enforced in all scenarios (including variations)
6. Verify error handling for database failures
7. Test bulk import with 10,000 products (success and failure scenarios)
8. Verify variation inheritance works correctly (parent attributes flow to children)
9. Verify expired badges are automatically hidden from customer view
10. Verify attribute-based filtering returns accurate results
11. Test concurrent badge assignments to same product
12. Verify SEO slug uniqueness constraint

### For Product Owners

1. Catalog can be managed efficiently through Admin UI
2. Product search is fast and accurate for customers
3. Product changes are reflected immediately
4. Audit trail captures all product changes
5. System remains responsive during high traffic
6. Bulk import reduces manual data entry time by 90%
7. Product variations provide Amazon-like shopping experience
8. Enhanced attributes enable precise product filtering
9. Badges drive customer engagement (visible, timely, relevant)
10. SEO improvements lead to increased organic traffic (measurable via analytics)

---

**NOTE**: This PRD describes **WHAT** the Product Service must do from a business perspective. Technical implementation decisions (database technology, messaging framework, programming language, etc.) are documented separately in technical design documents and Copilot instructions.
