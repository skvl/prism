"""Type schema loading from TOML files.

Loads and parses .toml type definitions from a vault's types directory.
"""

from pathlib import Path
from typing import Optional

import tomlkit

from prism.types.schema import FieldDef, TypeSchema, VALID_BODY_MODELS, VALID_TYPES


class TypeLoader:
    """Loads and parses type schema definitions from TOML files."""

    def __init__(self, types_dir: str) -> None:
        """Initialize the loader.

        Args:
            types_dir: Path to the directory containing .toml type files.
        """
        self.types_dir = Path(types_dir)

    def load_all(self) -> dict[str, TypeSchema]:
        """Load all type schemas from the types directory.

        Returns:
            Dictionary mapping type name to TypeSchema.
        """
        schemas: dict[str, TypeSchema] = {}
        if not self.types_dir.exists():
            return schemas
        for toml_file in sorted(self.types_dir.glob("*.toml")):
            schema = self._parse_file(toml_file)
            if schema is not None:
                schemas[schema.name] = schema
        return schemas

    def load(self, type_name: str) -> Optional[TypeSchema]:
        """Load a single type schema by name.

        Args:
            type_name: Name of the type (filename without .toml).

        Returns:
            The TypeSchema or None if not found.
        """
        toml_file = self.types_dir / f"{type_name}.toml"
        if not toml_file.exists():
            return None
        return self._parse_file(toml_file)

    def _parse_file(self, path: Path) -> Optional[TypeSchema]:
        try:
            with open(path) as f:
                doc = tomlkit.load(f)

            name = doc.get("name")
            if not name:
                print(f"Validation error: type schema at {path} is missing 'name' field. Skipping.")
                return None

            icon = doc.get("icon", "")
            body_model = doc.get("body_model", "null")
            if body_model not in VALID_BODY_MODELS:
                print(f"Validation error: type '{name}' has invalid body_model '{body_model}'. Skipping.")
                return None

            fields: list[FieldDef] = []
            for raw in doc.get("fields", []):
                field_type = raw.get("type", "string")
                if field_type not in VALID_TYPES:
                    print(f"Validation error: type '{name}' field '{raw.get('name')}' has invalid type '{field_type}'. Skipping.")
                    continue
                fields.append(
                    FieldDef(
                        name=raw["name"],
                        type=field_type,
                        required=raw.get("required", False),
                        default=raw.get("default"),
                    )
                )

            return TypeSchema(name=name, icon=icon, fields=fields, body_model=body_model)
        except Exception as e:
            print(f"Error parsing type schema {path}: {e}. Skipping.")
            return None
