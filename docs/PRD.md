# Product Requirements Document (PRD)

## Product Service - AIOutlet Platform

**Version:** 1.0  
**Last Updated:** November 3, 2025  
**Status:** Active Development  
**Owner:** AIOutlet Platform Team

---

## Table of Contents

1. [Product Overview](#1-product-overview)
   - 1.1 [Product Vision](#11-product-vision)
   - 1.2 [Business Objectives](#12-business-objectives)
   - 1.3 [Success Metrics](#13-success-metrics)
   - 1.4 [Product Description](#14-product-description)
   - 1.5 [Target Users](#15-target-users)
   - 1.6 [Key Features](#16-key-features)
2. [Technical Architecture](#2-technical-architecture)
   - 2.1 [Technology Stack](#21-technology-stack)
   - 2.2 [Architecture Pattern](#22-architecture-pattern)
   - 2.3 [Event-Driven Integration](#23-event-driven-integration)
     - 2.3.1 [Integration Pattern](#231-integration-pattern)
     - 2.3.2 [Outbound Events (Published)](#232-outbound-events-published)
     - 2.3.3 [Inbound Events (Consumed)](#233-inbound-events-consumed)
   - 2.4 [Data Model](#24-data-model)
   - 2.5 [Database Indexes](#25-database-indexes)
   - 2.6 [Inter-Service Communication](#26-inter-service-communication)
   - 2.7 [Environment Variables](#27-environment-variables)
     - 2.7.1 [Database Configuration](#271-database-configuration)
     - 2.7.2 [Message Broker Configuration](#272-message-broker-configuration)
     - 2.7.3 [Dapr Configuration](#273-dapr-configuration)
     - 2.7.4 [Authentication & Authorization](#274-authentication--authorization)
     - 2.7.5 [Service Configuration](#275-service-configuration)
     - 2.7.6 [Performance & Caching](#276-performance--caching)
     - 2.7.7 [File Upload Configuration](#277-file-upload-configuration)
     - 2.7.8 [Monitoring & Observability](#278-monitoring--observability)
     - 2.7.9 [Health Check Configuration](#279-health-check-configuration)
     - 2.7.10 [Event Publishing Configuration](#2710-event-publishing-configuration)
     - 2.7.11 [Example Configuration Files](#2711-example-configuration-files)
3. [API Specifications](#3-api-specifications)
   - 3.1 [Authentication](#31-authentication)
   - 3.2 [Product Management APIs](#32-product-management-apis)
     - 3.2.1 [Create Product](#321-create-product)
     - 3.2.2 [Get Product by ID](#322-get-product-by-id)
     - 3.2.3 [Update Product](#323-update-product)
     - 3.2.4 [Delete Product](#324-delete-product)
     - 3.2.5 [Check Product Existence](#325-check-product-existence)
     - 3.2.6 [Batch Product Lookup](#326-batch-product-lookup)
     - 3.2.7 [Bulk Product Import](#327-bulk-product-import)
     - 3.2.8 [Get Bulk Import Status](#328-get-bulk-import-status)
     - 3.2.9 [Create Product Variations](#329-create-product-variations)
     - 3.2.10 [Assign Badge to Product](#3210-assign-badge-to-product)
     - 3.2.11 [Remove Badge from Product](#3211-remove-badge-from-product)
     - 3.2.12 [Bulk Badge Assignment](#3212-bulk-badge-assignment)
     - 3.2.13 [Update SEO Metadata](#3213-update-seo-metadata)
     - 3.2.14 [Download Import Template](#3214-download-import-template)
     - 3.2.15 [Get Bulk Import Errors](#3215-get-bulk-import-errors)
     - 3.2.16 [Bulk Image Upload](#3216-bulk-image-upload)
     - 3.2.17 [Get Product Variations](#3217-get-product-variations)
     - 3.2.18 [Add Variation to Parent](#3218-add-variation-to-parent)
   - 3.3 [Product Discovery APIs](#33-product-discovery-apis)
     - 3.3.1 [Search Products (Offset Pagination)](#331-search-products-offset-pagination)
     - 3.3.2 [Search Products (Cursor Pagination)](#332-search-products-cursor-pagination)
     - 3.3.3 [Get Products by Category](#333-get-products-by-category)
     - 3.3.4 [Autocomplete Product Search](#334-autocomplete-product-search)
     - 3.3.5 [Get Trending Products](#335-get-trending-products)
   - 3.4 [Admin APIs](#34-admin-apis)
   - 3.5 [Health Check APIs](#35-health-check-apis)
     - 3.5.1 [Liveness Probe](#351-liveness-probe)
     - 3.5.2 [Readiness Probe](#352-readiness-probe)
   - 3.6 [Error Code Catalog](#36-error-code-catalog)
     - 3.6.1 [Client Error Codes (4xx)](#361-client-error-codes-4xx)
     - 3.6.2 [Server Error Codes (5xx)](#362-server-error-codes-5xx)
     - 3.6.3 [Business Logic Error Codes](#363-business-logic-error-codes)
     - 3.6.4 [Error Response Format](#364-error-response-format)
4. [Functional Requirements](#4-functional-requirements)
   - 4.1 [Product Management (CRUD Operations)](#41-product-management-crud-operations)
     - 4.1.1 [Create Products](#411-create-products)
     - 4.1.2 [Update Products](#412-update-products)
     - 4.1.3 [Soft Delete Products](#413-soft-delete-products)
     - 4.1.4 [Prevent Duplicate SKUs](#414-prevent-duplicate-skus)
   - 4.2 [Product Discovery & Search](#42-product-discovery--search)
     - 4.2.1 [Text Search](#421-text-search)
     - 4.2.2 [Hierarchical Filtering](#422-hierarchical-filtering)
     - 4.2.3 [Price Range Filtering](#423-price-range-filtering)
     - 4.2.4 [Tag-Based Filtering](#424-tag-based-filtering)
     - 4.2.5 [Pagination & Large Dataset Handling](#425-pagination--large-dataset-handling)
     - 4.2.6 [Trending Products](#426-trending-products)
     - 4.2.7 [Top Categories](#427-top-categories)
   - 4.3 [Data Consistency & Validation](#43-data-consistency--validation)
     - 4.3.1 [Price Validation](#431-price-validation)
     - 4.3.2 [Required Field Validation](#432-required-field-validation)
     - 4.3.3 [SKU Format Validation](#433-sku-format-validation)
     - 4.3.4 [Data Persistence](#434-data-persistence)
   - 4.4 [Administrative Features](#44-administrative-features)
     - 4.4.1 [Product Statistics & Reporting](#441-product-statistics--reporting)
     - 4.4.2 [Bulk Product Operations](#442-bulk-product-operations)
       - 4.4.2.1 [Template Download](#4421-template-download)
       - 4.4.2.2 [Bulk Product Import](#4422-bulk-product-import)
       - 4.4.2.3 [Image Handling for Bulk Import](#4423-image-handling-for-bulk-import)
       - 4.4.2.4 [Import Status Tracking](#4424-import-status-tracking)
       - 4.4.2.5 [Bulk Update Operations](#4425-bulk-update-operations)
     - 4.4.3 [Badge Management](#443-badge-management)
       - 4.4.3.1 [Manual Badge Assignment](#4431-manual-badge-assignment)
       - 4.4.3.2 [Badge Types & Properties](#4432-badge-types--properties)
       - 4.4.3.3 [Badge Monitoring](#4433-badge-monitoring)
     - 4.4.4 [Size Chart Management](#444-size-chart-management)
       - 4.4.4.1 [Size Chart Creation & Assignment](#4441-size-chart-creation--assignment)
       - 4.4.4.2 [Size Chart Templates](#4442-size-chart-templates)
     - 4.4.5 [Product Restrictions & Compliance](#445-product-restrictions--compliance)
       - 4.4.5.1 [Age Restrictions](#4451-age-restrictions)
       - 4.4.5.2 [Shipping Restrictions](#4452-shipping-restrictions)
       - 4.4.5.3 [Regional Availability](#4453-regional-availability)
       - 4.4.5.4 [Compliance Metadata](#4454-compliance-metadata)
     - 4.4.6 [Admin Permissions & Audit](#446-admin-permissions--audit)
   - 4.5 [Product Variations](#45-product-variations)
     - 4.5.1 [Variation Structure](#451-variation-structure)
     - 4.5.2 [Variation Attributes](#452-variation-attributes)
     - 4.5.3 [Variation Inheritance](#453-variation-inheritance)
     - 4.5.4 [Variation Display and Selection](#454-variation-display-and-selection)
     - 4.5.5 [Variation Management](#455-variation-management)
   - 4.6 [Enhanced Product Attributes](#46-enhanced-product-attributes)
     - 4.6.1 [Structured Attribute Schema](#461-structured-attribute-schema)
     - 4.6.2 [Common Attribute Categories](#462-common-attribute-categories)
     - 4.6.3 [Category-Specific Attributes](#463-category-specific-attributes)
     - 4.6.4 [Attribute-Based Search and Filtering](#464-attribute-based-search-and-filtering)
     - 4.6.5 [Attribute Validation](#465-attribute-validation)
5. [Non-Functional Requirements](#5-non-functional-requirements)
   - 5.1 [Performance](#51-performance)
     - 5.1.1 [API Response Times](#511-api-response-times)
     - 5.1.2 [Throughput](#512-throughput)
     - 5.1.3 [Database Performance](#513-database-performance)
   - 5.2 [Scalability](#52-scalability)
     - 5.2.1 [Service Uptime](#521-service-uptime)
     - 5.2.2 [Event Publishing Resilience](#522-event-publishing-resilience)
     - 5.2.3 [Database Resilience](#523-database-resilience)
   - 5.3 [Availability](#53-availability)
     - 5.3.1 [Horizontal Scaling](#531-horizontal-scaling)
     - 5.3.2 [Data Growth](#532-data-growth)
   - 5.4 [Security](#54-security)
     - 5.4.1 [Authentication](#541-authentication)
     - 5.4.2 [Authorization](#542-authorization)
     - 5.4.3 [Input Validation](#543-input-validation)
     - 5.4.4 [Role-Based Access Control (RBAC)](#544-role-based-access-control-rbac)
       - 5.4.4.1 [Roles](#5441-roles)
       - 5.4.4.2 [Permission Matrix](#5442-permission-matrix)
       - 5.4.4.3 [Implementation Requirements](#5443-implementation-requirements)
     - 5.4.5 [Secrets Management](#545-secrets-management)
       - 5.4.5.1 [Sensitive Data](#5451-sensitive-data)
       - 5.4.5.2 [Requirements](#5452-requirements)
       - 5.4.5.3 [Recommended Implementation](#5453-recommended-implementation)
   - 5.5 [Data Privacy](#55-data-privacy)
     - 5.5.1 [Data Classification](#551-data-classification)
     - 5.5.2 [Data Retention](#552-data-retention)
   - 5.6 [Observability](#56-observability)
     - 5.6.1 [Distributed Tracing](#561-distributed-tracing)
     - 5.6.2 [Logging](#562-logging)
       - 5.6.2.1 [General Logging Requirements](#5621-general-logging-requirements)
       - 5.6.2.2 [Correlation ID Requirements](#5622-correlation-id-requirements)
       - 5.6.2.3 [Structured Logging Format](#5623-structured-logging-format)
       - 5.6.2.4 [Logging Levels](#5624-logging-levels)
       - 5.6.2.5 [Sensitive Data Handling](#5625-sensitive-data-handling)
       - 5.6.2.6 [Environment-Specific Logging Behavior](#5626-environment-specific-logging-behavior)
     - 5.6.3 [Metrics](#563-metrics)
       - 5.6.3.1 [General Metrics Requirements](#5631-general-metrics-requirements)
       - 5.6.3.2 [Request Metrics](#5632-request-metrics)
       - 5.6.3.3 [Database Metrics](#5633-database-metrics)
       - 5.6.3.4 [Event Metrics](#5634-event-metrics)
       - 5.6.3.5 [Business Metrics](#5635-business-metrics)
       - 5.6.3.6 [Alerting Thresholds](#5636-alerting-thresholds)
     - 5.6.4 [Health Checks](#564-health-checks)
   - 5.7 [Error Handling](#57-error-handling)
     - 5.7.1 [Error Response Format](#571-error-response-format)
       - 5.7.1.1 [General Requirements](#5711-general-requirements)
       - 5.7.1.2 [Structured Error Response Example](#5712-structured-error-response-example)
       - 5.7.1.3 [Error Response Structure](#5713-error-response-structure)
     - 5.7.2 [Error Logging](#572-error-logging)
     - 5.7.3 [Resilience](#573-resilience)
6. [Dependencies](#6-dependencies)
   - 6.1 [External Services](#61-external-services)
   - 6.2 [Infrastructure](#62-infrastructure)
   - 6.3 [Development Dependencies](#63-development-dependencies)
7. [Testing Strategy](#7-testing-strategy)
   - 7.1 [Unit Testing](#71-unit-testing)
   - 7.2 [Integration Testing](#72-integration-testing)
   - 7.3 [E2E Testing](#73-e2e-testing)
   - 7.4 [Performance Testing](#74-performance-testing)
   - 7.5 [Security Testing](#75-security-testing)
8. [Deployment](#8-deployment)
   - 8.1 [Environment Configuration](#81-environment-configuration)
   - 8.2 [Docker Configuration](#82-docker-configuration)
   - 8.3 [Kubernetes Deployment](#83-kubernetes-deployment)
   - 8.4 [CI/CD Pipeline](#84-cicd-pipeline)
9. [Monitoring & Alerts](#9-monitoring--alerts)
   - 9.1 [Metrics](#91-metrics)
   - 9.2 [Alerts](#92-alerts)
   - 9.3 [Dashboards](#93-dashboards)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [Compliance & Legal](#11-compliance--legal)
    - 11.1 [Data Protection Regulations](#111-data-protection-regulations)
12. [Documentation References](#12-documentation-references)
    - 12.1 [Developer Documentation](#121-developer-documentation)
    - 12.2 [Runbooks](#122-runbooks)
    - 12.3 [API Documentation](#123-api-documentation)
13. [Approval & Sign-off](#13-approval--sign-off)
14. [Revision History](#14-revision-history)
15. [Appendix](#15-appendix)
    - 15.1 [Glossary](#151-glossary)
    - 15.2 [References](#152-references)

---

## 1. Product Overview

### 1.1 Product Vision

The Product Service is a core microservice within the AIOutlet e-commerce platform, responsible for managing the complete product catalog, including product information, taxonomy, search, and product discovery features. It serves as the central source of truth for all product data and provides both REST APIs and event-driven integration patterns.

### 1.2 Business Objectives

- **Centralized Product Catalog**: Single source of truth for all product data across the platform
- **Scalability**: Support millions of products with sub-100ms response times
- **Rich Product Discovery**: Enable customers to find products through search, filters, and recommendations
- **Data Consistency**: Maintain eventually consistent denormalized data from review, inventory, and analytics services
- **Admin Capabilities**: Provide comprehensive tools for catalog management and bulk operations

### 1.3 Success Metrics

| Metric                        | Target  | Current |
| ----------------------------- | ------- | ------- |
| API Response Time (p95)       | < 100ms | TBD     |
| Search Response Time (p95)    | < 200ms | TBD     |
| Service Uptime                | 99.9%   | TBD     |
| Product Creation Success Rate | > 99%   | TBD     |
| API Error Rate                | < 0.5%  | TBD     |
| Event Processing Success Rate | > 99.5% | TBD     |

### 1.4 Product Description

The Product Service is a Python/FastAPI microservice that manages the product catalog, including CRUD operations, search, taxonomy management, and event-driven data synchronization. It follows the **Publisher & Consumer** pattern, publishing product events via Dapr Pub/Sub while consuming events from review, inventory, and analytics services to maintain denormalized data for optimal read performance.

### 1.5 Target Users

1. **Customers**: End-users browsing and searching for products
2. **Admin Users**: Platform administrators managing product catalog and operations
3. **Internal Services**: Other microservices (order, inventory, review, cart) consuming product data

### 1.6 Key Features

- ✅ Product catalog management (CRUD operations)
- ✅ Hierarchical product taxonomy (Department → Category → Subcategory → Product Type)
- ✅ Product search with filters (price, brand, category, ratings)
- ✅ Product variations (parent-child relationships for sizes/colors)
- ✅ Event-driven architecture (publisher & consumer)
- ✅ Denormalized data for performance (review aggregates, inventory status, sales metrics)
- ✅ Admin features (bulk operations, badge management, statistics)
- ✅ Comprehensive health checks and observability

---

## 2. Technical Architecture

### 2.1 Technology Stack

- **Runtime**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **Database**: MongoDB (PyMongo)
- **Authentication**: JWT (validated by auth-service)
- **Message Broker**: Dapr Pub/Sub with RabbitMQ backend
- **Observability**: Structured logging, OpenTelemetry (tracing)
- **Testing**: Pytest, HTTPx
- **Validation**: Pydantic

### 2.2 Architecture Pattern

**Publisher & Consumer (Event-Driven)**

```
┌─────────────────┐
│ Product Service │
│   (FastAPI)     │
└────────┬────────┘
         │
         ├─► Publish: product.* events (Dapr Pub/Sub)
         │
         └─► Consume: review.*, inventory.*, analytics.* events
```

### 2.3 Event-Driven Integration

Product Service follows a **Publisher & Consumer** pattern, both publishing events for downstream services and consuming events from upstream services to maintain denormalized data.

#### 2.3.1 Integration Pattern

**Event Infrastructure**:

- Transport: Dapr Pub/Sub with RabbitMQ backend
- Message Format: JSON with CloudEvents specification
- Delivery Guarantee: At-least-once delivery
- Consistency Model: Eventual consistency (5-30 seconds)
- Error Handling: Dead letter queue for failed message processing
- Retry Policy: Exponential backoff (max 3 retries)

**Event Flow**:

1. **Outbound**: Product Service publishes events to RabbitMQ topics
2. **Inbound**: Product Service subscribes to events from Review, Inventory, Analytics, and Q&A services
3. **Processing**: Events processed asynchronously by background workers
4. **Idempotency**: Event handlers use idempotency keys to prevent duplicate processing

#### 2.3.2 Outbound Events (Published)

Product Service publishes the following events to notify downstream services of catalog changes:

##### Event: `product.created`

**Purpose**: Notify services when a new product is added to the catalog

**Consumers**: Audit Service, Notification Service, Search Service, Analytics Service

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.created",
  "source": "product-service",
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "time": "2025-11-04T10:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "name": "Premium Cotton T-Shirt",
    "description": "Comfortable 100% cotton t-shirt with modern fit",
    "price": 29.99,
    "compareAtPrice": 39.99,
    "brand": "TrendyWear",
    "status": "active",
    "taxonomy": {
      "department": "Men",
      "category": "Clothing",
      "subcategory": "Tops",
      "productType": "T-Shirts"
    },
    "images": [
      {
        "url": "https://cdn.aioutlet.com/products/ts-001-front.jpg",
        "alt": "Front view of black t-shirt",
        "isPrimary": true,
        "order": 1
      }
    ],
    "variationType": "parent",
    "childCount": 6,
    "createdAt": "2025-11-04T10:30:00Z",
    "createdBy": "admin-user-123"
  },
  "metadata": {
    "correlationId": "req-xyz-789",
    "userId": "admin-user-123",
    "source": "api"
  }
}
```

##### Event: `product.updated`

**Purpose**: Notify services when product information changes

**Consumers**: Audit Service, Notification Service, Search Service, Cache Invalidation Service

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.updated",
  "source": "product-service",
  "id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
  "time": "2025-11-04T11:45:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "changedFields": ["price", "description", "images"],
    "before": {
      "price": 29.99,
      "description": "Comfortable 100% cotton t-shirt",
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-001-old.jpg",
          "alt": "Old image",
          "isPrimary": true,
          "order": 1
        }
      ]
    },
    "after": {
      "price": 24.99,
      "description": "Comfortable 100% cotton t-shirt with modern fit",
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
      ]
    },
    "updatedAt": "2025-11-04T11:45:00Z",
    "updatedBy": "admin-user-456"
  },
  "metadata": {
    "correlationId": "req-abc-123",
    "userId": "admin-user-456",
    "source": "api"
  }
}
```

##### Event: `product.deleted`

**Purpose**: Notify services when a product is soft-deleted

**Consumers**: Audit Service, Search Service, Cache Invalidation Service

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.deleted",
  "source": "product-service",
  "id": "c3d4e5f6-g7h8-9012-cdef-gh3456789012",
  "time": "2025-11-04T12:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "name": "Premium Cotton T-Shirt",
    "status": "deleted",
    "deletedAt": "2025-11-04T12:00:00Z",
    "deletedBy": "admin-user-789",
    "reason": "Product discontinued"
  },
  "metadata": {
    "correlationId": "req-def-456",
    "userId": "admin-user-789",
    "source": "api"
  }
}
```

##### Event: `product.price.changed`

**Purpose**: Notify services when product price is updated (critical for Order Service)

**Consumers**: Order Service, Notification Service, Analytics Service, Cart Service

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.price.changed",
  "source": "product-service",
  "id": "d4e5f6g7-h8i9-0123-defg-hi4567890123",
  "time": "2025-11-04T13:15:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "name": "Premium Cotton T-Shirt",
    "priceChange": {
      "oldPrice": 29.99,
      "newPrice": 24.99,
      "changePercentage": -16.67,
      "effectiveDate": "2025-11-04T13:15:00Z"
    },
    "compareAtPrice": 39.99,
    "updatedBy": "admin-user-456"
  },
  "metadata": {
    "correlationId": "req-ghi-789",
    "userId": "admin-user-456",
    "source": "api",
    "priority": "high"
  }
}
```

##### Event: `product.badge.assigned`

**Purpose**: Notify services when a badge is assigned (manual or automated)

**Consumers**: Notification Service, Analytics Service

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.badge.assigned",
  "source": "product-service",
  "id": "e5f6g7h8-i9j0-1234-efgh-ij5678901234",
  "time": "2025-11-04T14:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "badge": {
      "badgeId": "badge-best-seller-001",
      "type": "best-seller",
      "label": "Best Seller",
      "displayStyle": {
        "backgroundColor": "#FFD700",
        "textColor": "#000000",
        "icon": "star"
      },
      "priority": 1,
      "source": "auto",
      "assignedAt": "2025-11-04T14:00:00Z",
      "expiresAt": "2025-12-04T14:00:00Z",
      "criteria": {
        "metric": "sales",
        "threshold": 1000,
        "period": "30days"
      }
    },
    "assignedBy": "system"
  },
  "metadata": {
    "correlationId": "evt-badge-auto-001",
    "source": "analytics-trigger"
  }
}
```

##### Event: `product.badge.removed`

**Purpose**: Notify services when a badge is removed

**Consumers**: Notification Service, Analytics Service

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.badge.removed",
  "source": "product-service",
  "id": "f6g7h8i9-j0k1-2345-fghi-jk6789012345",
  "time": "2025-11-04T15:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "badge": {
      "badgeId": "badge-best-seller-001",
      "type": "best-seller",
      "removedAt": "2025-11-04T15:00:00Z",
      "reason": "sales_threshold_not_met"
    },
    "removedBy": "system"
  },
  "metadata": {
    "correlationId": "evt-badge-auto-002",
    "source": "analytics-trigger"
  }
}
```

##### Event: `product.bulk.import.started`

**Purpose**: Notify services when a bulk import job begins

**Consumers**: Notification Service, Admin Dashboard

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.bulk.import.started",
  "source": "product-service",
  "id": "g7h8i9j0-k1l2-3456-ghij-kl7890123456",
  "time": "2025-11-04T16:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "jobId": "import-job-20251104-001",
    "fileName": "products_november_2025.xlsx",
    "totalRows": 5000,
    "category": "Clothing",
    "importMode": "partial",
    "startedAt": "2025-11-04T16:00:00Z",
    "startedBy": "admin-user-123",
    "estimatedDuration": "15 minutes"
  },
  "metadata": {
    "correlationId": "job-import-001",
    "userId": "admin-user-123",
    "source": "bulk-import-api"
  }
}
```

##### Event: `product.bulk.import.completed`

**Purpose**: Notify services when a bulk import job completes successfully

**Consumers**: Notification Service, Admin Dashboard, Analytics Service

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.bulk.import.completed",
  "source": "product-service",
  "id": "h8i9j0k1-l2m3-4567-hijk-lm8901234567",
  "time": "2025-11-04T16:15:00Z",
  "datacontenttype": "application/json",
  "data": {
    "jobId": "import-job-20251104-001",
    "fileName": "products_november_2025.xlsx",
    "results": {
      "totalRows": 5000,
      "successfulImports": 4850,
      "failedImports": 150,
      "skippedRows": 0,
      "duration": "14 minutes 32 seconds"
    },
    "errorReportUrl": "https://cdn.aioutlet.com/reports/import-job-20251104-001-errors.csv",
    "completedAt": "2025-11-04T16:15:00Z",
    "completedBy": "admin-user-123"
  },
  "metadata": {
    "correlationId": "job-import-001",
    "userId": "admin-user-123",
    "source": "bulk-import-worker"
  }
}
```

##### Event: `product.bulk.import.failed`

**Purpose**: Notify services when a bulk import job fails

**Consumers**: Notification Service, Admin Dashboard

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.bulk.import.failed",
  "source": "product-service",
  "id": "i9j0k1l2-m3n4-5678-ijkl-mn9012345678",
  "time": "2025-11-04T16:20:00Z",
  "datacontenttype": "application/json",
  "data": {
    "jobId": "import-job-20251104-002",
    "fileName": "products_invalid.xlsx",
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "File format validation failed",
      "details": "Missing required columns: SKU, Price"
    },
    "failedAt": "2025-11-04T16:20:00Z",
    "startedBy": "admin-user-456"
  },
  "metadata": {
    "correlationId": "job-import-002",
    "userId": "admin-user-456",
    "source": "bulk-import-worker"
  }
}
```

#### 2.3.3 Inbound Events (Consumed)

Product Service consumes the following events from upstream services to maintain denormalized data for optimal read performance:

##### From Review Service

###### Event: `review.created`

**Purpose**: Update product review aggregates when a new review is posted

**Processing**: Increment review count, recalculate average rating, update rating distribution

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "review.created",
  "source": "review-service",
  "id": "j0k1l2m3-n4o5-6789-jklm-no0123456789",
  "time": "2025-11-04T17:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "reviewId": "review-12345",
    "productId": "507f1f77bcf86cd799439011",
    "userId": "user-67890",
    "rating": 5,
    "title": "Excellent quality!",
    "comment": "Love this t-shirt, fits perfectly",
    "verified": true,
    "createdAt": "2025-11-04T17:00:00Z"
  },
  "metadata": {
    "correlationId": "review-post-123",
    "userId": "user-67890"
  }
}
```

**Product Service Action**:

```javascript
// Update reviewAggregates in product document
{
  "reviewAggregates": {
    "averageRating": 4.52,  // Recalculated
    "totalReviewCount": 129, // Incremented
    "ratingDistribution": {
      "5": 85,  // Incremented
      "4": 30,
      "3": 10,
      "2": 3,
      "1": 1
    },
    "lastUpdated": "2025-11-04T17:00:05Z"
  }
}
```

###### Event: `review.updated`

**Purpose**: Recalculate product review aggregates when a review is edited

**Processing**: Recalculate average rating, update rating distribution if rating changed

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "review.updated",
  "source": "review-service",
  "id": "k1l2m3n4-o5p6-7890-klmn-op1234567890",
  "time": "2025-11-04T17:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "reviewId": "review-12345",
    "productId": "507f1f77bcf86cd799439011",
    "userId": "user-67890",
    "changes": {
      "rating": {
        "oldValue": 5,
        "newValue": 4
      },
      "comment": {
        "oldValue": "Love this t-shirt, fits perfectly",
        "newValue": "Good t-shirt, but sizing runs small"
      }
    },
    "updatedAt": "2025-11-04T17:30:00Z"
  },
  "metadata": {
    "correlationId": "review-update-456",
    "userId": "user-67890"
  }
}
```

**Product Service Action**:

```javascript
// Recalculate reviewAggregates
{
  "reviewAggregates": {
    "averageRating": 4.51,  // Recalculated (decreased)
    "totalReviewCount": 129, // Unchanged
    "ratingDistribution": {
      "5": 84,  // Decremented
      "4": 31,  // Incremented
      "3": 10,
      "2": 3,
      "1": 1
    },
    "lastUpdated": "2025-11-04T17:30:05Z"
  }
}
```

###### Event: `review.deleted`

**Purpose**: Update product review aggregates when a review is removed

**Processing**: Decrement review count, recalculate average rating, update rating distribution

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "review.deleted",
  "source": "review-service",
  "id": "l2m3n4o5-p6q7-8901-lmno-pq2345678901",
  "time": "2025-11-04T18:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "reviewId": "review-12345",
    "productId": "507f1f77bcf86cd799439011",
    "rating": 4,
    "deletedAt": "2025-11-04T18:00:00Z",
    "deletedBy": "user-67890",
    "reason": "user_request"
  },
  "metadata": {
    "correlationId": "review-delete-789",
    "userId": "user-67890"
  }
}
```

**Product Service Action**:

```javascript
// Update reviewAggregates
{
  "reviewAggregates": {
    "averageRating": 4.52,  // Recalculated
    "totalReviewCount": 128, // Decremented
    "ratingDistribution": {
      "5": 84,
      "4": 30,  // Decremented
      "3": 10,
      "2": 3,
      "1": 1
    },
    "lastUpdated": "2025-11-04T18:00:05Z"
  }
}
```

##### From Inventory Service

###### Event: `inventory.stock.updated`

**Purpose**: Update product availability status when stock levels change

**Processing**: Update availabilityStatus (in-stock, low-stock, out-of-stock), available quantity

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "inventory.stock.updated",
  "source": "inventory-service",
  "id": "m3n4o5p6-q7r8-9012-mnop-qr3456789012",
  "time": "2025-11-04T19:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "warehouseId": "warehouse-us-east-001",
    "stockChange": {
      "oldQuantity": 150,
      "newQuantity": 25,
      "changeReason": "order_fulfillment",
      "changeAmount": -125
    },
    "currentStock": {
      "totalAvailable": 25,
      "reserved": 5,
      "available": 20
    },
    "updatedAt": "2025-11-04T19:00:00Z"
  },
  "metadata": {
    "correlationId": "inv-update-001",
    "source": "order-fulfillment"
  }
}
```

**Product Service Action**:

```javascript
// Update availabilityStatus
{
  "availabilityStatus": {
    "status": "low-stock",  // Changed from "in-stock"
    "availableQuantity": 20,
    "reservedQuantity": 5,
    "totalQuantity": 25,
    "lowStockThreshold": 50,
    "lastUpdated": "2025-11-04T19:00:05Z"
  }
}

// Trigger badge auto-assignment (if low stock badge enabled)
// Publish event: product.badge.assigned (type: low-stock)
```

###### Event: `inventory.reserved`

**Purpose**: Update reserved quantity when inventory is reserved for an order

**Processing**: Adjust available quantity, update reservation count

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "inventory.reserved",
  "source": "inventory-service",
  "id": "n4o5p6q7-r8s9-0123-nopq-rs4567890123",
  "time": "2025-11-04T19:15:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "reservationId": "res-12345",
    "orderId": "order-67890",
    "quantityReserved": 2,
    "currentStock": {
      "totalAvailable": 25,
      "reserved": 7,
      "available": 18
    },
    "reservedAt": "2025-11-04T19:15:00Z",
    "expiresAt": "2025-11-04T19:30:00Z"
  },
  "metadata": {
    "correlationId": "order-67890",
    "orderId": "order-67890"
  }
}
```

**Product Service Action**:

```javascript
// Update availabilityStatus
{
  "availabilityStatus": {
    "status": "low-stock",
    "availableQuantity": 18,  // Updated
    "reservedQuantity": 7,    // Updated
    "totalQuantity": 25,
    "lowStockThreshold": 50,
    "lastUpdated": "2025-11-04T19:15:05Z"
  }
}
```

###### Event: `inventory.released`

**Purpose**: Update available quantity when reserved inventory is released

**Processing**: Increase available quantity, decrease reservation count

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "inventory.released",
  "source": "inventory-service",
  "id": "o5p6q7r8-s9t0-1234-opqr-st5678901234",
  "time": "2025-11-04T19:35:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "reservationId": "res-12345",
    "orderId": "order-67890",
    "quantityReleased": 2,
    "reason": "order_cancelled",
    "currentStock": {
      "totalAvailable": 25,
      "reserved": 5,
      "available": 20
    },
    "releasedAt": "2025-11-04T19:35:00Z"
  },
  "metadata": {
    "correlationId": "order-67890",
    "orderId": "order-67890"
  }
}
```

**Product Service Action**:

```javascript
// Update availabilityStatus
{
  "availabilityStatus": {
    "status": "low-stock",
    "availableQuantity": 20,  // Updated
    "reservedQuantity": 5,    // Updated
    "totalQuantity": 25,
    "lowStockThreshold": 50,
    "lastUpdated": "2025-11-04T19:35:05Z"
  }
}
```

##### From Analytics Service

###### Event: `analytics.product.sales.updated`

**Purpose**: Auto-assign or remove sales-based badges (Best Seller, Trending)

**Processing**: Check badge assignment criteria, assign/remove badges as needed

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "analytics.product.sales.updated",
  "source": "analytics-service",
  "id": "p6q7r8s9-t0u1-2345-pqrs-tu6789012345",
  "time": "2025-11-04T20:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "salesMetrics": {
      "last7Days": {
        "totalSales": 250,
        "revenue": 6247.5,
        "units": 250
      },
      "last30Days": {
        "totalSales": 1200,
        "revenue": 29988.0,
        "units": 1200
      },
      "rankInCategory": 3,
      "percentileInCategory": 95
    },
    "badgeEligibility": {
      "bestSeller": true,
      "trending": false
    },
    "updatedAt": "2025-11-04T20:00:00Z"
  },
  "metadata": {
    "correlationId": "analytics-batch-001",
    "source": "analytics-batch-job"
  }
}
```

**Product Service Action**:

```javascript
// Assign "Best Seller" badge if criteria met
if (salesMetrics.last30Days.units >= 1000 && badgeEligibility.bestSeller) {
  // Add badge to product.badges array
  // Publish event: product.badge.assigned
}

// Remove "Trending" badge if no longer eligible
if (!badgeEligibility.trending && product.badges.includes('trending')) {
  // Remove badge from product.badges array
  // Publish event: product.badge.removed
}
```

###### Event: `analytics.product.views.updated`

**Purpose**: Track product view metrics for analytics and badge assignment

**Processing**: Update view count, check trending badge eligibility

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "analytics.product.views.updated",
  "source": "analytics-service",
  "id": "q7r8s9t0-u1v2-3456-qrst-uv7890123456",
  "time": "2025-11-04T20:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "productId": "507f1f77bcf86cd799439011",
    "sku": "TS-BLK-001",
    "viewMetrics": {
      "last24Hours": 450,
      "last7Days": 2100,
      "last30Days": 8500,
      "uniqueVisitors": {
        "last24Hours": 380,
        "last7Days": 1800,
        "last30Days": 7200
      }
    },
    "badgeEligibility": {
      "trending": true,
      "criteria": {
        "viewGrowthRate": 150,
        "threshold": 100
      }
    },
    "updatedAt": "2025-11-04T20:30:00Z"
  },
  "metadata": {
    "correlationId": "analytics-batch-002",
    "source": "analytics-batch-job"
  }
}
```

**Product Service Action**:

```javascript
// Assign "Trending" badge if view growth exceeds threshold
if (badgeEligibility.trending && viewGrowthRate >= 100) {
  // Add badge to product.badges array
  // Publish event: product.badge.assigned
}
```

##### From Q&A Service

###### Event: `product.question.created`

**Purpose**: Update Q&A statistics when a new question is posted

**Processing**: Increment total question count

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.question.created",
  "source": "qa-service",
  "id": "r8s9t0u1-v2w3-4567-rstu-vw8901234567",
  "time": "2025-11-04T21:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "questionId": "q-12345",
    "productId": "507f1f77bcf86cd799439011",
    "userId": "user-54321",
    "questionText": "Does this t-shirt shrink after washing?",
    "createdAt": "2025-11-04T21:00:00Z"
  },
  "metadata": {
    "correlationId": "qa-post-123",
    "userId": "user-54321"
  }
}
```

**Product Service Action**:

```javascript
// Update qaStats
{
  "qaStats": {
    "totalQuestions": 24,        // Incremented
    "answeredQuestions": 20,     // Unchanged
    "unansweredQuestions": 4,    // Incremented
    "lastUpdated": "2025-11-04T21:00:05Z"
  }
}
```

###### Event: `product.answer.created`

**Purpose**: Update Q&A statistics when a question is answered

**Processing**: Increment answered question count

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.answer.created",
  "source": "qa-service",
  "id": "s9t0u1v2-w3x4-5678-stuv-wx9012345678",
  "time": "2025-11-04T21:30:00Z",
  "datacontenttype": "application/json",
  "data": {
    "answerId": "a-67890",
    "questionId": "q-12345",
    "productId": "507f1f77bcf86cd799439011",
    "userId": "vendor-rep-123",
    "answerText": "This t-shirt is pre-shrunk and should not shrink significantly if washed according to care instructions.",
    "answeredBy": "vendor",
    "createdAt": "2025-11-04T21:30:00Z"
  },
  "metadata": {
    "correlationId": "qa-answer-456",
    "userId": "vendor-rep-123"
  }
}
```

**Product Service Action**:

```javascript
// Update qaStats
{
  "qaStats": {
    "totalQuestions": 24,        // Unchanged
    "answeredQuestions": 21,     // Incremented
    "unansweredQuestions": 3,    // Decremented
    "lastUpdated": "2025-11-04T21:30:05Z"
  }
}
```

###### Event: `product.question.deleted`

**Purpose**: Update Q&A statistics when a question is removed

**Processing**: Decrement total question count, adjust answered count if applicable

**Schema**:

```json
{
  "specversion": "1.0",
  "type": "product.question.deleted",
  "source": "qa-service",
  "id": "t0u1v2w3-x4y5-6789-tuvw-xy0123456789",
  "time": "2025-11-04T22:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "questionId": "q-12345",
    "productId": "507f1f77bcf86cd799439011",
    "hadAnswer": true,
    "deletedAt": "2025-11-04T22:00:00Z",
    "deletedBy": "moderator-001",
    "reason": "duplicate_question"
  },
  "metadata": {
    "correlationId": "qa-delete-789",
    "userId": "moderator-001"
  }
}
```

**Product Service Action**:

```javascript
// Update qaStats
{
  "qaStats": {
    "totalQuestions": 23,        // Decremented
    "answeredQuestions": 20,     // Decremented (if hadAnswer: true)
    "unansweredQuestions": 3,    // Unchanged or decremented based on hadAnswer
    "lastUpdated": "2025-11-04T22:00:05Z"
  }
}
```

### 2.4 Data Model

Product Service stores product data in MongoDB with the following complete schema:

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
  "childSkus": ["TS-BLK-001-S", "TS-BLK-001-M", "TS-BLK-001-L"],
  "childCount": 6,

  // === ATTRIBUTES & SPECIFICATIONS ===
  "attributes": {
    "color": "Black",
    "size": "Medium",
    "material": "100% Cotton",
    "fit": "Regular Fit",
    "care": "Machine wash cold"
  },

  // === MEDIA ===
  "images": [
    {
      "url": "https://cdn.aioutlet.com/products/ts-001-front.jpg",
      "alt": "Front view of black t-shirt",
      "isPrimary": true,
      "order": 1
    }
  ],

  // === BADGES & LABELS (Manual + Automated) ===
  "badges": [
    {
      "type": "best-seller",
      "label": "Best Seller",
      "priority": 1,
      "source": "auto",
      "assignedAt": "2025-11-01T00:00:00Z"
    }
  ],

  // === SEO METADATA ===
  "seo": {
    "metaTitle": "Premium Cotton T-Shirt - Comfortable & Stylish",
    "metaDescription": "Shop our premium cotton t-shirt...",
    "slug": "premium-cotton-tshirt-black"
  },

  // === RESTRICTIONS & COMPLIANCE ===
  "restrictions": {
    "ageRestricted": false,
    "shippingRestrictions": [],
    "hazardousMaterial": false
  },

  // === DENORMALIZED DATA (From Other Services) ===

  // From Review Service
  "reviewAggregates": {
    "averageRating": 4.5,
    "totalReviewCount": 128,
    "lastUpdated": "2025-11-03T09:45:00Z"
  },

  // From Inventory Service
  "availabilityStatus": {
    "status": "in-stock",
    "availableQuantity": 150,
    "lastUpdated": "2025-11-03T09:50:00Z"
  },

  // From Q&A Service
  "qaStats": {
    "totalQuestions": 23,
    "answeredQuestions": 20,
    "lastUpdated": "2025-11-03T09:30:00Z"
  },

  // === AUDIT FIELDS ===
  "createdAt": "2025-10-01T10:00:00Z",
  "createdBy": "admin-user-123",
  "updatedAt": "2025-11-03T10:00:00Z",
  "updatedBy": "admin-user-456"
}
```

**Key Design Decisions**:

- **Denormalized Data**: Review aggregates, inventory status, and Q&A stats are consumed from other services via events for optimal read performance (eventual consistency: 5-30 seconds)
- **Taxonomy Hierarchy**: Supports 4-level categorization (Department → Category → Subcategory → Product Type)
- **Variations**: Parent-child relationships enable product variations (e.g., different sizes/colors)
- **Media Management**: Support for multiple images and videos with ordering
- **Badge System**: Both manual (admin-assigned) and automated (analytics-driven) badges

### 2.5 Database Indexes

**Core Indexes**:

```javascript
// Primary Key
{ "_id": 1 }

// Unique SKU Index
{ "sku": 1 }  // Unique constraint

// Search & Filter Indexes
{ "status": 1, "taxonomy.category": 1, "price": 1 }
{ "status": 1, "reviewAggregates.averageRating": -1 }
{ "status": 1, "createdAt": -1 }

// Full-Text Search Index
{ "name": "text", "description": "text", "tags": "text", "searchKeywords": "text" }
```

**Performance Optimization**: Compound indexes support common query patterns (category browsing + filtering by price/rating), while the text index enables efficient product search across multiple fields.

### 2.6 Inter-Service Communication

Product Service provides synchronous APIs for other services to query product information:

**Product Existence Check**: Other services (Order Service, Cart Service) can verify if a product exists and is active before processing operations.

**Endpoint**: `GET /api/products/{productId}/exists`

- Returns: `{ exists: true/false, isActive: true/false }`
- Used by: Order Service (order creation), Cart Service (add to cart)
- Performance: Optimized for low latency (frequently called)

**Batch Product Lookup**: Services can retrieve multiple products in a single request to reduce network overhead.

**Endpoint**: `POST /api/products/batch`

- Request: `{ productIds: ["id1", "id2", ...] }`
- Returns: Array of product objects
- Used by: Order Service, Cart Service, Recommendation Service

---

### 2.7 Environment Variables

This section documents all environment variables required to run the Product Service.

#### 2.7.1 Database Configuration

| Variable                | Description                        | Example                     | Required | Default |
| ----------------------- | ---------------------------------- | --------------------------- | -------- | ------- |
| `MONGODB_URI`           | MongoDB connection string          | `mongodb://localhost:27017` | Yes      | -       |
| `MONGODB_DATABASE`      | Database name                      | `aioutlet_products`         | Yes      | -       |
| `MONGODB_MAX_POOL_SIZE` | Maximum connection pool size       | `100`                       | No       | `50`    |
| `MONGODB_MIN_POOL_SIZE` | Minimum connection pool size       | `10`                        | No       | `5`     |
| `MONGODB_TIMEOUT_MS`    | Connection timeout in milliseconds | `5000`                      | No       | `10000` |

#### 2.7.2 Message Broker Configuration

| Variable                | Description               | Example           | Required | Default           |
| ----------------------- | ------------------------- | ----------------- | -------- | ----------------- |
| `RABBITMQ_HOST`         | RabbitMQ hostname         | `localhost`       | Yes      | -                 |
| `RABBITMQ_PORT`         | RabbitMQ port             | `5672`            | Yes      | `5672`            |
| `RABBITMQ_USER`         | RabbitMQ username         | `admin`           | Yes      | -                 |
| `RABBITMQ_PASSWORD`     | RabbitMQ password         | `secretpassword`  | Yes      | -                 |
| `RABBITMQ_VHOST`        | RabbitMQ virtual host     | `/aioutlet`       | No       | `/`               |
| `RABBITMQ_EXCHANGE`     | Exchange name for pub/sub | `aioutlet.events` | No       | `aioutlet.events` |
| `RABBITMQ_QUEUE_PREFIX` | Prefix for queue names    | `product-service` | No       | `product-service` |

#### 2.7.3 Dapr Configuration

| Variable           | Description                        | Example           | Required | Default  |
| ------------------ | ---------------------------------- | ----------------- | -------- | -------- |
| `DAPR_HTTP_PORT`   | Dapr HTTP sidecar port             | `3500`            | No       | `3500`   |
| `DAPR_GRPC_PORT`   | Dapr gRPC sidecar port             | `50001`           | No       | `50001`  |
| `DAPR_PUBSUB_NAME` | Dapr pub/sub component name        | `product-pubsub`  | Yes      | `pubsub` |
| `DAPR_APP_ID`      | Dapr application identifier        | `product-service` | Yes      | -        |
| `DAPR_APP_PORT`    | Port where product service listens | `8003`            | No       | `8003`   |

#### 2.7.4 Authentication & Authorization

| Variable         | Description                                  | Example                           | Required | Default |
| ---------------- | -------------------------------------------- | --------------------------------- | -------- | ------- |
| `JWT_PUBLIC_KEY` | Public key for JWT verification (PEM format) | `-----BEGIN PUBLIC KEY-----\n...` | Yes      | -       |
| `JWT_ALGORITHM`  | JWT signature algorithm                      | `RS256`                           | No       | `RS256` |
| `JWT_ISSUER`     | Expected JWT issuer                          | `aioutlet-auth-service`           | No       | -       |
| `JWT_AUDIENCE`   | Expected JWT audience                        | `aioutlet-api`                    | No       | -       |

#### 2.7.5 Service Configuration

| Variable          | Description                            | Example                                               | Required | Default           |
| ----------------- | -------------------------------------- | ----------------------------------------------------- | -------- | ----------------- |
| `SERVICE_NAME`    | Service name for logging/metrics       | `product-service`                                     | No       | `product-service` |
| `SERVICE_VERSION` | Service version                        | `1.0.0`                                               | No       | `1.0.0`           |
| `SERVICE_PORT`    | HTTP server port                       | `8003`                                                | No       | `8003`            |
| `SERVICE_HOST`    | Host to bind to                        | `0.0.0.0`                                             | No       | `0.0.0.0`         |
| `ENVIRONMENT`     | Deployment environment                 | `production`                                          | Yes      | `development`     |
| `LOG_LEVEL`       | Logging level                          | `info`                                                | No       | `info`            |
| `ENABLE_SWAGGER`  | Enable Swagger UI documentation        | `true`                                                | No       | `false`           |
| `ENABLE_CORS`     | Enable CORS                            | `true`                                                | No       | `true`            |
| `CORS_ORIGINS`    | Allowed CORS origins (comma-separated) | `https://www.aioutlet.com,https://admin.aioutlet.com` | No       | `*`               |

#### 2.7.6 Performance & Caching

| Variable                  | Description                       | Example | Required | Default |
| ------------------------- | --------------------------------- | ------- | -------- | ------- |
| `CACHE_ENABLED`           | Enable caching layer              | `true`  | No       | `false` |
| `CACHE_TTL_SECONDS`       | Cache time-to-live in seconds     | `300`   | No       | `300`   |
| `RATE_LIMIT_ENABLED`      | Enable rate limiting              | `true`  | No       | `true`  |
| `RATE_LIMIT_MAX_REQUESTS` | Max requests per window           | `1000`  | No       | `1000`  |
| `RATE_LIMIT_WINDOW_MS`    | Rate limit window in milliseconds | `60000` | No       | `60000` |
| `MAX_PAGE_SIZE`           | Maximum pagination limit          | `100`   | No       | `100`   |
| `DEFAULT_PAGE_SIZE`       | Default pagination limit          | `20`    | No       | `20`    |
| `SEARCH_TIMEOUT_MS`       | Search query timeout              | `5000`  | No       | `5000`  |

#### 2.7.7 File Upload Configuration

| Variable                  | Description                     | Example                    | Required | Default        |
| ------------------------- | ------------------------------- | -------------------------- | -------- | -------------- |
| `MAX_IMPORT_FILE_SIZE_MB` | Maximum Excel import file size  | `50`                       | No       | `50`           |
| `MAX_IMAGE_ZIP_SIZE_MB`   | Maximum image ZIP file size     | `100`                      | No       | `100`          |
| `UPLOAD_TEMP_DIR`         | Temporary upload directory      | `/tmp/uploads`             | No       | `/tmp/uploads` |
| `CDN_BASE_URL`            | CDN base URL for product images | `https://cdn.aioutlet.com` | No       | -              |

#### 2.7.8 Monitoring & Observability

| Variable              | Description                   | Example     | Required | Default     |
| --------------------- | ----------------------------- | ----------- | -------- | ----------- |
| `METRICS_ENABLED`     | Enable Prometheus metrics     | `true`      | No       | `true`      |
| `METRICS_PORT`        | Metrics endpoint port         | `9090`      | No       | `9090`      |
| `TRACING_ENABLED`     | Enable distributed tracing    | `true`      | No       | `true`      |
| `TRACING_SAMPLE_RATE` | Trace sampling rate (0.0-1.0) | `0.1`       | No       | `0.1`       |
| `JAEGER_AGENT_HOST`   | Jaeger agent hostname         | `localhost` | No       | `localhost` |
| `JAEGER_AGENT_PORT`   | Jaeger agent port             | `6831`      | No       | `6831`      |
| `LOG_FORMAT`          | Log output format             | `json`      | No       | `json`      |
| `LOG_OUTPUT`          | Log output destination        | `stdout`    | No       | `stdout`    |

#### 2.7.9 Health Check Configuration

| Variable                        | Description             | Example | Required | Default |
| ------------------------------- | ----------------------- | ------- | -------- | ------- |
| `HEALTH_CHECK_INTERVAL_SECONDS` | Health check interval   | `30`    | No       | `30`    |
| `LIVENESS_TIMEOUT_MS`           | Liveness probe timeout  | `3000`  | No       | `3000`  |
| `READINESS_TIMEOUT_MS`          | Readiness probe timeout | `5000`  | No       | `5000`  |
| `STARTUP_TIMEOUT_SECONDS`       | Service startup timeout | `60`    | No       | `60`    |

#### 2.7.10 Event Publishing Configuration

| Variable                   | Description                   | Example | Required | Default |
| -------------------------- | ----------------------------- | ------- | -------- | ------- |
| `EVENT_RETRY_MAX_ATTEMPTS` | Maximum event publish retries | `3`     | No       | `3`     |
| `EVENT_RETRY_DELAY_MS`     | Initial retry delay           | `1000`  | No       | `1000`  |
| `EVENT_RETRY_MAX_DELAY_MS` | Maximum retry delay           | `10000` | No       | `10000` |
| `EVENT_BATCH_SIZE`         | Event batch size              | `100`   | No       | `100`   |
| `EVENT_BATCH_TIMEOUT_MS`   | Event batch timeout           | `5000`  | No       | `5000`  |

#### 2.7.11 Example Configuration Files

**Development Environment** (`.env.development`):

```bash
# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=aioutlet_products_dev

# Message Broker
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=admin123

# Dapr
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001
DAPR_PUBSUB_NAME=product-pubsub
DAPR_APP_ID=product-service
DAPR_APP_PORT=8003

# Authentication
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0B...\n-----END PUBLIC KEY-----
JWT_ALGORITHM=RS256

# Service
SERVICE_NAME=product-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8003
ENVIRONMENT=development
LOG_LEVEL=debug
ENABLE_SWAGGER=true
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Performance
CACHE_ENABLED=false
RATE_LIMIT_ENABLED=false

# Monitoring
METRICS_ENABLED=true
TRACING_ENABLED=true
TRACING_SAMPLE_RATE=1.0
LOG_FORMAT=pretty
```

**Production Environment** (`.env.production`):

```bash
# Database
MONGODB_URI=mongodb://prod-mongo-cluster:27017
MONGODB_DATABASE=aioutlet_products
MONGODB_MAX_POOL_SIZE=100

# Message Broker
RABBITMQ_HOST=prod-rabbitmq-cluster
RABBITMQ_PORT=5672
RABBITMQ_USER=${RABBITMQ_USER_SECRET}
RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD_SECRET}

# Dapr
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001
DAPR_PUBSUB_NAME=product-pubsub
DAPR_APP_ID=product-service
DAPR_APP_PORT=8003

# Authentication
JWT_PUBLIC_KEY=${JWT_PUBLIC_KEY_SECRET}
JWT_ALGORITHM=RS256
JWT_ISSUER=aioutlet-auth-service
JWT_AUDIENCE=aioutlet-api

# Service
SERVICE_NAME=product-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8003
ENVIRONMENT=production
LOG_LEVEL=info
ENABLE_SWAGGER=false
ENABLE_CORS=true
CORS_ORIGINS=https://www.aioutlet.com,https://admin.aioutlet.com

# Performance
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=1000
RATE_LIMIT_WINDOW_MS=60000

# File Upload
MAX_IMPORT_FILE_SIZE_MB=50
MAX_IMAGE_ZIP_SIZE_MB=100
CDN_BASE_URL=https://cdn.aioutlet.com

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
TRACING_ENABLED=true
TRACING_SAMPLE_RATE=0.1
JAEGER_AGENT_HOST=jaeger-agent
JAEGER_AGENT_PORT=6831
LOG_FORMAT=json
LOG_OUTPUT=stdout
```

**Kubernetes ConfigMap Example** (`product-service-config.yaml`):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: product-service-config
  namespace: aioutlet
data:
  SERVICE_NAME: 'product-service'
  SERVICE_VERSION: '1.0.0'
  SERVICE_PORT: '8003'
  ENVIRONMENT: 'production'
  LOG_LEVEL: 'info'
  LOG_FORMAT: 'json'

  # MongoDB
  MONGODB_URI: 'mongodb://mongo-service:27017'
  MONGODB_DATABASE: 'aioutlet_products'
  MONGODB_MAX_POOL_SIZE: '100'

  # RabbitMQ
  RABBITMQ_HOST: 'rabbitmq-service'
  RABBITMQ_PORT: '5672'
  RABBITMQ_VHOST: '/aioutlet'

  # Dapr
  DAPR_HTTP_PORT: '3500'
  DAPR_GRPC_PORT: '50001'
  DAPR_PUBSUB_NAME: 'product-pubsub'
  DAPR_APP_ID: 'product-service'
  DAPR_APP_PORT: '8003'

  # Performance
  CACHE_ENABLED: 'true'
  RATE_LIMIT_ENABLED: 'true'
  MAX_PAGE_SIZE: '100'

  # Monitoring
  METRICS_ENABLED: 'true'
  TRACING_ENABLED: 'true'
  JAEGER_AGENT_HOST: 'jaeger-agent'
```

---

## 3. API Specifications

### 3.1 Authentication

All API endpoints (except health checks) require JWT authentication via the `Authorization: Bearer <token>` header.

### 3.2 Product Management APIs

#### 3.2.1 Create Product

**Endpoint**: `POST /api/products`

**Description**: Create a new product in the catalog

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Headers**:

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Correlation-ID: req-abc-123 (optional)
```

**Request Body**:

```json
{
  "name": "Premium Cotton T-Shirt",
  "description": "Comfortable 100% cotton t-shirt with modern fit",
  "longDescription": "This premium cotton t-shirt features breathable fabric, reinforced stitching, and a contemporary cut that flatters all body types. Perfect for casual wear or layering.",
  "price": 29.99,
  "compareAtPrice": 39.99,
  "sku": "TS-BLK-001",
  "brand": "TrendyWear",
  "taxonomy": {
    "department": "Men",
    "category": "Clothing",
    "subcategory": "Tops",
    "productType": "T-Shirts"
  },
  "attributes": {
    "color": "Black",
    "size": "Medium",
    "material": "100% Cotton",
    "fit": "Regular Fit",
    "care": "Machine wash cold"
  },
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
  "tags": ["cotton", "casual", "comfortable", "basic"],
  "seo": {
    "metaTitle": "Premium Cotton T-Shirt - Black | AIOutlet",
    "metaDescription": "Shop our premium cotton t-shirt in black. Comfortable, durable, and stylish.",
    "slug": "premium-cotton-tshirt-black"
  }
}
```

**Response** (201 Created):

```json
{
  "productId": "507f1f77bcf86cd799439011",
  "sku": "TS-BLK-001",
  "name": "Premium Cotton T-Shirt",
  "status": "active",
  "price": 29.99,
  "createdAt": "2025-11-04T10:30:00Z",
  "createdBy": "admin-user-123",
  "message": "Product created successfully"
}
```

**Error Responses**:

- `400 Bad Request` - Validation error (missing required fields, invalid data)
- `401 Unauthorized` - Invalid or missing JWT token
- `403 Forbidden` - Insufficient permissions (non-admin user)
- `409 Conflict` - Duplicate SKU

#### 3.2.2 Get Product by ID

**Endpoint**: `GET /api/products/{productId}`

**Description**: Retrieve a single product by its ID

**Authentication**: Optional (public endpoint for active products)

**Request Headers**:

```http
Authorization: Bearer <jwt_token> (optional, required for draft/deleted products)
X-Correlation-ID: req-xyz-456 (optional)
```

**Response** (200 OK):

```json
{
  "productId": "507f1f77bcf86cd799439011",
  "name": "Premium Cotton T-Shirt",
  "description": "Comfortable 100% cotton t-shirt with modern fit",
  "longDescription": "This premium cotton t-shirt features...",
  "price": 29.99,
  "compareAtPrice": 39.99,
  "sku": "TS-BLK-001",
  "brand": "TrendyWear",
  "status": "active",
  "taxonomy": {
    "department": "Men",
    "category": "Clothing",
    "subcategory": "Tops",
    "productType": "T-Shirts"
  },
  "attributes": {
    "color": "Black",
    "size": "Medium",
    "material": "100% Cotton",
    "fit": "Regular Fit"
  },
  "images": [
    {
      "url": "https://cdn.aioutlet.com/products/ts-001-front.jpg",
      "alt": "Front view of black t-shirt",
      "isPrimary": true,
      "order": 1
    }
  ],
  "badges": [
    {
      "type": "best-seller",
      "label": "Best Seller",
      "priority": 1
    }
  ],
  "reviewAggregates": {
    "averageRating": 4.5,
    "totalReviewCount": 128,
    "ratingDistribution": {
      "5": 84,
      "4": 30,
      "3": 10,
      "2": 3,
      "1": 1
    }
  },
  "availabilityStatus": {
    "status": "in-stock",
    "availableQuantity": 150
  },
  "qaStats": {
    "totalQuestions": 23,
    "answeredQuestions": 20
  },
  "variationType": "parent",
  "childCount": 6,
  "seo": {
    "metaTitle": "Premium Cotton T-Shirt - Black | AIOutlet",
    "metaDescription": "Shop our premium cotton t-shirt in black.",
    "slug": "premium-cotton-tshirt-black"
  },
  "createdAt": "2025-10-01T10:00:00Z",
  "updatedAt": "2025-11-03T10:00:00Z"
}
```

**Error Responses**:

- `404 Not Found` - Product does not exist
- `403 Forbidden` - Attempting to access draft/deleted product without admin role

#### 3.2.3 Update Product

**Endpoint**: `PUT /api/products/{productId}`

**Description**: Update an existing product (partial updates supported)

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Headers**:

```http
Authorization: Bearer <jwt_token>
Content-Type: application/json
X-Correlation-ID: req-def-789
```

**Request Body** (partial update example):

```json
{
  "price": 24.99,
  "compareAtPrice": 34.99,
  "description": "Comfortable 100% cotton t-shirt with modern fit - NOW ON SALE!",
  "images": [
    {
      "url": "https://cdn.aioutlet.com/products/ts-001-front-new.jpg",
      "alt": "Updated front view of black t-shirt",
      "isPrimary": true,
      "order": 1
    }
  ]
}
```

**Response** (200 OK):

```json
{
  "productId": "507f1f77bcf86cd799439011",
  "sku": "TS-BLK-001",
  "updatedFields": ["price", "compareAtPrice", "description", "images"],
  "updatedAt": "2025-11-04T11:45:00Z",
  "updatedBy": "admin-user-456",
  "message": "Product updated successfully"
}
```

**Error Responses**:

- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Invalid JWT token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Product does not exist
- `409 Conflict` - SKU conflict (if trying to update SKU to existing one)

#### 3.2.4 Delete Product

**Endpoint**: `DELETE /api/products/{productId}`

**Description**: Soft-delete a product (sets status to 'deleted')

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Headers**:

```http
Authorization: Bearer <jwt_token>
X-Correlation-ID: req-ghi-012
```

**Response** (204 No Content):

```
(Empty body)
```

**Error Responses**:

- `401 Unauthorized` - Invalid JWT token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Product does not exist

#### 3.2.5 Check Product Existence

**Endpoint**: `GET /api/products/{productId}/exists`

**Description**: Lightweight endpoint to check if a product exists and is active

**Authentication**: Optional

**Response** (200 OK):

```json
{
  "productId": "507f1f77bcf86cd799439011",
  "exists": true,
  "isActive": true,
  "sku": "TS-BLK-001"
}
```

**Error Responses**:

- `404 Not Found` - Product does not exist

#### 3.2.6 Batch Product Lookup

**Endpoint**: `POST /api/products/batch`

**Description**: Retrieve multiple products in a single request

**Authentication**: Optional (public endpoint for active products)

**Request Body**:

```json
{
  "productIds": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"],
  "fields": ["productId", "name", "price", "sku", "images", "availabilityStatus"]
}
```

**Response** (200 OK):

```json
{
  "products": [
    {
      "productId": "507f1f77bcf86cd799439011",
      "name": "Premium Cotton T-Shirt",
      "price": 29.99,
      "sku": "TS-BLK-001",
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-001-front.jpg",
          "alt": "Front view",
          "isPrimary": true
        }
      ],
      "availabilityStatus": {
        "status": "in-stock",
        "availableQuantity": 150
      }
    },
    {
      "productId": "507f1f77bcf86cd799439012",
      "name": "Cotton Hoodie",
      "price": 49.99,
      "sku": "HD-GRY-002",
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/hd-002-front.jpg",
          "alt": "Front view",
          "isPrimary": true
        }
      ],
      "availabilityStatus": {
        "status": "low-stock",
        "availableQuantity": 5
      }
    }
  ],
  "notFound": ["507f1f77bcf86cd799439013"],
  "totalRequested": 3,
  "totalFound": 2
}
```

#### 3.2.7 Bulk Product Import

**Endpoint**: `POST /api/products/bulk/import`

**Description**: Import multiple products via Excel file (asynchronous operation)

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Headers**:

```http
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
X-Correlation-ID: req-jkl-345
```

**Request Body** (multipart/form-data):

```
file: products_november_2025.xlsx
category: Clothing
importMode: partial (or "all-or-nothing")
```

**Response** (202 Accepted):

```json
{
  "jobId": "import-job-20251104-001",
  "status": "processing",
  "fileName": "products_november_2025.xlsx",
  "totalRows": 5000,
  "category": "Clothing",
  "importMode": "partial",
  "startedAt": "2025-11-04T16:00:00Z",
  "startedBy": "admin-user-123",
  "estimatedDuration": "15 minutes",
  "statusUrl": "/api/products/bulk/jobs/import-job-20251104-001"
}
```

**Error Responses**:

- `400 Bad Request` - Invalid file format, missing required columns
- `401 Unauthorized` - Invalid JWT token
- `403 Forbidden` - Insufficient permissions
- `413 Payload Too Large` - File exceeds size limit

#### 3.2.8 Get Bulk Import Status

**Endpoint**: `GET /api/products/bulk/jobs/{jobId}`

**Description**: Check the status of a bulk import job

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Response** (200 OK - In Progress):

```json
{
  "jobId": "import-job-20251104-001",
  "status": "processing",
  "fileName": "products_november_2025.xlsx",
  "progress": {
    "totalRows": 5000,
    "processedRows": 2500,
    "successfulImports": 2400,
    "failedImports": 100,
    "percentComplete": 50
  },
  "startedAt": "2025-11-04T16:00:00Z",
  "estimatedCompletion": "2025-11-04T16:15:00Z"
}
```

**Response** (200 OK - Completed):

```json
{
  "jobId": "import-job-20251104-001",
  "status": "completed",
  "fileName": "products_november_2025.xlsx",
  "results": {
    "totalRows": 5000,
    "successfulImports": 4850,
    "failedImports": 150,
    "skippedRows": 0,
    "duration": "14 minutes 32 seconds"
  },
  "errorReportUrl": "/api/products/bulk/jobs/import-job-20251104-001/errors",
  "completedAt": "2025-11-04T16:15:00Z"
}
```

**Error Responses**:

- `404 Not Found` - Job ID does not exist

#### 3.2.9 Create Product Variations

**Endpoint**: `POST /api/products/variations`

**Description**: Create a parent product with multiple variations

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Body**:

```json
{
  "parent": {
    "name": "Premium Cotton T-Shirt",
    "description": "Comfortable 100% cotton t-shirt",
    "brand": "TrendyWear",
    "taxonomy": {
      "department": "Men",
      "category": "Clothing",
      "subcategory": "Tops",
      "productType": "T-Shirts"
    },
    "variationTheme": "Color-Size",
    "variationAttributes": ["color", "size"]
  },
  "variations": [
    {
      "sku": "TS-BLK-001-S",
      "price": 29.99,
      "attributes": {
        "color": "Black",
        "size": "Small"
      },
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-blk-s.jpg",
          "alt": "Black t-shirt small",
          "isPrimary": true
        }
      ]
    },
    {
      "sku": "TS-BLK-001-M",
      "price": 29.99,
      "attributes": {
        "color": "Black",
        "size": "Medium"
      },
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-blk-m.jpg",
          "alt": "Black t-shirt medium",
          "isPrimary": true
        }
      ]
    },
    {
      "sku": "TS-BLK-001-L",
      "price": 29.99,
      "attributes": {
        "color": "Black",
        "size": "Large"
      },
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-blk-l.jpg",
          "alt": "Black t-shirt large",
          "isPrimary": true
        }
      ]
    }
  ]
}
```

**Response** (201 Created):

```json
{
  "parentProductId": "507f1f77bcf86cd799439011",
  "parentSku": "TS-BLK-001-PARENT",
  "variationCount": 3,
  "variations": [
    {
      "productId": "507f1f77bcf86cd799439021",
      "sku": "TS-BLK-001-S",
      "attributes": {
        "color": "Black",
        "size": "Small"
      }
    },
    {
      "productId": "507f1f77bcf86cd799439022",
      "sku": "TS-BLK-001-M",
      "attributes": {
        "color": "Black",
        "size": "Medium"
      }
    },
    {
      "productId": "507f1f77bcf86cd799439023",
      "sku": "TS-BLK-001-L",
      "attributes": {
        "color": "Black",
        "size": "Large"
      }
    }
  ],
  "createdAt": "2025-11-04T12:00:00Z",
  "message": "Parent product and 3 variations created successfully"
}
```

#### 3.2.10 Assign Badge to Product

**Endpoint**: `POST /api/products/{productId}/badges`

**Description**: Manually assign a badge to a product

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Body**:

```json
{
  "type": "limited-time-deal",
  "label": "Limited Time Deal",
  "displayStyle": {
    "backgroundColor": "#FF6B6B",
    "textColor": "#FFFFFF",
    "icon": "clock"
  },
  "priority": 2,
  "expiresAt": "2025-11-30T23:59:59Z",
  "visibilityRules": {
    "showOnSearch": true,
    "showOnDetail": true,
    "showOnCart": true
  }
}
```

**Response** (201 Created):

```json
{
  "badgeId": "badge-ltd-deal-001",
  "productId": "507f1f77bcf86cd799439011",
  "sku": "TS-BLK-001",
  "badge": {
    "type": "limited-time-deal",
    "label": "Limited Time Deal",
    "priority": 2,
    "source": "manual",
    "assignedAt": "2025-11-04T14:00:00Z",
    "expiresAt": "2025-11-30T23:59:59Z"
  },
  "message": "Badge assigned successfully"
}
```

#### 3.2.11 Remove Badge from Product

**Endpoint**: `DELETE /api/products/{productId}/badges/{badgeId}`

**Description**: Remove a badge from a product

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Headers**:

```http
Authorization: Bearer <jwt_token>
X-Correlation-ID: req-mno-678
```

**Response** (204 No Content):

```
(Empty body)
```

**Error Responses**:

- `404 Not Found` - Product or badge does not exist
- `401 Unauthorized` - Invalid JWT token
- `403 Forbidden` - Insufficient permissions

#### 3.2.12 Bulk Badge Assignment

**Endpoint**: `POST /api/products/badges/bulk`

**Description**: Assign a badge to multiple products

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Body**:

```json
{
  "productIds": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012", "507f1f77bcf86cd799439013"],
  "badge": {
    "type": "seasonal-sale",
    "label": "Winter Sale",
    "displayStyle": {
      "backgroundColor": "#4A90E2",
      "textColor": "#FFFFFF"
    },
    "priority": 3,
    "expiresAt": "2025-12-31T23:59:59Z"
  }
}
```

**Response** (200 OK):

```json
{
  "totalRequested": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "productId": "507f1f77bcf86cd799439011",
      "sku": "TS-BLK-001",
      "status": "success",
      "badgeId": "badge-winter-001"
    },
    {
      "productId": "507f1f77bcf86cd799439012",
      "sku": "HD-GRY-002",
      "status": "success",
      "badgeId": "badge-winter-002"
    },
    {
      "productId": "507f1f77bcf86cd799439013",
      "sku": "JN-BLU-003",
      "status": "success",
      "badgeId": "badge-winter-003"
    }
  ],
  "message": "Bulk badge assignment completed"
}
```

#### 3.2.13 Update SEO Metadata

**Endpoint**: `PUT /api/products/{productId}/seo`

**Description**: Update SEO metadata for a product

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Body**:

```json
{
  "metaTitle": "Buy Premium Cotton T-Shirt Online - Best Price | AIOutlet",
  "metaDescription": "Shop our premium cotton t-shirt. Free shipping on orders over $50. 100% satisfaction guaranteed.",
  "metaKeywords": ["cotton t-shirt", "mens clothing", "casual wear", "comfortable tshirt"],
  "slug": "premium-cotton-tshirt-black-mens",
  "canonicalUrl": "https://www.aioutlet.com/products/premium-cotton-tshirt-black-mens",
  "ogTitle": "Premium Cotton T-Shirt - AIOutlet",
  "ogDescription": "Comfortable 100% cotton t-shirt with modern fit",
  "ogImage": "https://cdn.aioutlet.com/products/ts-001-og.jpg",
  "structuredData": {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Premium Cotton T-Shirt",
    "description": "Comfortable 100% cotton t-shirt",
    "brand": {
      "@type": "Brand",
      "name": "TrendyWear"
    },
    "offers": {
      "@type": "Offer",
      "price": "29.99",
      "priceCurrency": "USD",
      "availability": "https://schema.org/InStock"
    }
  }
}
```

**Response** (200 OK):

```json
{
  "productId": "507f1f77bcf86cd799439011",
  "sku": "TS-BLK-001",
  "seo": {
    "metaTitle": "Buy Premium Cotton T-Shirt Online - Best Price | AIOutlet",
    "slug": "premium-cotton-tshirt-black-mens",
    "updatedAt": "2025-11-04T15:30:00Z"
  },
  "message": "SEO metadata updated successfully"
}
```

#### 3.2.14 Download Import Template

**Endpoint**: `GET /api/products/bulk/template`

**Description**: Download category-specific Excel template for bulk import

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Query Parameters**:

- `category` (required): Category for which to generate template (e.g., "Clothing", "Electronics")

**Request Example**:

```http
GET /api/products/bulk/template?category=Clothing
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):

```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="product_import_template_clothing.xlsx"

[Binary Excel file content]
```

**Template Columns**:

- SKU (required)
- Name (required)
- Description (required)
- Price (required)
- CompareAtPrice (optional)
- Brand (required)
- Department (optional)
- Category (optional)
- Subcategory (optional)
- ProductType (optional)
- Color (optional)
- Size (optional)
- Material (optional)
- ImageURL1-5 (optional)
- Tags (comma-separated)
- MetaTitle (optional)
- MetaDescription (optional)

#### 3.2.15 Get Bulk Import Errors

**Endpoint**: `GET /api/products/bulk/jobs/{jobId}/errors`

**Description**: Download detailed error report for failed bulk import rows

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Response** (200 OK):

```
Content-Type: text/csv
Content-Disposition: attachment; filename="import_errors_import-job-20251104-001.csv"

Row,SKU,Field,Error,Recommendation
15,TS-001-INVALID,price,"Invalid price format: 'twenty dollars'","Use numeric format: 29.99"
23,HD-002-DUP,sku,"Duplicate SKU: HD-002-DUP already exists","Use unique SKU or update existing product"
47,JN-003-BAD,brand,"Brand cannot be empty","Provide valid brand name"
```

**Error Responses**:

- `404 Not Found` - Job ID does not exist or has no errors

#### 3.2.16 Bulk Image Upload

**Endpoint**: `POST /api/products/bulk/images`

**Description**: Upload multiple product images in ZIP format (maps images to products by filename convention)

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Headers**:

```http
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Request Body** (multipart/form-data):

```
file: product_images_november_2025.zip
mappingMode: sku-based (or "product-id-based")
```

**Filename Convention**:

- SKU-based: `{SKU}-{variant}.jpg` (e.g., `TS-BLK-001-front.jpg`, `TS-BLK-001-back.jpg`)
- Product ID-based: `{productId}-{variant}.jpg`

**Response** (202 Accepted):

```json
{
  "jobId": "image-upload-20251104-002",
  "status": "processing",
  "fileName": "product_images_november_2025.zip",
  "totalImages": 1500,
  "mappingMode": "sku-based",
  "startedAt": "2025-11-04T17:00:00Z",
  "estimatedDuration": "5 minutes",
  "statusUrl": "/api/products/bulk/jobs/image-upload-20251104-002"
}
```

#### 3.2.17 Get Product Variations

**Endpoint**: `GET /api/products/{parentId}/variations`

**Description**: List all variations of a parent product

**Authentication**: Optional (public for active products)

**Query Parameters**:

- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)
- `status` (optional): Filter by status (active/draft/deleted)
- `attributes` (optional): Filter by specific attributes (e.g., `color=Black&size=Medium`)

**Response** (200 OK):

```json
{
  "parentProduct": {
    "productId": "507f1f77bcf86cd799439011",
    "name": "Premium Cotton T-Shirt",
    "variationType": "parent",
    "variationTheme": "Color-Size",
    "variationAttributes": ["color", "size"]
  },
  "variations": [
    {
      "productId": "507f1f77bcf86cd799439021",
      "sku": "TS-BLK-001-S",
      "name": "Premium Cotton T-Shirt - Black Small",
      "price": 29.99,
      "attributes": {
        "color": "Black",
        "size": "Small"
      },
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-blk-s.jpg",
          "isPrimary": true
        }
      ],
      "availabilityStatus": {
        "status": "in-stock",
        "availableQuantity": 50
      }
    },
    {
      "productId": "507f1f77bcf86cd799439022",
      "sku": "TS-BLK-001-M",
      "name": "Premium Cotton T-Shirt - Black Medium",
      "price": 29.99,
      "attributes": {
        "color": "Black",
        "size": "Medium"
      },
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-blk-m.jpg",
          "isPrimary": true
        }
      ],
      "availabilityStatus": {
        "status": "in-stock",
        "availableQuantity": 75
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalVariations": 6,
    "totalPages": 1
  }
}
```

#### 3.2.18 Add Variation to Parent

**Endpoint**: `POST /api/products/{parentId}/variations`

**Description**: Add a new variation to an existing parent product

**Authentication**: Required (JWT)

**Authorization**: Admin role required

**Request Body**:

```json
{
  "sku": "TS-BLK-001-XL",
  "price": 31.99,
  "compareAtPrice": 39.99,
  "attributes": {
    "color": "Black",
    "size": "X-Large"
  },
  "images": [
    {
      "url": "https://cdn.aioutlet.com/products/ts-blk-xl.jpg",
      "alt": "Black t-shirt extra large",
      "isPrimary": true
    }
  ]
}
```

**Response** (201 Created):

```json
{
  "productId": "507f1f77bcf86cd799439024",
  "sku": "TS-BLK-001-XL",
  "parentId": "507f1f77bcf86cd799439011",
  "attributes": {
    "color": "Black",
    "size": "X-Large"
  },
  "price": 31.99,
  "createdAt": "2025-11-04T16:00:00Z",
  "message": "Variation added successfully"
}
```

---

### 3.3 Product Discovery APIs

#### 3.3.1 Search Products (Offset Pagination)

**Endpoint**: `GET /api/products/search`

**Description**: Search products with filtering, sorting, and offset-based pagination

**Authentication**: Optional (public endpoint for active products)

**Query Parameters**:

- `query` (optional): Search term (searches name, description, brand, tags)
- `department` (optional): Filter by department
- `category` (optional): Filter by category
- `subcategory` (optional): Filter by subcategory
- `productType` (optional): Filter by product type
- `brand` (optional): Filter by brand
- `minPrice` (optional): Minimum price filter
- `maxPrice` (optional): Maximum price filter
- `color` (optional): Filter by color
- `size` (optional): Filter by size
- `minRating` (optional): Minimum average rating (0-5)
- `availabilityStatus` (optional): Filter by availability (in-stock, low-stock, out-of-stock)
- `badges` (optional): Filter by badge types (comma-separated)
- `sortBy` (optional): Sort field (relevance, price, rating, newest, popular) - default: relevance
- `sortOrder` (optional): asc or desc - default: asc
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)

**Request Example**:

```http
GET /api/products/search?query=cotton&category=Clothing&minPrice=20&maxPrice=50&sortBy=price&sortOrder=asc&page=1&limit=20
```

**Response** (200 OK):

```json
{
  "products": [
    {
      "productId": "507f1f77bcf86cd799439011",
      "name": "Premium Cotton T-Shirt",
      "description": "Comfortable 100% cotton t-shirt with modern fit",
      "price": 29.99,
      "compareAtPrice": 39.99,
      "sku": "TS-BLK-001",
      "brand": "TrendyWear",
      "taxonomy": {
        "department": "Men",
        "category": "Clothing",
        "subcategory": "Tops",
        "productType": "T-Shirts"
      },
      "attributes": {
        "color": "Black",
        "size": "Medium",
        "material": "100% Cotton"
      },
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-001-front.jpg",
          "alt": "Front view",
          "isPrimary": true
        }
      ],
      "badges": [
        {
          "type": "best-seller",
          "label": "Best Seller",
          "priority": 1
        }
      ],
      "reviewAggregates": {
        "averageRating": 4.5,
        "totalReviewCount": 128
      },
      "availabilityStatus": {
        "status": "in-stock",
        "availableQuantity": 150
      }
    },
    {
      "productId": "507f1f77bcf86cd799439015",
      "name": "Organic Cotton Hoodie",
      "description": "Soft organic cotton hoodie with kangaroo pocket",
      "price": 49.99,
      "compareAtPrice": null,
      "sku": "HD-GRY-002",
      "brand": "EcoWear",
      "taxonomy": {
        "department": "Men",
        "category": "Clothing",
        "subcategory": "Tops",
        "productType": "Hoodies"
      },
      "attributes": {
        "color": "Grey",
        "size": "Large",
        "material": "100% Organic Cotton"
      },
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/hd-002-front.jpg",
          "alt": "Front view",
          "isPrimary": true
        }
      ],
      "badges": [
        {
          "type": "eco-friendly",
          "label": "Eco Friendly",
          "priority": 2
        }
      ],
      "reviewAggregates": {
        "averageRating": 4.7,
        "totalReviewCount": 89
      },
      "availabilityStatus": {
        "status": "in-stock",
        "availableQuantity": 45
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalResults": 47,
    "totalPages": 3
  },
  "facets": {
    "brands": [
      { "value": "TrendyWear", "count": 12 },
      { "value": "EcoWear", "count": 8 },
      { "value": "StyleCo", "count": 6 }
    ],
    "priceRanges": [
      { "min": 0, "max": 25, "count": 5 },
      { "min": 25, "max": 50, "count": 30 },
      { "min": 50, "max": 100, "count": 12 }
    ],
    "colors": [
      { "value": "Black", "count": 15 },
      { "value": "Grey", "count": 10 },
      { "value": "White", "count": 8 }
    ]
  },
  "appliedFilters": {
    "query": "cotton",
    "category": "Clothing",
    "minPrice": 20,
    "maxPrice": 50,
    "sortBy": "price",
    "sortOrder": "asc"
  }
}
```

#### 3.3.2 Search Products (Cursor Pagination)

**Endpoint**: `GET /api/products/search/cursor`

**Description**: Search products with cursor-based pagination (optimized for deep pagination)

**Authentication**: Optional

**Query Parameters**: Same as offset-based search, plus:

- `cursor` (optional): Cursor token from previous response

**Request Example**:

```http
GET /api/products/search/cursor?query=cotton&category=Clothing&cursor=eyJza3UiOiJUUy1CTEstMDAxIiwicHJpY2UiOjI5Ljk5fQ==
```

**Response** (200 OK):

```json
{
  "products": [
    {
      "productId": "507f1f77bcf86cd799439016",
      "name": "Cotton Blend Sweater",
      "price": 59.99,
      "sku": "SW-NAV-003"
    }
  ],
  "pagination": {
    "nextCursor": "eyJza3UiOiJTVy1OQVYtMDAzIiwicHJpY2UiOjU5Ljk5fQ==",
    "previousCursor": "eyJza3UiOiJUUy1CTEstMDAxIiwicHJpY2UiOjI5Ljk5fQ==",
    "hasMore": true,
    "limit": 20
  },
  "facets": {},
  "appliedFilters": {}
}
```

**Note**: Cursor pagination does not return `totalResults` or `totalPages` for performance optimization.

#### 3.3.3 Get Products by Category

**Endpoint**: `GET /api/products/category/{categoryPath}`

**Description**: Get products by hierarchical category path

**Authentication**: Optional

**Path Parameter**:

- `categoryPath`: Hierarchical category (e.g., `men/clothing/tops` or `women/shoes/sneakers`)

**Query Parameters**:

- `sortBy` (optional): Sort field (default: popularity)
- `sortOrder` (optional): asc or desc
- `page` (optional): Page number
- `limit` (optional): Items per page
- Additional filters (price, rating, brand, etc.)

**Request Example**:

```http
GET /api/products/category/men/clothing/tops?sortBy=price&sortOrder=asc&page=1&limit=20
```

**Response** (200 OK):

```json
{
  "categoryInfo": {
    "department": "Men",
    "category": "Clothing",
    "subcategory": "Tops",
    "totalProducts": 156
  },
  "products": [
    {
      "productId": "507f1f77bcf86cd799439011",
      "name": "Premium Cotton T-Shirt",
      "price": 29.99
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalResults": 156,
    "totalPages": 8
  },
  "facets": {}
}
```

#### 3.3.4 Autocomplete Product Search

**Endpoint**: `GET /api/products/autocomplete`

**Description**: Get product suggestions for autocomplete (optimized for speed)

**Authentication**: Optional

**Query Parameters**:

- `query` (required): Search term (minimum 2 characters)
- `limit` (optional): Number of suggestions (default: 10, max: 20)

**Request Example**:

```http
GET /api/products/autocomplete?query=cott&limit=10
```

**Response** (200 OK):

```json
{
  "suggestions": [
    {
      "text": "cotton t-shirt",
      "type": "product",
      "productId": "507f1f77bcf86cd799439011",
      "image": "https://cdn.aioutlet.com/products/ts-001-thumb.jpg",
      "price": 29.99
    },
    {
      "text": "cotton hoodie",
      "type": "product",
      "productId": "507f1f77bcf86cd799439015",
      "image": "https://cdn.aioutlet.com/products/hd-002-thumb.jpg",
      "price": 49.99
    },
    {
      "text": "cotton",
      "type": "category",
      "categoryPath": "clothing/cotton"
    },
    {
      "text": "100% cotton",
      "type": "attribute",
      "attributeType": "material"
    }
  ],
  "responseTime": "45ms"
}
```

#### 3.3.5 Get Trending Products

**Endpoint**: `GET /api/products/trending`

**Description**: Get currently trending products based on analytics

**Authentication**: Optional

**Query Parameters**:

- `category` (optional): Filter by category
- `limit` (optional): Number of products (default: 20, max: 100)
- `timeWindow` (optional): Time window for trending calculation (24h, 7d, 30d) - default: 24h

**Request Example**:

```http
GET /api/products/trending?category=Clothing&limit=10&timeWindow=7d
```

**Response** (200 OK):

```json
{
  "trendingProducts": [
    {
      "productId": "507f1f77bcf86cd799439011",
      "name": "Premium Cotton T-Shirt",
      "price": 29.99,
      "sku": "TS-BLK-001",
      "images": [
        {
          "url": "https://cdn.aioutlet.com/products/ts-001-front.jpg",
          "isPrimary": true
        }
      ],
      "badges": [
        {
          "type": "trending",
          "label": "Trending Now",
          "priority": 1
        }
      ],
      "trendingScore": 98.5,
      "viewCount7d": 15420,
      "salesCount7d": 342
    }
  ],
  "timeWindow": "7d",
  "generatedAt": "2025-11-04T18:00:00Z",
  "nextUpdate": "2025-11-04T19:00:00Z"
}
```

---

### 3.4 Admin APIs

**Admin-Only Operations**

All administrative operations require `role: admin` in the JWT token. These include:

- **Bulk Import Operations**: All `/api/products/bulk/*` endpoints (see Section 3.2.7-3.2.9, 3.2.14-3.2.16)
- **Badge Management**: Manual badge assignment and removal (see Section 3.2.10-3.2.12)
- **Product Deletion**: Soft-delete products (see Section 3.2.4)
- **SEO Metadata Updates**: Update SEO fields (see Section 3.2.13)
- **Variation Management**: Create product variations (see Section 3.2.9, 3.2.18)

**Admin Authorization Check**:

All admin endpoints validate the JWT token and verify the user has the `admin` role:

**Request Header**:

```http
Authorization: Bearer <jwt_token>
```

**JWT Payload** (must contain):

```json
{
  "sub": "admin-user-123",
  "role": "admin",
  "exp": 1730732400,
  "iat": 1730728800
}
```

**Authorization Error Response** (403 Forbidden):

```json
{
  "error": "FORBIDDEN",
  "message": "Admin role required for this operation",
  "correlationId": "req-abc-123",
  "timestamp": "2025-11-04T18:30:00Z"
}
```

**Audit Trail**

All admin operations are automatically logged in the audit system with:

- **Admin User ID**: Who performed the operation
- **Operation Type**: Action taken (CREATE, UPDATE, DELETE, BULK_IMPORT, BADGE_ASSIGN, etc.)
- **Timestamp**: When the operation occurred
- **Product ID(s)**: Affected products
- **Changes Made**: Before/after values for updates
- **Correlation ID**: Request tracking identifier
- **IP Address**: Source of the request
- **User Agent**: Client information

**Audit Log Example**:

```json
{
  "auditId": "audit-20251104-001",
  "userId": "admin-user-123",
  "userRole": "admin",
  "operation": "PRODUCT_UPDATE",
  "resource": "product",
  "resourceId": "507f1f77bcf86cd799439011",
  "changes": {
    "price": {
      "before": 29.99,
      "after": 24.99
    },
    "description": {
      "before": "Comfortable 100% cotton t-shirt",
      "after": "Comfortable 100% cotton t-shirt - NOW ON SALE!"
    }
  },
  "correlationId": "req-def-789",
  "ipAddress": "192.168.1.100",
  "userAgent": "Mozilla/5.0...",
  "timestamp": "2025-11-04T18:30:00Z",
  "status": "success"
}
```

---

### 3.5 Health Check APIs

#### 3.5.1 Liveness Probe

**Endpoint**: `GET /health`

**Description**: Kubernetes liveness probe - checks if the service process is running

**Authentication**: None (public endpoint)

**Response** (200 OK):

```json
{
  "status": "healthy",
  "service": "product-service",
  "timestamp": "2025-11-04T19:00:00Z",
  "uptime": "48h 23m 15s"
}
```

**Error Response** (503 Service Unavailable):

```json
{
  "status": "unhealthy",
  "service": "product-service",
  "timestamp": "2025-11-04T19:00:00Z",
  "error": "Service process not responding"
}
```

**Note**: This endpoint should always return quickly. Kubernetes will restart the pod if it fails multiple times.

#### 3.5.2 Readiness Probe

**Endpoint**: `GET /health/ready`

**Description**: Kubernetes readiness probe - checks if the service can accept traffic

**Authentication**: None (public endpoint)

**Response** (200 OK - Ready):

```json
{
  "status": "ready",
  "service": "product-service",
  "timestamp": "2025-11-04T19:00:00Z",
  "dependencies": {
    "mongodb": {
      "status": "connected",
      "responseTime": "5ms",
      "lastCheck": "2025-11-04T19:00:00Z"
    },
    "rabbitmq": {
      "status": "connected",
      "responseTime": "3ms",
      "lastCheck": "2025-11-04T19:00:00Z"
    },
    "dapr": {
      "status": "connected",
      "responseTime": "2ms",
      "lastCheck": "2025-11-04T19:00:00Z"
    }
  }
}
```

**Response** (503 Service Unavailable - Not Ready):

```json
{
  "status": "not-ready",
  "service": "product-service",
  "timestamp": "2025-11-04T19:00:00Z",
  "dependencies": {
    "mongodb": {
      "status": "disconnected",
      "error": "Connection timeout",
      "lastCheck": "2025-11-04T19:00:00Z"
    },
    "rabbitmq": {
      "status": "connected",
      "responseTime": "3ms",
      "lastCheck": "2025-11-04T19:00:00Z"
    },
    "dapr": {
      "status": "connected",
      "responseTime": "2ms",
      "lastCheck": "2025-11-04T19:00:00Z"
    }
  },
  "reason": "MongoDB connection unavailable"
}
```

**Response** (503 Service Unavailable - Degraded):

```json
{
  "status": "degraded",
  "service": "product-service",
  "timestamp": "2025-11-04T19:00:00Z",
  "dependencies": {
    "mongodb": {
      "status": "connected",
      "responseTime": "250ms",
      "warning": "Slow response time",
      "lastCheck": "2025-11-04T19:00:00Z"
    },
    "rabbitmq": {
      "status": "connected",
      "responseTime": "3ms",
      "lastCheck": "2025-11-04T19:00:00Z"
    },
    "dapr": {
      "status": "connected",
      "responseTime": "2ms",
      "lastCheck": "2025-11-04T19:00:00Z"
    }
  },
  "reason": "MongoDB response time exceeds threshold"
}
```

**Health Status Definitions**:

- **ready**: All dependencies healthy, service can accept traffic
- **not-ready**: One or more critical dependencies unavailable
- **degraded**: All dependencies connected but performance degraded

**Note**: Kubernetes will remove the pod from the service load balancer if readiness probe fails.

---

### 3.6 Error Code Catalog

This section provides a comprehensive catalog of all error codes returned by the Product Service APIs.

#### 3.6.1 Client Error Codes (4xx)

| Error Code                     | HTTP Status | Description                              | Scenario                                                             | Client Action                                                           |
| ------------------------------ | ----------- | ---------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `VALIDATION_ERROR`             | 400         | Request validation failed                | Missing required fields, invalid data types, format errors           | Review request body/params, check API documentation                     |
| `INVALID_SKU_FORMAT`           | 400         | SKU format is invalid                    | SKU contains invalid characters or doesn't match pattern             | Use alphanumeric characters, hyphens, underscores only                  |
| `INVALID_PRICE`                | 400         | Price value is invalid                   | Negative price, non-numeric value, exceeds maximum                   | Provide valid positive numeric price                                    |
| `INVALID_PAGINATION`           | 400         | Pagination parameters invalid            | Page/limit out of bounds, invalid cursor                             | Use valid page numbers (≥1) and limit (1-100)                           |
| `INVALID_SORT_FIELD`           | 400         | Sort field not supported                 | Unsupported sort field name                                          | Use supported sort fields: relevance, price, rating, newest, popular    |
| `INVALID_FILE_FORMAT`          | 400         | Uploaded file format not supported       | Wrong file type for bulk import/image upload                         | Use Excel (.xlsx) for imports, JPEG/PNG for images, ZIP for bulk images |
| `MISSING_REQUIRED_COLUMNS`     | 400         | Import template missing required columns | Excel template doesn't have mandatory columns                        | Download latest template, ensure all required columns present           |
| `INVALID_CATEGORY_PATH`        | 400         | Category path format is invalid          | Malformed category path                                              | Use format: department/category/subcategory                             |
| `INVALID_VARIATION_ATTRIBUTES` | 400         | Variation attributes don't match parent  | Child variation has different attributes than parent variation theme | Ensure variation attributes match parent's variationAttributes array    |
| `UNAUTHORIZED`                 | 401         | Authentication failed                    | Missing, expired, or invalid JWT token                               | Re-authenticate, obtain fresh token                                     |
| `TOKEN_EXPIRED`                | 401         | JWT token has expired                    | Token expiration time passed                                         | Re-authenticate with valid credentials                                  |
| `INVALID_TOKEN`                | 401         | JWT token is malformed or invalid        | Token signature invalid, tampered token                              | Re-authenticate, do not modify token                                    |
| `FORBIDDEN`                    | 403         | Insufficient permissions                 | User lacks required role (e.g., admin)                               | Contact admin for role upgrade or use authorized account                |
| `ADMIN_ROLE_REQUIRED`          | 403         | Admin role required                      | Attempting admin operation without admin role                        | Use admin account or contact administrator                              |
| `PRODUCT_NOT_FOUND`            | 404         | Product does not exist                   | Product ID doesn't exist in database                                 | Verify product ID, check if product was deleted                         |
| `BADGE_NOT_FOUND`              | 404         | Badge does not exist                     | Badge ID not found for product                                       | Verify badge ID, check if badge was removed                             |
| `JOB_NOT_FOUND`                | 404         | Bulk operation job not found             | Job ID doesn't exist or expired                                      | Verify job ID from import/upload response                               |
| `VARIATION_PARENT_NOT_FOUND`   | 404         | Parent product not found                 | Parent product ID for variation doesn't exist                        | Create parent product first or verify parent ID                         |
| `DUPLICATE_SKU`                | 409         | SKU already exists                       | Attempting to create/update product with existing SKU                | Use unique SKU or update existing product                               |
| `DUPLICATE_SLUG`               | 409         | SEO slug already exists                  | Attempting to use SEO slug already assigned                          | Use unique slug or modify to make it unique                             |
| `PRODUCT_HAS_VARIATIONS`       | 409         | Cannot delete product with variations    | Attempting to delete parent product with child variations            | Delete all child variations first                                       |
| `BADGE_ALREADY_ASSIGNED`       | 409         | Badge already assigned to product        | Attempting to assign duplicate badge                                 | Check existing badges before assignment                                 |
| `PAYLOAD_TOO_LARGE`            | 413         | Request payload exceeds size limit       | File upload exceeds maximum size (50MB for imports, 100MB for ZIP)   | Reduce file size, split into multiple batches                           |
| `TOO_MANY_REQUESTS`            | 429         | Rate limit exceeded                      | Too many requests in time window                                     | Implement exponential backoff, reduce request frequency                 |

#### 3.6.2 Server Error Codes (5xx)

| Error Code                   | HTTP Status | Description                     | Scenario                                              | Client Action                                               |
| ---------------------------- | ----------- | ------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------- |
| `INTERNAL_SERVER_ERROR`      | 500         | Unexpected server error         | Unhandled exception, programming error                | Retry with exponential backoff, contact support if persists |
| `DATABASE_ERROR`             | 500         | Database operation failed       | MongoDB connection lost, query timeout, write failure | Retry request, check service health status                  |
| `EVENT_PUBLISH_FAILED`       | 500         | Failed to publish event         | RabbitMQ unavailable, Dapr error                      | System will retry automatically, check system health        |
| `IMAGE_PROCESSING_FAILED`    | 500         | Image processing error          | Image upload/processing failed                        | Re-upload image, verify image format and size               |
| `BULK_IMPORT_FAILED`         | 500         | Bulk import job failed          | Critical error during import processing               | Check error report, contact support                         |
| `SERVICE_UNAVAILABLE`        | 503         | Service temporarily unavailable | Service starting up, dependencies unavailable         | Wait and retry, check /health/ready endpoint                |
| `DATABASE_UNAVAILABLE`       | 503         | Database not available          | MongoDB connection down                               | Wait for database recovery, check infrastructure            |
| `MESSAGE_BROKER_UNAVAILABLE` | 503         | Message broker not available    | RabbitMQ connection down                              | Wait for broker recovery, check infrastructure              |
| `GATEWAY_TIMEOUT`            | 504         | Request timeout                 | Operation took too long to complete                   | Retry with exponential backoff, check service performance   |

#### 3.6.3 Business Logic Error Codes

| Error Code                             | HTTP Status | Description                            | Scenario                                             | Client Action                                   |
| -------------------------------------- | ----------- | -------------------------------------- | ---------------------------------------------------- | ----------------------------------------------- |
| `PRODUCT_NOT_ACTIVE`                   | 400         | Product is not active                  | Attempting operation on draft/deleted product        | Activate product first or use admin credentials |
| `INVALID_PRICE_RANGE`                  | 400         | Price range is invalid                 | minPrice > maxPrice in search                        | Ensure minPrice ≤ maxPrice                      |
| `INVALID_RATING_RANGE`                 | 400         | Rating must be between 0-5             | Rating value out of bounds                           | Provide rating between 0 and 5                  |
| `PARENT_PRODUCT_REQUIRED`              | 400         | Operation requires parent product      | Attempting variation operation on non-parent product | Use parent product ID or create parent first    |
| `CHILD_PRODUCT_CANNOT_HAVE_VARIATIONS` | 400         | Child products cannot have variations  | Attempting to add variation to child product         | Only parent products can have variations        |
| `BADGE_EXPIRED`                        | 400         | Badge has expired                      | Attempting to assign expired badge                   | Update badge expiration or create new badge     |
| `MAX_VARIATIONS_EXCEEDED`              | 400         | Maximum variation count exceeded       | Attempting to create more than 1000 variations       | Split into multiple parent products             |
| `MAX_IMAGES_EXCEEDED`                  | 400         | Maximum image count exceeded           | Uploading more than 10 images per product            | Reduce number of images to 10 or less           |
| `SEARCH_QUERY_TOO_SHORT`               | 400         | Search query too short                 | Query less than 2 characters                         | Provide search query with at least 2 characters |
| `DEEP_PAGINATION_NOT_SUPPORTED`        | 400         | Offset pagination limited to 500 pages | Attempting to access page > 500                      | Use cursor-based pagination for deep pagination |

#### 3.6.4 Error Response Format

All error responses follow this standard format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error description",
  "details": {
    "field": "specific_field_name",
    "value": "invalid_value",
    "constraint": "validation_constraint"
  },
  "correlationId": "req-abc-123",
  "timestamp": "2025-11-04T19:30:00Z",
  "path": "/api/products",
  "method": "POST"
}
```

**Field Descriptions**:

- `error`: Machine-readable error code (from catalog above)
- `message`: Human-readable error message for developers
- `details`: Additional context about the error (optional)
- `correlationId`: Request tracking identifier
- `timestamp`: When the error occurred
- `path`: API endpoint path
- `method`: HTTP method

**Example Error Responses**:

**Validation Error**:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": {
    "field": "price",
    "value": "-10.00",
    "constraint": "must be positive"
  },
  "correlationId": "req-abc-123",
  "timestamp": "2025-11-04T19:30:00Z",
  "path": "/api/products",
  "method": "POST"
}
```

**Authorization Error**:

```json
{
  "error": "FORBIDDEN",
  "message": "Admin role required for this operation",
  "correlationId": "req-def-456",
  "timestamp": "2025-11-04T19:31:00Z",
  "path": "/api/products/bulk/import",
  "method": "POST"
}
```

**Resource Not Found**:

```json
{
  "error": "PRODUCT_NOT_FOUND",
  "message": "Product with ID '507f1f77bcf86cd799439999' does not exist",
  "details": {
    "productId": "507f1f77bcf86cd799439999"
  },
  "correlationId": "req-ghi-789",
  "timestamp": "2025-11-04T19:32:00Z",
  "path": "/api/products/507f1f77bcf86cd799439999",
  "method": "GET"
}
```

---

## 4. Functional Requirements

### 4.1 Product Management (CRUD Operations)

#### 4.1.1 Create Products

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

#### 4.1.2 Update Products

- System MUST allow updating any product field except the product ID
- System MUST track all changes in product history with:
  - Who made the change (user ID)
  - When the change was made (timestamp)
  - What fields were changed (before/after values)
- System MUST validate that price remains non-negative on updates

#### 4.1.3 Soft Delete Products

- System MUST support soft-deleting products (set is_active=false)
- System MUST retain all product data for audit purposes
- Deleted products MUST NOT appear in customer-facing searches or listings
- System MUST allow reactivating previously deleted products

#### 4.1.4 Prevent Duplicate SKUs

- System MUST enforce unique SKU constraint across all active products
- System MUST validate SKU uniqueness on product creation
- System MUST validate SKU uniqueness on product updates
- System MUST validate SKU uniqueness when reactivating deleted products

### 4.2 Product Discovery & Search

#### 4.2.1 Text Search

- System MUST support searching products by text across:
  - Product name
  - Product description
  - Tags
  - Brand name
- Search MUST be case-insensitive
- Search MUST support partial text matching
- Search MUST only return active products

#### 4.2.2 Hierarchical Filtering

- System MUST support filtering by department
- System MUST support filtering by category (within a department)
- System MUST support filtering by subcategory (within a category)
- Filters MUST work in combination (department + category + subcategory)

#### 4.2.3 Price Range Filtering

- System MUST support filtering by minimum price
- System MUST support filtering by maximum price
- System MUST support filtering by price range (min and max together)

#### 4.2.4 Tag-Based Filtering

- System MUST support filtering products by tags
- System MUST support matching any tag in a provided list

#### 4.2.5 Pagination & Large Dataset Handling

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

#### 4.2.6 Trending Products

- System MUST provide an endpoint to retrieve recently added products
- Default limit MUST be 4 products
- NOTE: Full trending logic (incorporating ratings, reviews, sales) MUST be implemented in Web BFF by aggregating data from Product Service and Review Service

#### 4.2.7 Top Categories

- System MUST provide an endpoint to retrieve top categories by product count
- Default limit MUST be 5 categories
- System MUST return category metadata including product count and featured product
- NOTE: Full trending logic (incorporating ratings, reviews) MUST be implemented in Web BFF

### 4.3 Data Consistency & Validation

#### 4.3.1 Price Validation

- Product price MUST be non-negative (>= 0)
- System MUST validate price on create and update operations

#### 4.3.2 Required Field Validation

- System MUST validate that all required fields are provided on creation
- System MUST return clear error messages for validation failures

#### 4.3.3 SKU Format Validation

- System MUST validate SKU format if business rules are defined
- System MUST accept alphanumeric SKUs

#### 4.3.4 Data Persistence

- All product operations (create, update, delete) MUST be immediately consistent
- Product reads MUST always return the most recent data

### 4.4 Administrative Features

This section consolidates all administrative operations for catalog management, including bulk operations, manual badge assignment, size chart management, and compliance configuration.

#### 4.4.1 Product Statistics & Reporting

- System MUST provide an endpoint returning:
  - Total products count
  - Active products count
  - Inactive products count
- NOTE: Stock-related statistics (low stock, out of stock) are managed by Inventory Service
- System MUST maintain complete history of all product changes
- History MUST include timestamp, user, and changed fields
- History MUST be retrievable via API

#### 4.4.2 Bulk Product Operations

See also REQ-3.2.5 for background worker implementation details.

##### 4.4.2.1 Template Download

- System MUST provide downloadable Excel template for bulk product import
- Templates MUST be category-specific (e.g., "Clothing Template", "Electronics Template")
- Template MUST include:
  - All required and optional fields with descriptions
  - Field validation rules and constraints
  - Example rows with sample data
  - Column headers matching product attributes
- Template MUST support product variation import (parent-child relationships)
- System MUST provide template version control for backward compatibility

##### 4.4.2.2 Bulk Product Import

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

##### 4.4.2.3 Image Handling for Bulk Import

- System MUST support two image upload methods:
  - **Method 1**: Image URLs in import file (direct CDN links)
  - **Method 2**: Separate bulk image upload via ZIP file
- For ZIP upload, system MUST match filenames to SKUs automatically: `{SKU}-{sequence}.{ext}`
- System MUST validate image formats (JPEG, PNG, WebP), sizes (max 10MB), and count (max 10 per product)

##### 4.4.2.4 Import Status Tracking

- Admin MUST be able to view import job history with:
  - Job ID, status, filename, timestamps, row counts, user info
- System MUST provide downloadable error reports for failed imports
- System MUST allow retrying failed imports
- Import history MUST be preserved for 90+ days for audit

##### 4.4.2.5 Bulk Update Operations

- System MUST support bulk price/attribute updates via Excel
- System MUST support bulk status changes (activate/deactivate)
- Bulk updates MUST follow same validation as bulk import
- System MUST publish events for each updated product

#### 4.4.3 Badge Management

**Note**: Automated badge assignment via analytics is covered in REQ-3.2.3

##### 4.4.3.1 Manual Badge Assignment

- Admin MUST be able to manually assign/remove badges
- Admin MUST be able to set badge expiration dates
- Admin MUST be able to override auto-assigned badges
- System MUST allow bulk badge assignment
- System MUST maintain badge history
- Badge operations MUST NOT trigger product.updated events (use badge-specific events)

##### 4.4.3.2 Badge Types & Properties

Supported badge types: Best Seller (auto), New Arrival (auto), Limited Time Deal (manual), Featured (manual), Trending (auto), Exclusive (manual), Low Stock (auto), Back in Stock (auto), Pre-Order (manual), Clearance (manual), Eco-Friendly (manual), Custom (manual)

Each badge MUST have:

- Type, display text, style, priority, validity period, visibility rules, scope, source (manual/auto)

##### 4.4.3.3 Badge Monitoring

- Admin MUST be able to view all products with specific badge
- Admin MUST be able to view auto-assignment criteria
- Admin MUST receive alerts when badges expire

#### 4.4.4 Size Chart Management

##### 4.4.4.1 Size Chart Creation & Assignment

- Admin MUST be able to create/update size charts per category
- Size charts MUST support multiple formats: Image (PNG, JPG), PDF, Structured JSON
- Size charts MUST support regional sizing: US, EU, UK, Asian
- Size charts MUST be reusable across categories
- Product variations MUST reference parent's size chart
- Product API MUST include size chart reference

##### 4.4.4.2 Size Chart Templates

- System SHOULD provide standard templates for common categories
- Admin MUST be able to customize templates
- System MUST version control size charts

#### 4.4.5 Product Restrictions & Compliance

##### 4.4.5.1 Age Restrictions

- Admin MUST be able to set age restrictions: None, 18+, 21+, Custom
- Age-restricted products MUST be filtered if user age unknown
- Product API MUST return age restriction

##### 4.4.5.2 Shipping Restrictions

- Admin MUST be able to configure: Hazmat, Oversized, Perishable, International restricted, Regional restricted, Ground only
- Restrictions MUST be exposed to Order Service
- Products MUST display shipping limitation messages

##### 4.4.5.3 Regional Availability

- Admin MUST be able to configure: Available countries, states/provinces, regions
- Products MUST be filtered by customer location
- Regional availability MUST integrate with shipping restrictions

##### 4.4.5.4 Compliance Metadata

- Admin MUST be able to add: Certifications, safety warnings, ingredient disclosures, country of origin, warranty
- Compliance data MUST be searchable and displayed on product pages
- System MUST validate required compliance fields by category

#### 4.4.6 Admin Permissions & Audit

- All admin operations MUST require admin role
- System MUST validate permissions before operations
- All admin operations MUST be logged with: user ID, operation type, timestamp, IP, changed data
- Audit logs MUST be immutable and retrievable for compliance

### 4.5 Product Variations

#### 4.5.1 Variation Structure

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

#### 4.5.2 Variation Attributes

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

#### 4.5.3 Variation Inheritance

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

#### 4.5.4 Variation Display and Selection

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

#### 4.5.5 Variation Management

- Admin MUST be able to create parent product with variations in single operation
- Admin MUST be able to add new variations to existing parent
- Admin MUST be able to update variation attributes
- Admin MUST be able to remove variations (soft delete)
- System MUST validate variation uniqueness (no duplicate color-size combinations)
- Bulk import MUST support parent-child relationship specification

### 4.6 Enhanced Product Attributes

#### 4.6.1 Structured Attribute Schema

- System MUST support category-specific attribute schemas
- Each category MUST define:
  - Required attributes
  - Optional attributes
  - Attribute data types (string, number, boolean, list, object)
  - Validation rules (min/max, allowed values, regex patterns)
- System MUST validate product attributes against category schema on create/update
- System MUST provide API to retrieve category attribute schema

#### 4.6.2 Common Attribute Categories

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

#### 4.6.3 Category-Specific Attributes

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

#### 4.6.4 Attribute-Based Search and Filtering

- System MUST support filtering products by any defined attribute
- System MUST support multi-select attribute filtering (e.g., multiple colors, multiple sizes)
- System MUST provide faceted search results showing:
  - Available attribute values
  - Count of products for each attribute value
  - Applied filters
- System MUST support attribute-based sorting
- Attribute filters MUST work in combination with text search and category filters

#### 4.6.5 Attribute Validation

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

---

## 5. Non-Functional Requirements

### 5.1 Performance

#### 5.1.1 API Response Times

- Read operations (get, list, search) MUST respond within 200ms (p95)
- Write operations (create, update, delete) MUST respond within 500ms (p95)
- Event publishing MUST NOT add more than 50ms to API response time

#### 5.1.2 Throughput

- System MUST handle 1,000 requests per second during normal load
- System MUST handle 5,000 requests per second during peak load (sales events)

#### 5.1.3 Database Performance

- Product searches MUST be optimized with database indexes
- Text search MUST use database text indexes where available
- Pagination queries MUST be optimized to avoid full table scans

### 5.2 Scalability

#### 5.2.1 Service Uptime

- System MUST maintain 99.9% uptime
- Planned maintenance windows MUST be communicated in advance

#### 5.2.2 Event Publishing Resilience

- Event publishing failures MUST NOT cause product operations to fail
- Failed event publishes MUST be retried automatically (handled by messaging infrastructure)
- All event publishing attempts MUST be logged

#### 5.2.3 Database Resilience

- System MUST handle temporary database connection failures gracefully
- System MUST return 503 Service Unavailable on database connection errors
- Database connection pool MUST be configured for resilience

### 5.3 Availability

#### 5.3.1 Horizontal Scaling

- Service MUST be stateless to support horizontal scaling
- Multiple instances MUST be able to run concurrently
- No instance-specific state MUST be maintained

#### 5.3.2 Data Growth

- System MUST efficiently handle 1 million+ products
- Performance MUST NOT degrade significantly with catalog growth
- Database indexes MUST be optimized for large datasets

### 5.4 Security

#### 5.4.1 Authentication

- All API endpoints MUST validate JWT tokens
- Invalid or expired tokens MUST result in 401 Unauthorized

#### 5.4.2 Authorization

- Admin operations MUST verify admin role from JWT token
- Non-admin users MUST receive 403 Forbidden for admin operations

#### 5.4.3 Input Validation

- All user inputs MUST be validated and sanitized
- SQL injection and NoSQL injection MUST be prevented
- Product ID validation MUST prevent injection attacks

#### 5.4.4 Role-Based Access Control (RBAC)

##### 5.4.4.1 Roles

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

##### 5.4.4.2 Permission Matrix

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

##### 5.4.4.3 Implementation Requirements

- JWT token MUST include `role` claim (either "customer" or "admin")
- Authorization middleware MUST check role before granting access
- API responses MUST return 403 Forbidden for insufficient permissions
- All admin endpoints MUST log user ID and action for audit trail
- Unauthenticated requests default to "customer" role (read-only public access)

#### 5.4.5 Secrets Management

##### 5.4.5.1 Sensitive Data

Product Service handles the following sensitive configuration:

- **Database Credentials**: MongoDB connection string (username, password, host, port)
- **JWT Signing Keys**: Public keys for JWT token verification
- **Message Broker Credentials**: RabbitMQ/Event broker authentication
- **External API Keys**: Third-party service integrations (if any)

##### 5.4.5.2 Requirements

- Secrets MUST NOT be stored in source code or committed to version control
- Secrets MUST be injected at runtime via environment variables or secrets management service
- Database connection strings MUST use secure protocols (TLS/SSL)
- Secrets MUST be rotated periodically (recommended: every 90 days)
- Logging MUST NOT expose secrets (mask credentials in logs)
- Error messages MUST NOT leak sensitive configuration details

##### 5.4.5.3 Recommended Implementation

- Use Azure Key Vault, AWS Secrets Manager, or HashiCorp Vault for secret storage
- Mount secrets as environment variables in container/pod configuration
- Use Kubernetes Secrets or Docker Secrets for orchestration environments
- Implement secret rotation without service downtime

### 5.5 Data Privacy

#### 5.5.1 Data Classification

- Product data is non-PII and not subject to GDPR
- Product images and descriptions are considered public data
- Admin user actions are logged for audit purposes

#### 5.5.2 Data Retention

- Soft-deleted products retained for 30 days before purging
- Audit logs retained for 1 year minimum
- Event logs retained per organizational policy

### 5.6 Observability

#### 5.6.1 Distributed Tracing

- All incoming requests MUST generate or propagate correlation IDs
- All outgoing calls (database, events) MUST include correlation IDs
- System MUST support distributed tracing across service boundaries

#### 5.6.2 Logging

##### 5.6.2.1 General Logging Requirements

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

##### 5.6.2.2 Correlation ID Requirements

- Service MUST check for `X-Correlation-ID` header on incoming requests
- If header exists, use the provided correlation ID
- If header is missing, generate a new UUID v4 correlation ID
- Correlation ID MUST be included in:
  - All log entries for that request
  - All outgoing HTTP calls (as `X-Correlation-ID` header)
  - All published events (in event metadata)
  - All database query logs
  - Response headers (echo back to caller)

##### 5.6.2.3 Structured Logging Format

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

##### 5.6.2.4 Logging Levels

- **DEBUG**: Detailed diagnostic information (disabled in production)
- **INFO**: Business operations, successful operations
- **WARNING**: Validation failures, retryable errors, deprecated API usage
- **ERROR**: System errors, failed operations, exceptions

##### 5.6.2.5 Sensitive Data Handling

**What NOT to Log:**

- Passwords, API keys, or secrets
- Complete JWT tokens (log only user ID from token)
- Credit card numbers or PII
- Full database connection strings

##### 5.6.2.6 Environment-Specific Logging Behavior

System MUST implement different logging strategies based on environment:

**Development Environment (DEV):**

- Log level: DEBUG enabled
- Stack traces: Full stack traces included in error logs
- Request/Response logging: Log complete request bodies and response payloads
- Database queries: Log full SQL/NoSQL queries with parameters
- Performance metrics: Detailed timing for each operation
- Correlation tracing: Verbose trace logging for debugging
- Sensitive data: Masked but more verbose than production
- Log retention: 7 days (shorter for cost optimization)
- Log destination: Local files + Console output

**Staging Environment (STAGING):**

- Log level: INFO (WARNING for high-traffic endpoints)
- Stack traces: Summarized stack traces (top 5 frames)
- Request/Response logging: Log request/response metadata only (no bodies)
- Database queries: Log query type and execution time (no parameters)
- Performance metrics: Standard p50, p95, p99 metrics
- Correlation tracing: Standard correlation ID tracking
- Sensitive data: Fully masked
- Log retention: 30 days
- Log destination: Centralized logging system (e.g., Azure Log Analytics, ELK)

**Production Environment (PROD):**

- Log level: INFO (WARNING for high-traffic endpoints, ERROR for critical paths)
- Stack traces: Error message + correlation ID only (no stack trace in logs)
  - Full stack traces sent to error tracking system (e.g., Sentry, Application Insights)
- Request/Response logging: Metadata only (endpoint, method, status, duration)
  - NO request/response bodies logged
- Database queries: Execution time only (no query details)
- Performance metrics: Aggregated metrics only
- Correlation tracing: Correlation ID + minimal context
- Sensitive data: Fully masked/redacted
- Log retention: 90 days (compliance requirement)
- Log destination: Centralized logging + long-term archival

**Configuration:**

- Environment detection via `NODE_ENV` or `ENVIRONMENT` variable
- Log level configurable via environment variable: `LOG_LEVEL`
- Override mechanism for temporary debugging: `DEBUG_MODE=true` (max 1 hour, auto-expires)

**Security Considerations:**

- Production logs MUST NOT contain:
  - Full JWT tokens
  - Database credentials
  - API keys or secrets
  - User passwords (even hashed)
  - Credit card numbers
  - PII beyond user IDs
  - Complete stack traces (use error tracking service instead)

#### 5.6.3 Metrics

##### 5.6.3.1 General Metrics Requirements

- System MUST expose health check endpoints
- System MUST expose metrics for monitoring
- Metrics MUST be exposed in Prometheus format
- Metrics endpoint: `/metrics` (accessible without authentication for scraping)

##### 5.6.3.2 Request Metrics

- Request count by endpoint and HTTP method
- Request latency by endpoint (p50, p95, p99)
- Error count by type (4xx, 5xx)
- Request rate (requests per second)

##### 5.6.3.3 Database Metrics

- Query performance (execution time)
- Connection pool utilization
- Query error rate
- Document read/write counts

##### 5.6.3.4 Event Metrics

- Events published (count by event type)
- Events consumed (count by event type)
- Event processing latency
- Event consumer lag
- Dead letter queue depth

##### 5.6.3.5 Business Metrics

- Product CRUD operations (count by operation type)
- Bulk import job success/failure rate
- Badge assignment/removal counts
- Search query performance

##### 5.6.3.6 Alerting Thresholds

System SHOULD implement the following alerting thresholds:

- Error rate > 5% for 5 minutes → Alert
- P95 latency > 500ms for 5 minutes → Alert
- Event consumer lag > 1000 messages → Alert
- Database connection pool exhausted → Critical Alert
- Health check failures for 2 minutes → Critical Alert

#### 5.6.4 Health Checks

- System MUST provide /health endpoint for liveness checks
- System MUST provide /health/ready endpoint for readiness checks
- Health check MUST verify database connectivity

### 5.7 Error Handling

#### 5.7.1 Error Response Format

##### 5.7.1.1 General Requirements

- All errors MUST return appropriate HTTP status codes (4xx, 5xx)
- Error responses MUST include correlation ID for traceability
- Error messages MUST be clear and actionable for API consumers

##### 5.7.1.2 Structured Error Response Example

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Product validation failed",
    "timestamp": "2025-11-03T14:32:10.123Z",
    "correlationId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "path": "/api/products",
    "method": "POST",
    "statusCode": 400,
    "details": [
      {
        "field": "price",
        "message": "Price must be greater than or equal to 0",
        "value": -10.99
      },
      {
        "field": "sku",
        "message": "SKU already exists",
        "value": "TS-BLK-001"
      }
    ],
    "documentation": "https://docs.aioutlet.com/api/errors#validation-error"
  }
}
```

##### 5.7.1.3 Error Response Structure

- `code`: Machine-readable error code (VALIDATION_ERROR, PRODUCT_NOT_FOUND, etc.)
- `message`: Human-readable error description
- `timestamp`: ISO 8601 timestamp when error occurred
- `correlationId`: Request correlation ID for tracing across services
- `path`: API endpoint where error occurred
- `method`: HTTP method (GET, POST, PUT, DELETE)
- `statusCode`: HTTP status code (400, 404, 500, etc.)
- `details`: Array of specific validation errors (for validation failures)
- `documentation`: Link to error documentation (optional)

#### 5.7.2 Error Logging

- All errors MUST be logged with full context (stack trace, input data)
- Error logs MUST include correlation ID for debugging
- Critical errors MUST trigger alerts

#### 5.7.3 Resilience

- Event publishing failures MUST NOT cause product operations to fail
- Database connection failures MUST return 503 Service Unavailable
- System MUST implement retry logic with exponential backoff

---

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

## 6. Dependencies

### 6.1 External Services

- **Review Service**: Provides aggregated review data (ratings, count)
- **Inventory Service**: Provides stock availability data
- **Analytics Service**: Provides view/sales metrics
- **User Service**: Provides user authentication and authorization
- **Message Broker**: RabbitMQ for event-driven communication

### 6.2 Infrastructure

- **MongoDB**: Primary database
- **Docker**: Containerization
- **Kubernetes**: Container orchestration

### 6.3 Development Dependencies

- **Python 3.11+**: Runtime environment
- **FastAPI**: Web framework
- **Pytest**: Testing framework

---

## 7. Testing Strategy

### 7.1 Unit Testing

- Controller/route testing
- Service layer business logic
- Data model validation

### 7.2 Integration Testing

- Database integration tests
- Message broker integration tests
- External service mocks

### 7.3 E2E Testing

- Full API workflow tests
- Event publication and consumption

### 7.4 Performance Testing

- Load testing at 1,000 req/s
- Response time validation (< 200ms p95)

### 7.5 Security Testing

- Authentication and authorization
- Input validation and sanitization

---

## 8. Deployment

### 8.1 Environment Configuration

- Development, Staging, Production environments
- Environment-specific configuration

### 8.2 Docker Configuration

- Multi-stage Docker builds
- Container optimization

### 8.3 Kubernetes Deployment

- Deployment manifests
- Service definitions
- ConfigMaps and Secrets

### 8.4 CI/CD Pipeline

- Automated testing
- Container image building
- Deployment automation

---

## 9. Monitoring & Alerts

### 9.1 Metrics

- Request rate and latency
- Error rates
- Database performance
- Event processing metrics

### 9.2 Alerts

- High error rate alerts
- Performance degradation alerts
- Service availability alerts

### 9.3 Dashboards

- Service health dashboard
- API performance metrics
- Business metrics

---

## 10. Risks & Mitigations

| Risk                       | Impact   | Probability | Mitigation                                        |
| -------------------------- | -------- | ----------- | ------------------------------------------------- |
| MongoDB downtime           | High     | Low         | Replica set, automated failover                   |
| Message broker unavailable | Medium   | Low         | Circuit breaker, retry logic                      |
| Performance degradation    | High     | Medium      | Caching, database indexing, horizontal scaling    |
| Data inconsistency         | Medium   | Medium      | Event-driven eventual consistency, reconciliation |
| Security breach            | Critical | Low         | Security audits, penetration testing, monitoring  |

---

## 11. Compliance & Legal

### 11.1 Data Protection Regulations

- Product data is non-PII and not subject to GDPR
- Audit logs for compliance tracking
- Data retention policies

---

## 12. Documentation References

### 12.1 Developer Documentation

- [README.md](../README.md) - Getting started guide
- [API.md](API.md) - API reference (to be created)
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture (to be created)

### 12.2 Runbooks

- [Deployment Runbook](runbooks/deployment.md) - Deployment procedures (to be created)
- [Incident Response](runbooks/incident-response.md) - Incident handling (to be created)

### 12.3 API Documentation

- OpenAPI/Swagger documentation
- Postman collections

---

## 13. Approval & Sign-off

| Role                | Name | Date | Signature |
| ------------------- | ---- | ---- | --------- |
| Product Owner       | TBD  | TBD  | TBD       |
| Engineering Lead    | TBD  | TBD  | TBD       |
| Architecture Review | TBD  | TBD  | TBD       |
| Security Review     | TBD  | TBD  | TBD       |

---

## 14. Revision History

| Version | Date       | Author | Changes              |
| ------- | ---------- | ------ | -------------------- |
| 1.0     | 2025-11-03 | Team   | Initial PRD creation |

---

## 15. Appendix

### 15.1 Glossary

- **SKU**: Stock Keeping Unit - Unique product identifier
- **Variation**: Product variant (e.g., different size/color of same product)
- **Badge**: Product label (e.g., "New", "Sale", "Trending")
- **Taxonomy**: Category hierarchy for product organization

### 15.2 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Best Practices](https://docs.mongodb.com/manual/)
- [Event-Driven Architecture Patterns](https://martinfowler.com/articles/201701-event-driven.html)

---

**NOTE**: This PRD describes **WHAT** the Product Service must do from a business perspective. Technical implementation decisions (database technology, messaging framework, programming language, etc.) are documented separately in technical design documents and Copilot instructions.
