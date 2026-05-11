import os
import shutil
import tempfile

from prism.types.builtins import CONTACT_TOML, NOTE_TOML
from prism.types.loader import TypeLoader


class TestTypeLoader:
    def setup_method(self):
        self.types_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.types_dir)

    def test_load_all_empty_dir(self):
        loader = TypeLoader(self.types_dir)
        schemas = loader.load_all()
        assert schemas == {}

    def test_load_all_nonexistent_dir(self):
        loader = TypeLoader("/nonexistent/path/types")
        schemas = loader.load_all()
        assert schemas == {}

    def test_load_all_with_types(self):
        with open(os.path.join(self.types_dir, "note.toml"), "w") as f:
            f.write(NOTE_TOML)
        with open(os.path.join(self.types_dir, "contact.toml"), "w") as f:
            f.write(CONTACT_TOML)
        loader = TypeLoader(self.types_dir)
        schemas = loader.load_all()
        assert set(schemas) == {"note", "contact"}

    def test_load_all_sorted(self):
        with open(os.path.join(self.types_dir, "b.toml"), "w") as f:
            f.write('name = "b"\nbody_model = "null"\n')
        with open(os.path.join(self.types_dir, "a.toml"), "w") as f:
            f.write('name = "a"\nbody_model = "null"\n')
        loader = TypeLoader(self.types_dir)
        schemas = loader.load_all()
        assert list(schemas) == ["a", "b"]

    def test_load_existing_type(self):
        with open(os.path.join(self.types_dir, "note.toml"), "w") as f:
            f.write(NOTE_TOML)
        loader = TypeLoader(self.types_dir)
        schema = loader.load("note")
        assert schema is not None
        assert schema.name == "note"
        assert schema.body_model == "file(markdown)"

    def test_load_nonexistent_type(self):
        loader = TypeLoader(self.types_dir)
        schema = loader.load("nonexistent")
        assert schema is None

    def test_parse_file_missing_name(self):
        path = os.path.join(self.types_dir, "bad.toml")
        with open(path, "w") as f:
            f.write('icon = "test"\n')
        loader = TypeLoader(self.types_dir)
        schema = loader.load("bad")
        assert schema is None

    def test_parse_file_invalid_body_model(self):
        path = os.path.join(self.types_dir, "bad.toml")
        with open(path, "w") as f:
            f.write('name = "bad"\nbody_model = "invalid"\n')
        loader = TypeLoader(self.types_dir)
        schema = loader.load("bad")
        assert schema is None

    def test_parse_file_invalid_field_type(self):
        path = os.path.join(self.types_dir, "bad.toml")
        with open(path, "w") as f:
            f.write('name = "bad"\nbody_model = "null"\n[[fields]]\nname = "x"\ntype = "invalid"\n')
        loader = TypeLoader(self.types_dir)
        schema = loader.load("bad")
        assert schema is not None
        assert len(schema.fields) == 0

    def test_parse_file_exception(self):
        path = os.path.join(self.types_dir, "bad.toml")
        with open(path, "w") as f:
            f.write("not [[valid toml = {{{{\n")
        loader = TypeLoader(self.types_dir)
        schema = loader.load("bad")
        assert schema is None
