from dataclasses import dataclass, asdict
from typing import Dict, Optional

@dataclass
class UserPreferences:
    language: str = "en"
    theme: str = "light"
    notification_enabled: bool = True
    auto_save: bool = True

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, str]] = None) -> 'UserPreferences':
        """Create UserPreferences instance from dictionary"""
        if not data:
            return cls()
        
        # Convert string values to appropriate types
        preferences = {}
        for key, value in data.items():
            if key in ['notification_enabled', 'auto_save']:
                preferences[key] = str(value).lower() == 'true'
            else:
                preferences[key] = value
        
        return cls(**preferences)

    def to_dict(self) -> Dict[str, str]:
        """Convert preferences to dictionary with string values"""
        return {k: str(v) for k, v in asdict(self).items()} 