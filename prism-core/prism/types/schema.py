from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FieldDef:
    name: str
    type: str
    required: bool = False
    default: Optional[Any] = None


@dataclass
class TypeSchema:
    name: str
    icon: str = ""
    fields: list[FieldDef] = field(default_factory=list)
    body_model: str = "null"

    def get_field(self, name: str) -> Optional[FieldDef]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def validate_fields(self, field_values: dict[str, Any]) -> list[str]:
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
