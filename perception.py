from pathlib import Path
from typing import Optional, Tuple
import logging
from models import UserPreferences, MigrationType, ReleaseType
from storage import LocalStorage

logger = logging.getLogger(__name__)

class Perception:
    def __init__(self):
        self.storage = LocalStorage()

    def _validate_project_path(self, path: str) -> Path:
        """Validate project path"""
        project_path = Path(path.strip())
        if not project_path.exists():
            raise ValueError(f"Project path {project_path} does not exist")
        return project_path

    def _validate_migration_type(self, migration_type: str) -> MigrationType:
        """Validate migration type"""
        try:
            return MigrationType(migration_type.lower())
        except ValueError:
            raise ValueError(f"Invalid migration type: {migration_type}")

    def _validate_release_type(self, release_type: str) -> ReleaseType:
        """Validate release type"""
        try:
            return ReleaseType(release_type.lower())
        except ValueError:
            raise ValueError(f"Invalid release type: {release_type}")

    def _get_user_choice(self, saved_value: str, preference_name: str) -> Tuple[str, bool]:
        """Get user choice for using saved value or entering new one"""
        while True:
            print(f"\nFound saved {preference_name}: {saved_value}")
            choice = input(f"Use saved {preference_name}? (y/n): ").lower().strip()
            if choice in ['y', 'n']:
                return saved_value if choice == 'y' else input(f"Enter new {preference_name}: "), choice == 'y'
            print("Please enter 'y' or 'n'")

    def get_user_input(self) -> UserPreferences:
        """Get and validate user input, with option to use saved preferences"""
        try:
            # Load saved preferences
            saved_prefs = self.storage.load_preferences()
            
            if saved_prefs:
                print("\nFound saved preferences:")
                print(f"Project Path: {saved_prefs['project_path']}")
                print(f"Migration Type: {saved_prefs['migration_type']}")
                print(f"Release Type: {saved_prefs['release_type']}")
                
                use_saved = input("\nUse all saved preferences? (y/n/select): ").lower().strip()
                
                if use_saved == 'y':
                    # Use all saved preferences
                    return UserPreferences(
                        project_path=Path(saved_prefs['project_path']),
                        migration_type=MigrationType(saved_prefs['migration_type']),
                        release_type=ReleaseType(saved_prefs['release_type'])
                    )
                elif use_saved == 'select':
                    # Selectively use saved preferences
                    project_path_str, used_saved_path = self._get_user_choice(
                        saved_prefs['project_path'], "project path")
                    migration_type_str, used_saved_migration = self._get_user_choice(
                        saved_prefs['migration_type'], "migration type")
                    release_type_str, used_saved_release = self._get_user_choice(
                        saved_prefs['release_type'], "release type")
                else:
                    # Get all new preferences
                    project_path_str = input("Enter project path: ")
                    migration_type_str = input("Enter migration type (java/python): ")
                    release_type_str = input("Enter release type (stable/rc): ")
            else:
                # No saved preferences, get all new
                project_path_str = input("Enter project path: ")
                migration_type_str = input("Enter migration type (java/python): ")
                release_type_str = input("Enter release type (stable/rc): ")

            # Validate inputs
            project_path = self._validate_project_path(project_path_str)
            migration_type = self._validate_migration_type(migration_type_str)
            release_type = self._validate_release_type(release_type_str)

            # Create preferences object
            preferences = UserPreferences(
                project_path=project_path,
                migration_type=migration_type,
                release_type=release_type
            )

            # Save new preferences
            self.storage.save_preferences({
                "project_path": str(project_path),
                "migration_type": migration_type.value,
                "release_type": release_type.value
            })

            return preferences

        except Exception as e:
            logger.error(f"Error in get_user_input: {e}")
            raise

    @staticmethod
    def get_llm_input() -> str:
        """Get input from LLM or user during development"""
        return input("Enter LLM response (or 'exit' to quit): ") 