from pathlib import Path
from models import UserPreferences, MigrationType, ReleaseType

class Perception:
    @staticmethod
    def get_user_input() -> UserPreferences:
        """Pure function to get and validate user input"""
        project_path = Path(input("Enter project path: ").strip())
        migration_type_input = input("Enter migration type (java/python): ").lower()
        release_type_input = input("Enter release type (stable/rc): ").lower()
        
        # Validate inputs
        if not project_path.exists():
            raise ValueError(f"Project path {project_path} does not exist")
        
        try:
            migration_type = MigrationType(migration_type_input)
        except ValueError:
            raise ValueError(f"Invalid migration type: {migration_type_input}")
        
        try:
            release_type = ReleaseType(release_type_input)
        except ValueError:
            raise ValueError(f"Invalid release type: {release_type_input}")
        
        return UserPreferences(
            project_path=project_path,
            migration_type=migration_type,
            release_type=release_type
        )

    @staticmethod
    def get_llm_input() -> str:
        """Get input from LLM or user during development"""
        return input("Enter LLM response (or 'exit' to quit): ") 