"""Type schema and field definitions.

Defines FieldDef and TypeSchema dataclasses plus valid value sets.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FieldDef:
    """Defines a single field within a type schema.

    Attributes:
        name: Field identifier.
        type: One of string, url, datetime, number, array.
        required: Whether the field must have a value.
        default: Default value if not provided.
    """

    name: str
    type: str
    required: bool = False
    default: Optional[Any] = None


@dataclass
class TypeSchema:
    """Defines a complete type with fields and body model.

    Attributes:
        name: Unique type identifier.
        icon: Emoji icon for display.
        fields: List of field definitions.
        body_model: One of null, file(markdown), file(binary).
    """

    name: str
    icon: str = ""
    fields: list[FieldDef] = field(default_factory=list)
    body_model: str = "null"

    def get_field(self, name: str) -> Optional[FieldDef]:
        """Look up a field definition by name.

        Args:
            name: Field name to find.

        Returns:
            The matching FieldDef or None.
        """
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def validate_fields(self, field_values: dict[str, Any]) -> list[str]:
        """Validate field values against this schema.

        Checks required fields are present and no unknown fields exist.

        Args:
            field_values: Dictionary of field name to value.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors: list[str] = []
        for f in self.fields:
            if f.name not in field_values or field_values[f.name] is None:
                if f.required:
                    errors.append(f"Field '{f.name}' is required for type '{self.name}'")
        for key in field_values:
            if key not in [f.name for f in self.fields]:
                errors.append(f"Unknown field '{key}' for type '{self.name}'. It will be ignored.")
        return errors


VALID_TYPES = {"string", "url", "datetime", "number", "array"}
VALID_BODY_MODELS = {"null", "file(markdown)", "file(binary)"}
