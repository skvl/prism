from prism.types.builtins import BOOKMARK_TOML, CONTACT_TOML, FILE_TOML, NOTE_TOML
from prism.types.schema import FieldDef, TypeSchema
from prism.types.validator import FieldValidator


class TestTypeSchema:
    def test_schema_creation(self):
        schema = TypeSchema(
            name="test",
            icon="🧪",
            fields=[FieldDef(name="name", type="string", required=True)],
            body_model="null",
        )
        assert schema.name == "test"
        assert schema.get_field("name") is not None
        assert schema.get_field("nonexistent") is None

    def test_validate_fields_required(self):
        schema = TypeSchema(
            name="contact",
            fields=[FieldDef(name="name", type="string", required=True)],
        )
        errors = schema.validate_fields({})
        assert any("required" in e for e in errors)

    def test_validate_fields_unknown(self):
        schema = TypeSchema(
            name="test",
            fields=[FieldDef(name="name", type="string")],
        )
        errors = schema.validate_fields({"name": "Alice", "unknown": "val"})
        assert any("Unknown" in e for e in errors)

    def test_validate_fields_optional_ok(self):
        schema = TypeSchema(
            name="test",
            fields=[FieldDef(name="name", type="string", required=True)],
        )
        errors = schema.validate_fields({"name": "Alice"})
        assert len(errors) == 0

    def test_builtin_note_toml(self):
        import tomlkit

        doc = tomlkit.loads(NOTE_TOML)
        assert doc["name"] == "note"
        assert doc["body_model"] == "file(markdown)"

    def test_builtin_contact_toml(self):
        import tomlkit

        doc = tomlkit.loads(CONTACT_TOML)
        assert doc["name"] == "contact"
        assert doc["body_model"] == "null"

    def test_builtin_bookmark_toml(self):
        import tomlkit

        doc = tomlkit.loads(BOOKMARK_TOML)
        assert doc["name"] == "bookmark"
        assert doc["body_model"] == "null"

    def test_builtin_file_toml(self):
        import tomlkit

        doc = tomlkit.loads(FILE_TOML)
        assert doc["name"] == "file"
        assert doc["body_model"] == "file(binary)"


class TestFieldValidator:
    def test_valid_string(self):
        schema = TypeSchema(
            name="test",
            fields=[FieldDef(name="name", type="string", required=True)],
        )
        validator = FieldValidator(schema)
        errors = validator.validate({"name": "Alice"})
        assert len(errors) == 0

    def test_invalid_type(self):
        schema = TypeSchema(
            name="test",
            fields=[FieldDef(name="count", type="number", required=True)],
        )
        validator = FieldValidator(schema)
        errors = validator.validate({"count": "not-a-number"})
        assert len(errors) > 0

    def test_missing_required(self):
        schema = TypeSchema(
            name="test",
            fields=[FieldDef(name="name", type="string", required=True)],
        )
        validator = FieldValidator(schema)
        errors = validator.validate({})
        assert len(errors) > 0

    def test_unknown_type_passes_validation(self):
        schema = TypeSchema(
            name="test",
            fields=[FieldDef(name="val", type="unknown_type", required=True)],
        )
        validator = FieldValidator(schema)
        errors = validator.validate({"val": "anything"})
        assert len(errors) == 0
