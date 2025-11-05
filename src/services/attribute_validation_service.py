"""
Attribute Validation Service

Validates product attributes against category schemas with comprehensive
type checking, constraint validation, and error reporting.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from src.models.attribute_schema import (
    CategorySchema,
    AttributeDefinition,
    AttributeDataType,
    AttributeValidationError,
    AttributeValidationResult,
    ProductAttributes
)
from src.models.standard_schemas import StandardSchemas
from src.core.logger import logger


class AttributeValidationService:
    """
    Service for validating product attributes against category schemas.
    
    Performs:
    - Data type validation
    - Constraint validation (min/max, length, regex)
    - Enum value validation
    - Required field validation
    - Type coercion where appropriate
    """
    
    def __init__(self):
        """Initialize with standard schemas"""
        self.standard_schemas = StandardSchemas.get_all_schemas()
    
    def validate_attributes(
        self,
        attributes: ProductAttributes,
        category: str,
        correlation_id: Optional[str] = None
    ) -> AttributeValidationResult:
        """
        Validate product attributes against category schema.
        
        Args:
            attributes: Product attributes to validate
            category: Product category name
            correlation_id: For logging
            
        Returns:
            AttributeValidationResult with validation status and errors
        """
        # Convert ProductAttributes to dict for validation
        attr_dict = attributes.get_all_attributes() if isinstance(attributes, ProductAttributes) else attributes
        
        logger.info(
            f"Validating attributes for category: {category}",
            metadata={"category": category, "attr_groups": len(attr_dict)},
            correlation_id=correlation_id
        )
        
        # Get schema for category
        schema = self.standard_schemas.get(category)
        if not schema:
            return AttributeValidationResult(
                is_valid=False,
                errors=[AttributeValidationError(
                    attribute_name="category",
                    attribute_path="category",
                    error_code="UNKNOWN_CATEGORY",
                    error_message=f"No schema found for category: {category}. Available categories: {list(self.standard_schemas.keys())}"
                )]
            )
        
        errors: List[AttributeValidationError] = []
        warnings: List[str] = []
        validated_attrs: Dict[str, Any] = {}
        
        # Build attribute definition lookup
        attr_defs = self._build_attribute_lookup(schema)
        
        # Validate each attribute group
        for group_name, group_attrs in attr_dict.items():
            if not isinstance(group_attrs, dict):
                errors.append(AttributeValidationError(
                    attribute_name=group_name,
                    attribute_path=group_name,
                    error_code="INVALID_GROUP_TYPE",
                    error_message=f"Attribute group must be a dictionary, got {type(group_attrs).__name__}",
                    expected_type="dict",
                    actual_value=group_attrs
                ))
                continue
            
            validated_group = {}
            
            for attr_name, attr_value in group_attrs.items():
                path = f"{group_name}.{attr_name}"
                
                # Check if attribute is defined in schema
                attr_def = attr_defs.get(path)
                if not attr_def:
                    warnings.append(f"Unknown attribute: {path}")
                    validated_group[attr_name] = attr_value
                    continue
                
                # Validate attribute
                validation_errors, validated_value = self._validate_attribute(
                    attr_name=attr_name,
                    attr_value=attr_value,
                    attr_def=attr_def,
                    path=path
                )
                
                if validation_errors:
                    errors.extend(validation_errors)
                else:
                    validated_group[attr_name] = validated_value
            
            if validated_group:
                validated_attrs[group_name] = validated_group
        
        # Check required attributes
        required_errors = self._check_required_attributes(attr_defs, attr_dict)
        errors.extend(required_errors)
        
        is_valid = len(errors) == 0
        
        logger.info(
            f"Validation complete: valid={is_valid}, errors={len(errors)}, warnings={len(warnings)}",
            correlation_id=correlation_id
        )
        
        return AttributeValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_attributes=validated_attrs if is_valid else None
        )
    
    def _build_attribute_lookup(self, schema: CategorySchema) -> Dict[str, AttributeDefinition]:
        """Build flat lookup of all attribute definitions"""
        lookup = {}
        for group in schema.attribute_groups:
            for attr_def in group.attributes:
                path = f"{group.name}.{attr_def.name}"
                lookup[path] = attr_def
        return lookup
    
    def _validate_attribute(
        self,
        attr_name: str,
        attr_value: Any,
        attr_def: AttributeDefinition,
        path: str
    ) -> Tuple[List[AttributeValidationError], Any]:
        """
        Validate a single attribute.
        
        Returns:
            Tuple of (errors, validated_value)
        """
        errors = []
        
        # Handle None values
        if attr_value is None:
            if attr_def.required:
                errors.append(AttributeValidationError(
                    attribute_name=attr_name,
                    attribute_path=path,
                    error_code="REQUIRED_FIELD",
                    error_message=f"{attr_def.display_name} is required",
                    expected_type=attr_def.data_type.value,
                    actual_value=None
                ))
            return errors, attr_def.default_value
        
        # Validate by data type
        if attr_def.data_type == AttributeDataType.STRING:
            return self._validate_string(attr_name, attr_value, attr_def, path)
        
        elif attr_def.data_type == AttributeDataType.NUMBER:
            return self._validate_number(attr_name, attr_value, attr_def, path)
        
        elif attr_def.data_type == AttributeDataType.BOOLEAN:
            return self._validate_boolean(attr_name, attr_value, attr_def, path)
        
        elif attr_def.data_type == AttributeDataType.LIST:
            return self._validate_list(attr_name, attr_value, attr_def, path)
        
        elif attr_def.data_type == AttributeDataType.ENUM:
            return self._validate_enum(attr_name, attr_value, attr_def, path)
        
        elif attr_def.data_type == AttributeDataType.OBJECT:
            return self._validate_object(attr_name, attr_value, attr_def, path)
        
        else:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="UNKNOWN_DATA_TYPE",
                error_message=f"Unknown data type: {attr_def.data_type}",
                actual_value=attr_value
            ))
            return errors, attr_value
    
    def _validate_string(
        self,
        attr_name: str,
        attr_value: Any,
        attr_def: AttributeDefinition,
        path: str
    ) -> Tuple[List[AttributeValidationError], Any]:
        """Validate string attribute"""
        errors = []
        
        # Type check
        if not isinstance(attr_value, str):
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="INVALID_TYPE",
                error_message=f"{attr_def.display_name} must be a string",
                expected_type="string",
                actual_value=attr_value
            ))
            return errors, attr_value
        
        # Length validation
        if attr_def.min_length and len(attr_value) < attr_def.min_length:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="MIN_LENGTH",
                error_message=f"{attr_def.display_name} must be at least {attr_def.min_length} characters",
                constraint=f"min_length: {attr_def.min_length}",
                actual_value=attr_value
            ))
        
        if attr_def.max_length and len(attr_value) > attr_def.max_length:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="MAX_LENGTH",
                error_message=f"{attr_def.display_name} must be at most {attr_def.max_length} characters",
                constraint=f"max_length: {attr_def.max_length}",
                actual_value=attr_value
            ))
        
        # Regex validation
        if attr_def.regex_pattern:
            if not re.match(attr_def.regex_pattern, attr_value):
                errors.append(AttributeValidationError(
                    attribute_name=attr_name,
                    attribute_path=path,
                    error_code="PATTERN_MISMATCH",
                    error_message=f"{attr_def.display_name} does not match required pattern",
                    constraint=f"pattern: {attr_def.regex_pattern}",
                    actual_value=attr_value
                ))
        
        return errors, attr_value
    
    def _validate_number(
        self,
        attr_name: str,
        attr_value: Any,
        attr_def: AttributeDefinition,
        path: str
    ) -> Tuple[List[AttributeValidationError], Any]:
        """Validate number attribute"""
        errors = []
        
        # Type check and coercion
        if isinstance(attr_value, bool):
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="INVALID_TYPE",
                error_message=f"{attr_def.display_name} must be a number",
                expected_type="number",
                actual_value=attr_value
            ))
            return errors, attr_value
        
        if not isinstance(attr_value, (int, float)):
            try:
                attr_value = float(attr_value)
            except (ValueError, TypeError):
                errors.append(AttributeValidationError(
                    attribute_name=attr_name,
                    attribute_path=path,
                    error_code="INVALID_TYPE",
                    error_message=f"{attr_def.display_name} must be a number",
                    expected_type="number",
                    actual_value=attr_value
                ))
                return errors, attr_value
        
        # Range validation
        if attr_def.min_value is not None and attr_value < attr_def.min_value:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="MIN_VALUE",
                error_message=f"{attr_def.display_name} must be at least {attr_def.min_value}",
                constraint=f"min_value: {attr_def.min_value}",
                actual_value=attr_value
            ))
        
        if attr_def.max_value is not None and attr_value > attr_def.max_value:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="MAX_VALUE",
                error_message=f"{attr_def.display_name} must be at most {attr_def.max_value}",
                constraint=f"max_value: {attr_def.max_value}",
                actual_value=attr_value
            ))
        
        return errors, attr_value
    
    def _validate_boolean(
        self,
        attr_name: str,
        attr_value: Any,
        attr_def: AttributeDefinition,
        path: str
    ) -> Tuple[List[AttributeValidationError], Any]:
        """Validate boolean attribute"""
        errors = []
        
        if not isinstance(attr_value, bool):
            # Try to coerce
            if isinstance(attr_value, str):
                if attr_value.lower() in ['true', '1', 'yes']:
                    return errors, True
                elif attr_value.lower() in ['false', '0', 'no']:
                    return errors, False
            
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="INVALID_TYPE",
                error_message=f"{attr_def.display_name} must be a boolean",
                expected_type="boolean",
                actual_value=attr_value
            ))
            return errors, attr_value
        
        return errors, attr_value
    
    def _validate_list(
        self,
        attr_name: str,
        attr_value: Any,
        attr_def: AttributeDefinition,
        path: str
    ) -> Tuple[List[AttributeValidationError], Any]:
        """Validate list attribute"""
        errors = []
        
        if not isinstance(attr_value, list):
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="INVALID_TYPE",
                error_message=f"{attr_def.display_name} must be a list",
                expected_type="list",
                actual_value=attr_value
            ))
            return errors, attr_value
        
        # Length validation
        if attr_def.min_length and len(attr_value) < attr_def.min_length:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="MIN_LENGTH",
                error_message=f"{attr_def.display_name} must have at least {attr_def.min_length} items",
                constraint=f"min_length: {attr_def.min_length}",
                actual_value=attr_value
            ))
        
        if attr_def.max_length and len(attr_value) > attr_def.max_length:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="MAX_LENGTH",
                error_message=f"{attr_def.display_name} must have at most {attr_def.max_length} items",
                constraint=f"max_length: {attr_def.max_length}",
                actual_value=attr_value
            ))
        
        return errors, attr_value
    
    def _validate_enum(
        self,
        attr_name: str,
        attr_value: Any,
        attr_def: AttributeDefinition,
        path: str
    ) -> Tuple[List[AttributeValidationError], Any]:
        """Validate enum attribute"""
        errors = []
        
        if not isinstance(attr_value, str):
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="INVALID_TYPE",
                error_message=f"{attr_def.display_name} must be a string",
                expected_type="string",
                actual_value=attr_value
            ))
            return errors, attr_value
        
        # Check allowed values
        if attr_def.allowed_values and attr_value not in attr_def.allowed_values:
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="INVALID_ENUM_VALUE",
                error_message=f"{attr_def.display_name} must be one of: {', '.join(attr_def.allowed_values)}",
                allowed_values=attr_def.allowed_values,
                actual_value=attr_value
            ))
        
        return errors, attr_value
    
    def _validate_object(
        self,
        attr_name: str,
        attr_value: Any,
        attr_def: AttributeDefinition,
        path: str
    ) -> Tuple[List[AttributeValidationError], Any]:
        """Validate object attribute"""
        errors = []
        
        if not isinstance(attr_value, dict):
            errors.append(AttributeValidationError(
                attribute_name=attr_name,
                attribute_path=path,
                error_code="INVALID_TYPE",
                error_message=f"{attr_def.display_name} must be an object",
                expected_type="object",
                actual_value=attr_value
            ))
            return errors, attr_value
        
        return errors, attr_value
    
    def _check_required_attributes(
        self,
        attr_defs: Dict[str, AttributeDefinition],
        attributes: Dict[str, Any]
    ) -> List[AttributeValidationError]:
        """Check that all required attributes are present"""
        errors = []
        
        for path, attr_def in attr_defs.items():
            if not attr_def.required:
                continue
            
            # Parse path (group.attribute)
            parts = path.split('.')
            if len(parts) != 2:
                continue
            
            group_name, attr_name = parts
            
            # Check if attribute is present
            group = attributes.get(group_name, {})
            if not isinstance(group, dict) or attr_name not in group or group[attr_name] is None:
                errors.append(AttributeValidationError(
                    attribute_name=attr_name,
                    attribute_path=path,
                    error_code="REQUIRED_FIELD",
                    error_message=f"{attr_def.display_name} is required",
                    expected_type=attr_def.data_type.value
                ))
        
        return errors
    
    def get_schema(self, category: str) -> Optional[CategorySchema]:
        """Get schema for a category"""
        return self.standard_schemas.get(category)
    
    def list_categories(self) -> List[str]:
        """List all available categories"""
        return list(self.standard_schemas.keys())
