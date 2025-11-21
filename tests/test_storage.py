import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json
import gzip

from src.storage import BaseStore


class TestableStore(BaseStore):
    """Concrete implementation for testing BaseStore."""
    filename = "test.json.gz"
    model_class = MagicMock


class TestBaseStoreLoad(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("src.storage.GLib.get_user_data_dir")
    def test_load_nonexistent_file(self, mock_glib):
        """Test loading when file doesn't exist returns empty list."""
        mock_glib.return_value = str(self.temp_path)
        store = TestableStore("test_app")
        self.assertEqual(store.items, [])

    @patch("src.storage.GLib.get_user_data_dir")
    def test_load_valid_gzip_json(self, mock_glib):
        """Test loading valid gzip JSON file."""
        mock_glib.return_value = str(self.temp_path)
        
        # Create valid gzip file
        file_path = self.temp_path / "test_app" / "test.json.gz"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(file_path, "wt", encoding="utf-8") as f:
            json.dump([{"id": 1}, {"id": 2}], f)
        
        mock_model = MagicMock()
        mock_model.from_dict.side_effect = lambda x: f"Item({x['id']})"
        
        with patch.object(TestableStore, "model_class", mock_model):
            store = TestableStore("test_app")
            self.assertEqual(len(store.items), 2)
            self.assertEqual(store.items[0], "Item(1)")
            self.assertEqual(store.items[1], "Item(2)")

    @patch("src.storage.GLib.get_user_data_dir")
    def test_load_corrupt_gzip(self, mock_glib):
        """Test loading corrupt gzip file returns empty list."""
        mock_glib.return_value = str(self.temp_path)
        
        file_path = self.temp_path / "test_app" / "test.json.gz"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(b"not valid gzip data")
        
        store = TestableStore("test_app")
        self.assertEqual(store.items, [])

    @patch("src.storage.GLib.get_user_data_dir")
    def test_load_non_list_json(self, mock_glib):
        """Test loading JSON that's not a list returns empty list."""
        mock_glib.return_value = str(self.temp_path)
        
        file_path = self.temp_path / "test_app" / "test.json.gz"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(file_path, "wt", encoding="utf-8") as f:
            json.dump({"key": "value"}, f)
        
        store = TestableStore("test_app")
        self.assertEqual(store.items, [])

    @patch("src.storage.GLib.get_user_data_dir")
    def test_load_empty_list(self, mock_glib):
        """Test loading empty list."""
        mock_glib.return_value = str(self.temp_path)
        
        file_path = self.temp_path / "test_app" / "test.json.gz"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(file_path, "wt", encoding="utf-8") as f:
            json.dump([], f)
        
        store = TestableStore("test_app")
        self.assertEqual(store.items, [])


if __name__ == "__main__":
    unittest.main()