"""
Standard Attribute Schemas

Defines predefined attribute schemas for common product categories.
"""

from typing import Dict
from src.models.attribute_schema import (
    AttributeDefinition,
    AttributeGroup,
    CategorySchema,
    AttributeDataType,
    AttributeUnit,
    AttributeCategory
)


class StandardSchemas:
    """Factory for creating standard attribute schemas"""
    
    @staticmethod
    def get_physical_dimensions_group() -> AttributeGroup:
        """Physical dimensions attribute group (common to all categories)"""
        return AttributeGroup(
            name="physical_dimensions",
            display_name="Physical Dimensions",
            category=AttributeCategory.PHYSICAL_DIMENSIONS,
            description="Product physical measurements",
            order=1,
            attributes=[
                AttributeDefinition(
                    name="length",
                    display_name="Length",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.INCHES,
                    required=False,
                    min_value=0,
                    max_value=10000,
                    description="Product length",
                    example_value=24.0
                ),
                AttributeDefinition(
                    name="width",
                    display_name="Width",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.INCHES,
                    required=False,
                    min_value=0,
                    max_value=10000,
                    description="Product width",
                    example_value=18.0
                ),
                AttributeDefinition(
                    name="height",
                    display_name="Height",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.INCHES,
                    required=False,
                    min_value=0,
                    max_value=10000,
                    description="Product height",
                    example_value=2.0
                ),
                AttributeDefinition(
                    name="weight",
                    display_name="Weight",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.POUNDS,
                    required=False,
                    min_value=0,
                    max_value=50000,
                    description="Product weight",
                    example_value=5.5
                ),
                AttributeDefinition(
                    name="volume",
                    display_name="Volume",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.LITERS,
                    required=False,
                    min_value=0,
                    description="Product volume",
                    example_value=10.5
                )
            ]
        )
    
    @staticmethod
    def get_materials_group() -> AttributeGroup:
        """Materials and composition attribute group"""
        return AttributeGroup(
            name="materials_composition",
            display_name="Materials & Composition",
            category=AttributeCategory.MATERIALS_COMPOSITION,
            description="Product materials and composition",
            order=2,
            attributes=[
                AttributeDefinition(
                    name="primary_material",
                    display_name="Primary Material",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=100,
                    description="Main material used",
                    example_value="Cotton"
                ),
                AttributeDefinition(
                    name="secondary_materials",
                    display_name="Secondary Materials",
                    data_type=AttributeDataType.LIST,
                    required=False,
                    description="Additional materials used",
                    example_value=["Spandex", "Polyester"]
                ),
                AttributeDefinition(
                    name="certifications",
                    display_name="Certifications",
                    data_type=AttributeDataType.LIST,
                    required=False,
                    description="Material certifications (organic, fair-trade, etc.)",
                    example_value=["GOTS Certified Organic", "Fair Trade"]
                ),
                AttributeDefinition(
                    name="recycled_content_percentage",
                    display_name="Recycled Content %",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.PERCENTAGE,
                    required=False,
                    min_value=0,
                    max_value=100,
                    description="Percentage of recycled materials",
                    example_value=50
                )
            ]
        )
    
    @staticmethod
    def get_care_instructions_group() -> AttributeGroup:
        """Care instructions attribute group"""
        return AttributeGroup(
            name="care_instructions",
            display_name="Care Instructions",
            category=AttributeCategory.CARE_INSTRUCTIONS,
            description="Product care and maintenance instructions",
            order=3,
            attributes=[
                AttributeDefinition(
                    name="washing",
                    display_name="Washing Instructions",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Machine Wash Cold", "Machine Wash Warm", "Hand Wash Only", "Dry Clean Only", "Do Not Wash"],
                    description="How to wash the product",
                    example_value="Machine Wash Cold"
                ),
                AttributeDefinition(
                    name="drying",
                    display_name="Drying Instructions",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Tumble Dry Low", "Tumble Dry Medium", "Air Dry", "Hang Dry", "Dry Flat", "Do Not Tumble Dry"],
                    description="How to dry the product",
                    example_value="Tumble Dry Low"
                ),
                AttributeDefinition(
                    name="ironing",
                    display_name="Ironing Instructions",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Low Heat", "Medium Heat", "High Heat", "Steam Iron", "Do Not Iron"],
                    description="Ironing instructions",
                    example_value="Low Heat"
                ),
                AttributeDefinition(
                    name="special_care",
                    display_name="Special Care Notes",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=500,
                    description="Additional care instructions",
                    example_value="Do not bleach. Wash with similar colors."
                )
            ]
        )
    
    @staticmethod
    def get_technical_specs_group() -> AttributeGroup:
        """Technical specifications attribute group"""
        return AttributeGroup(
            name="technical_specs",
            display_name="Technical Specifications",
            category=AttributeCategory.TECHNICAL_SPECS,
            description="Technical product specifications",
            order=4,
            attributes=[
                AttributeDefinition(
                    name="model_number",
                    display_name="Model Number",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=100,
                    description="Manufacturer model number",
                    example_value="XJ-2024-BLK"
                ),
                AttributeDefinition(
                    name="year_released",
                    display_name="Year Released",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=1900,
                    max_value=2100,
                    description="Year product was released",
                    example_value=2024
                ),
                AttributeDefinition(
                    name="country_of_origin",
                    display_name="Country of Origin",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=100,
                    description="Country where product was manufactured",
                    example_value="USA"
                ),
                AttributeDefinition(
                    name="manufacturer_part_number",
                    display_name="Manufacturer Part Number",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=100,
                    description="Manufacturer's part number",
                    example_value="MPN-12345"
                ),
                AttributeDefinition(
                    name="upc",
                    display_name="UPC/EAN Code",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    regex_pattern=r'^\d{12,13}$',
                    description="Universal Product Code or European Article Number",
                    example_value="123456789012"
                ),
                AttributeDefinition(
                    name="warranty_duration_months",
                    display_name="Warranty Duration (Months)",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=0,
                    max_value=120,
                    description="Warranty duration in months",
                    example_value=12
                )
            ]
        )
    
    @staticmethod
    def get_sustainability_group() -> AttributeGroup:
        """Sustainability attribute group"""
        return AttributeGroup(
            name="sustainability",
            display_name="Sustainability & Ethics",
            category=AttributeCategory.SUSTAINABILITY,
            description="Environmental and ethical information",
            order=5,
            attributes=[
                AttributeDefinition(
                    name="eco_friendly",
                    display_name="Eco-Friendly",
                    data_type=AttributeDataType.BOOLEAN,
                    required=False,
                    description="Whether product is eco-friendly",
                    example_value=True
                ),
                AttributeDefinition(
                    name="eco_certifications",
                    display_name="Eco Certifications",
                    data_type=AttributeDataType.LIST,
                    required=False,
                    description="Environmental certifications",
                    example_value=["Energy Star", "FSC Certified"]
                ),
                AttributeDefinition(
                    name="carbon_neutral",
                    display_name="Carbon Neutral",
                    data_type=AttributeDataType.BOOLEAN,
                    required=False,
                    description="Whether product is carbon neutral",
                    example_value=False
                ),
                AttributeDefinition(
                    name="ethical_sourcing",
                    display_name="Ethical Sourcing",
                    data_type=AttributeDataType.BOOLEAN,
                    required=False,
                    description="Whether materials are ethically sourced",
                    example_value=True
                )
            ]
        )
    
    @staticmethod
    def get_clothing_schema() -> CategorySchema:
        """Complete schema for Clothing category"""
        clothing_specific = AttributeGroup(
            name="category_specific",
            display_name="Clothing Attributes",
            category=AttributeCategory.CATEGORY_SPECIFIC,
            description="Clothing-specific attributes",
            order=6,
            attributes=[
                AttributeDefinition(
                    name="fit_type",
                    display_name="Fit Type",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Regular", "Slim", "Relaxed", "Oversized", "Athletic", "Tailored"],
                    example_value="Regular"
                ),
                AttributeDefinition(
                    name="neckline",
                    display_name="Neckline Style",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Crew", "V-Neck", "Scoop", "Boat", "Collar", "Henley", "Mock Neck", "Turtleneck"],
                    example_value="Crew"
                ),
                AttributeDefinition(
                    name="sleeve_length",
                    display_name="Sleeve Length",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Sleeveless", "Short Sleeve", "3/4 Sleeve", "Long Sleeve"],
                    example_value="Short Sleeve"
                ),
                AttributeDefinition(
                    name="rise",
                    display_name="Rise (Pants)",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Low", "Mid", "High"],
                    example_value="Mid"
                ),
                AttributeDefinition(
                    name="pattern",
                    display_name="Pattern",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Solid", "Striped", "Printed", "Plaid", "Floral", "Geometric", "Animal Print"],
                    example_value="Solid"
                ),
                AttributeDefinition(
                    name="occasion",
                    display_name="Occasion",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Casual", "Formal", "Athletic", "Work", "Party", "Beach"],
                    example_value="Casual"
                ),
                AttributeDefinition(
                    name="season",
                    display_name="Season",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Spring", "Summer", "Fall", "Winter", "All-Season"],
                    example_value="All-Season"
                ),
                AttributeDefinition(
                    name="gender",
                    display_name="Gender",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Men", "Women", "Unisex", "Boys", "Girls"],
                    example_value="Unisex"
                )
            ]
        )
        
        return CategorySchema(
            category_name="Clothing",
            display_name="Clothing",
            description="Apparel and clothing items",
            attribute_groups=[
                StandardSchemas.get_physical_dimensions_group(),
                StandardSchemas.get_materials_group(),
                StandardSchemas.get_care_instructions_group(),
                StandardSchemas.get_technical_specs_group(),
                StandardSchemas.get_sustainability_group(),
                clothing_specific
            ],
            version="1.0",
            is_active=True
        )
    
    @staticmethod
    def get_electronics_schema() -> CategorySchema:
        """Complete schema for Electronics category"""
        electronics_specific = AttributeGroup(
            name="category_specific",
            display_name="Electronics Attributes",
            category=AttributeCategory.CATEGORY_SPECIFIC,
            description="Electronics-specific attributes",
            order=6,
            attributes=[
                AttributeDefinition(
                    name="processor",
                    display_name="Processor/Chipset",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=200,
                    example_value="Intel Core i7-12700K"
                ),
                AttributeDefinition(
                    name="memory_gb",
                    display_name="Memory (GB)",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=0,
                    example_value=16
                ),
                AttributeDefinition(
                    name="storage_gb",
                    display_name="Storage Capacity (GB)",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=0,
                    example_value=512
                ),
                AttributeDefinition(
                    name="display_size_inches",
                    display_name="Display Size (inches)",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=0,
                    example_value=15.6
                ),
                AttributeDefinition(
                    name="display_resolution",
                    display_name="Display Resolution",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=50,
                    example_value="1920x1080"
                ),
                AttributeDefinition(
                    name="connectivity",
                    display_name="Connectivity Options",
                    data_type=AttributeDataType.LIST,
                    required=False,
                    example_value=["WiFi 6", "Bluetooth 5.2", "USB-C", "HDMI"]
                ),
                AttributeDefinition(
                    name="battery_capacity_mah",
                    display_name="Battery Capacity (mAh)",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=0,
                    example_value=5000
                ),
                AttributeDefinition(
                    name="operating_system",
                    display_name="Operating System",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=100,
                    example_value="Windows 11"
                ),
                AttributeDefinition(
                    name="power_rating_watts",
                    display_name="Power Rating (Watts)",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.WATTS,
                    required=False,
                    min_value=0,
                    example_value=65
                )
            ]
        )
        
        return CategorySchema(
            category_name="Electronics",
            display_name="Electronics",
            description="Electronic devices and gadgets",
            attribute_groups=[
                StandardSchemas.get_physical_dimensions_group(),
                StandardSchemas.get_materials_group(),
                StandardSchemas.get_technical_specs_group(),
                StandardSchemas.get_sustainability_group(),
                electronics_specific
            ],
            version="1.0",
            is_active=True
        )
    
    @staticmethod
    def get_home_furniture_schema() -> CategorySchema:
        """Complete schema for Home & Furniture category"""
        furniture_specific = AttributeGroup(
            name="category_specific",
            display_name="Home & Furniture Attributes",
            category=AttributeCategory.CATEGORY_SPECIFIC,
            description="Home and furniture-specific attributes",
            order=6,
            attributes=[
                AttributeDefinition(
                    name="room_type",
                    display_name="Room Type",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Living Room", "Bedroom", "Dining Room", "Kitchen", "Bathroom", "Office", "Outdoor"],
                    example_value="Living Room"
                ),
                AttributeDefinition(
                    name="assembly_required",
                    display_name="Assembly Required",
                    data_type=AttributeDataType.BOOLEAN,
                    required=False,
                    example_value=True
                ),
                AttributeDefinition(
                    name="number_of_pieces",
                    display_name="Number of Pieces",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=1,
                    example_value=1
                ),
                AttributeDefinition(
                    name="style",
                    display_name="Style",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Modern", "Traditional", "Rustic", "Industrial", "Mid-Century", "Contemporary", "Farmhouse"],
                    example_value="Modern"
                ),
                AttributeDefinition(
                    name="upholstery_material",
                    display_name="Upholstery Material",
                    data_type=AttributeDataType.STRING,
                    required=False,
                    max_length=100,
                    example_value="Linen"
                ),
                AttributeDefinition(
                    name="load_capacity_lbs",
                    display_name="Load Capacity (lbs)",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.POUNDS,
                    required=False,
                    min_value=0,
                    example_value=300
                ),
                AttributeDefinition(
                    name="seating_capacity",
                    display_name="Seating Capacity",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=1,
                    example_value=3
                )
            ]
        )
        
        return CategorySchema(
            category_name="Home & Furniture",
            display_name="Home & Furniture",
            description="Furniture and home decor items",
            attribute_groups=[
                StandardSchemas.get_physical_dimensions_group(),
                StandardSchemas.get_materials_group(),
                StandardSchemas.get_care_instructions_group(),
                StandardSchemas.get_technical_specs_group(),
                StandardSchemas.get_sustainability_group(),
                furniture_specific
            ],
            version="1.0",
            is_active=True
        )
    
    @staticmethod
    def get_beauty_schema() -> CategorySchema:
        """Complete schema for Beauty & Personal Care category"""
        beauty_specific = AttributeGroup(
            name="category_specific",
            display_name="Beauty & Personal Care Attributes",
            category=AttributeCategory.CATEGORY_SPECIFIC,
            description="Beauty and personal care-specific attributes",
            order=6,
            attributes=[
                AttributeDefinition(
                    name="skin_type",
                    display_name="Skin Type",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Oily", "Dry", "Combination", "Sensitive", "Normal", "All Skin Types"],
                    example_value="All Skin Types"
                ),
                AttributeDefinition(
                    name="fragrance_type",
                    display_name="Fragrance Type",
                    data_type=AttributeDataType.ENUM,
                    required=False,
                    allowed_values=["Unscented", "Light", "Moderate", "Strong"],
                    example_value="Light"
                ),
                AttributeDefinition(
                    name="spf_rating",
                    display_name="SPF Rating",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=0,
                    max_value=100,
                    example_value=30
                ),
                AttributeDefinition(
                    name="volume_ml",
                    display_name="Volume (ml)",
                    data_type=AttributeDataType.NUMBER,
                    unit=AttributeUnit.MILLILITERS,
                    required=False,
                    min_value=0,
                    example_value=100
                ),
                AttributeDefinition(
                    name="ingredients",
                    display_name="Key Ingredients",
                    data_type=AttributeDataType.LIST,
                    required=False,
                    example_value=["Hyaluronic Acid", "Vitamin C", "Retinol"]
                ),
                AttributeDefinition(
                    name="cruelty_free",
                    display_name="Cruelty Free",
                    data_type=AttributeDataType.BOOLEAN,
                    required=False,
                    example_value=True
                ),
                AttributeDefinition(
                    name="vegan",
                    display_name="Vegan",
                    data_type=AttributeDataType.BOOLEAN,
                    required=False,
                    example_value=True
                ),
                AttributeDefinition(
                    name="shelf_life_months",
                    display_name="Shelf Life (Months)",
                    data_type=AttributeDataType.NUMBER,
                    required=False,
                    min_value=1,
                    max_value=120,
                    example_value=24
                )
            ]
        )
        
        return CategorySchema(
            category_name="Beauty & Personal Care",
            display_name="Beauty & Personal Care",
            description="Beauty and personal care products",
            attribute_groups=[
                StandardSchemas.get_physical_dimensions_group(),
                StandardSchemas.get_materials_group(),
                StandardSchemas.get_technical_specs_group(),
                StandardSchemas.get_sustainability_group(),
                beauty_specific
            ],
            version="1.0",
            is_active=True
        )
    
    @staticmethod
    def get_all_schemas() -> Dict[str, CategorySchema]:
        """Get all predefined schemas"""
        return {
            "Clothing": StandardSchemas.get_clothing_schema(),
            "Electronics": StandardSchemas.get_electronics_schema(),
            "Home & Furniture": StandardSchemas.get_home_furniture_schema(),
            "Beauty & Personal Care": StandardSchemas.get_beauty_schema()
        }
