import unittest
from pathlib import Path
import shutil
import tempfile

from storage import LocalStorage
from user_preferences import UserPreferences

class TestStorage(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp())
        self.storage = LocalStorage(storage_dir=self.test_dir)
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir)
        
    def test_save_and_load_preferences(self):
        # Create test preferences
        prefs = UserPreferences(
            language="fr",
            theme="dark",
            notification_enabled=False,
            auto_save=True
        )
        
        # Save preferences
        self.storage.save_preferences(prefs.to_dict())
        
        # Load preferences
        loaded_data = self.storage.load_preferences()
        loaded_prefs = UserPreferences.from_dict(loaded_data)
        
        # Verify loaded preferences match original
        self.assertEqual(loaded_prefs.language, "fr")
        self.assertEqual(loaded_prefs.theme, "dark")
        self.assertEqual(loaded_prefs.notification_enabled, False)
        self.assertEqual(loaded_prefs.auto_save, True)
        
    def test_clear_preferences(self):
        # Save some preferences
        prefs = UserPreferences()
        self.storage.save_preferences(prefs.to_dict())
        
        # Verify file exists
        self.assertTrue(self.storage.preferences_file.exists())
        
        # Clear preferences
        self.storage.clear_preferences()
        
        # Verify file is gone
        self.assertFalse(self.storage.preferences_file.exists())
        
    def test_load_nonexistent_preferences(self):
        # Load preferences when file doesn't exist
        loaded_data = self.storage.load_preferences()
        loaded_prefs = UserPreferences.from_dict(loaded_data)
        
        # Verify default values
        self.assertEqual(loaded_prefs.language, "en")
        self.assertEqual(loaded_prefs.theme, "light")
        self.assertEqual(loaded_prefs.notification_enabled, True)
        self.assertEqual(loaded_prefs.auto_save, True)

if __name__ == '__main__':
    unittest.main() 