import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class LocalStorage:
    def __init__(self):
        self.storage_dir = Path.home() / '.migration_agent'
        self.preferences_file = self.storage_dir / 'preferences.json'
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating storage directory: {e}")
            raise

    def save_preferences(self, preferences: Dict[str, str]):
        """Save preferences to local storage"""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(preferences, f, indent=4)
            logger.info(f"Preferences saved to {self.preferences_file}")
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            raise

    def load_preferences(self) -> Optional[Dict[str, str]]:
        """Load preferences from local storage"""
        try:
            if not self.preferences_file.exists():
                return None
            with open(self.preferences_file, 'r') as f:
                preferences = json.load(f)
            logger.info(f"Preferences loaded from {self.preferences_file}")
            return preferences
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
            return None

    def clear_preferences(self):
        """Clear saved preferences"""
        try:
            if self.preferences_file.exists():
                self.preferences_file.unlink()
            logger.info("Preferences cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing preferences: {e}")
            raise 