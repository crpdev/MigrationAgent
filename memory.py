from typing import Any, Optional
from models import MemoryState, UserPreferences

class Memory:
    @staticmethod
    def save_to_memory(state: MemoryState, key: str, value: Any) -> MemoryState:
        """Pure function to update memory state"""
        new_context = dict(state.context)
        new_context[key] = value
        return MemoryState(preferences=state.preferences, context=new_context)

    @staticmethod
    def get_from_memory(state: MemoryState, key: str) -> Optional[Any]:
        """Pure function to retrieve from memory"""
        return state.context.get(key)

    @staticmethod
    def create_initial_state(preferences: UserPreferences) -> MemoryState:
        """Create initial memory state"""
        return MemoryState(preferences=preferences) 