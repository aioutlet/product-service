-- Product Service Schema
-- Handles products, categories, reviews, and vendor management

CREATE SCHEMA IF NOT EXISTS products;

-- Product categories
CREATE TABLE IF NOT EXISTS products.categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID,
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES products.categories(id) ON DELETE SET NULL
);

-- Vendors/Brands
CREATE TABLE IF NOT EXISTS products.vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    website_url VARCHAR(500),
    logo_url VARCHAR(500),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    address JSONB,
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    total_products INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main products table
CREATE TABLE IF NOT EXISTS products.products (
    id VARCHAR(24) PRIMARY KEY, -- MongoDB-style ObjectId for cross-service compatibility
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    short_description TEXT,
    sku VARCHAR(100) UNIQUE,
    barcode VARCHAR(100),
    category_id UUID,
    vendor_id UUID,
    price DECIMAL(10, 2) NOT NULL,
    compare_price DECIMAL(10, 2), -- Original price for discounts
    cost_price DECIMAL(10, 2), -- For vendor cost tracking
    currency VARCHAR(3) DEFAULT 'USD',
    weight DECIMAL(8, 3), -- in kg
    dimensions JSONB, -- {length, width, height, unit}
    images TEXT[], -- Array of image URLs
    tags TEXT[], -- Product tags for search
    status VARCHAR(20) DEFAULT 'active', -- active, inactive, archived
    visibility VARCHAR(20) DEFAULT 'public', -- public, private, hidden
    featured BOOLEAN DEFAULT FALSE,
    digital BOOLEAN DEFAULT FALSE, -- Is it a digital product?
    downloadable BOOLEAN DEFAULT FALSE,
    track_inventory BOOLEAN DEFAULT TRUE,
    allow_backorders BOOLEAN DEFAULT FALSE,
    requires_shipping BOOLEAN DEFAULT TRUE,
    tax_class VARCHAR(50) DEFAULT 'standard',
    meta_title VARCHAR(255),
    meta_description TEXT,
    meta_keywords TEXT[],
    rating DECIMAL(3, 2) DEFAULT 0.00,
    rating_count INTEGER DEFAULT 0,
    total_sales INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES products.categories(id) ON DELETE SET NULL,
    FOREIGN KEY (vendor_id) REFERENCES products.vendors(id) ON DELETE SET NULL
);

-- Product variants (for different sizes, colors, etc.)
CREATE TABLE IF NOT EXISTS products.product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(24) NOT NULL,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    price DECIMAL(10, 2),
    compare_price DECIMAL(10, 2),
    weight DECIMAL(8, 3),
    dimensions JSONB,
    image_url VARCHAR(500),
    attributes JSONB, -- {color: "red", size: "L", etc.}
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products.products(id) ON DELETE CASCADE
);

-- Product attributes (for filtering and variants)
CREATE TABLE IF NOT EXISTS products.attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- text, number, select, multiselect, boolean
    is_required BOOLEAN DEFAULT FALSE,
    is_variant BOOLEAN DEFAULT FALSE, -- Used for variants
    is_filterable BOOLEAN DEFAULT TRUE, -- Used for search filters
    sort_order INTEGER DEFAULT 0,
    options JSONB, -- For select/multiselect types
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product attribute values
CREATE TABLE IF NOT EXISTS products.product_attributes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(24) NOT NULL,
    attribute_id UUID NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products.products(id) ON DELETE CASCADE,
    FOREIGN KEY (attribute_id) REFERENCES products.attributes(id) ON DELETE CASCADE,
    UNIQUE(product_id, attribute_id)
);

-- Product reviews
CREATE TABLE IF NOT EXISTS products.reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(24) NOT NULL,
    user_id UUID NOT NULL, -- Reference to user service
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    content TEXT,
    images TEXT[], -- Review images
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT TRUE,
    helpful_count INTEGER DEFAULT 0,
    total_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products.products(id) ON DELETE CASCADE
);

-- Review helpfulness votes
CREATE TABLE IF NOT EXISTS products.review_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    user_id UUID NOT NULL,
    is_helpful BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES products.reviews(id) ON DELETE CASCADE,
    UNIQUE(review_id, user_id)
);

-- Product collections/bundles
CREATE TABLE IF NOT EXISTS products.collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    type VARCHAR(50) DEFAULT 'manual', -- manual, automatic, smart
    conditions JSONB, -- For automatic collections
    image_url VARCHAR(500),
    is_published BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products in collections
CREATE TABLE IF NOT EXISTS products.collection_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID NOT NULL,
    product_id VARCHAR(24) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (collection_id) REFERENCES products.collections(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products.products(id) ON DELETE CASCADE,
    UNIQUE(collection_id, product_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON products.categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON products.categories(slug);
CREATE INDEX IF NOT EXISTS idx_vendors_slug ON products.vendors(slug);
CREATE INDEX IF NOT EXISTS idx_vendors_active ON products.vendors(is_active);
CREATE INDEX IF NOT EXISTS idx_products_slug ON products.products(slug);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products.products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products.products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_vendor_id ON products.products(vendor_id);
CREATE INDEX IF NOT EXISTS idx_products_status ON products.products(status);
CREATE INDEX IF NOT EXISTS idx_products_featured ON products.products(featured);
CREATE INDEX IF NOT EXISTS idx_products_price ON products.products(price);
CREATE INDEX IF NOT EXISTS idx_products_rating ON products.products(rating);
CREATE INDEX IF NOT EXISTS idx_variants_product_id ON products.product_variants(product_id);
CREATE INDEX IF NOT EXISTS idx_variants_sku ON products.product_variants(sku);
CREATE INDEX IF NOT EXISTS idx_attributes_slug ON products.attributes(slug);
CREATE INDEX IF NOT EXISTS idx_product_attributes_product_id ON products.product_attributes(product_id);
CREATE INDEX IF NOT EXISTS idx_product_attributes_attribute_id ON products.product_attributes(attribute_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON products.reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON products.reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON products.reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_approved ON products.reviews(is_approved);
CREATE INDEX IF NOT EXISTS idx_collection_products_collection_id ON products.collection_products(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_products_product_id ON products.collection_products(product_id);
