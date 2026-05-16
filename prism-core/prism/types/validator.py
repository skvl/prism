"""Field validation against type schemas.

Validates field values match their expected types.
"""

from typing import Any

from prism.types.schema import TypeSchema


class FieldValidator:
    """Validates field values against a type schema's field definitions."""

    def __init__(self, schema: TypeSchema) -> None:
        """Initialize the validator.

        Args:
            schema: The TypeSchema to validate against.
        """
        self.schema = schema

    def validate(self, field_values: dict[str, Any]) -> list[str]:
        """Validate field values against the schema.

        Args:
            field_values: Dictionary of field name to value.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors: list[str] = []

        for field_def in self.schema.fields:
            value = field_values.get(field_def.name)
            if value is None:
                if field_def.required:
                    errors.append(
                        f"Field '{field_def.name}' is required for type '{self.schema.name}'"
                    )
                continue

            if not self._check_type(value, field_def.type):
                errors.append(
                    f"Field '{field_def.name}' should be of type "
                    f"'{field_def.type}', got {type(value).__name__}"
                )

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        type_map = {
            "string": lambda v: isinstance(v, str),
            "url": lambda v: isinstance(v, str),
            "datetime": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)),
            "array": lambda v: isinstance(v, list),
        }
        checker = type_map.get(expected_type)
        if checker is None:
            return True
        return checker(value)
