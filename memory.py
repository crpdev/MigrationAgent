from typing import Dict, Any, Optional
import logging
import json
from models import UserPreferences
from storage import LocalStorage

logger = logging.getLogger(__name__)

class Memory:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.storage = LocalStorage()
        self._load_saved_preferences()

    def _load_saved_preferences(self):
        """Load saved preferences from local storage"""
        try:
            saved_prefs = self.storage.load_preferences()
            if saved_prefs:
                self.state['saved_preferences'] = saved_prefs
        except Exception as e:
            logger.error(f"Error loading saved preferences: {e}")

    def store_user_preferences(self, preferences: UserPreferences):
        """Store user preferences in memory and local storage"""
        try:
            # Store in memory state
            self.state['user_preferences'] = {
                'project_path': str(preferences.project_path),
                'migration_type': preferences.migration_type.value,
                'release_type': preferences.release_type.value
            }

            # Store in local storage
            self.storage.save_preferences(self.state['user_preferences'])
            logger.info("User preferences stored successfully")
        except Exception as e:
            logger.error(f"Error storing user preferences: {e}")
            raise

    def get_user_preferences(self) -> Optional[Dict[str, str]]:
        """Retrieve user preferences from memory"""
        return self.state.get('user_preferences')

    def get_saved_preferences(self) -> Optional[Dict[str, str]]:
        """Retrieve saved preferences from memory"""
        return self.state.get('saved_preferences')

    def store_last_action(self, action: str):
        """Store the last action executed"""
        self.state['last_action'] = action
        
        # Try to extract recipe_id from migrationPlan response
        if "migrationPlan" in action:
            try:
                # Find the JSON content in the response
                start_idx = action.find('{"success"')
                if start_idx != -1:
                    end_idx = action.find('FUNCTION_CALL: migrationPlan|', start_idx)
                    if end_idx == -1:
                        end_idx = len(action)
                    json_str = action[start_idx:end_idx].strip()
                    if json_str:
                        response_data = json.loads(json_str)
                        if isinstance(response_data, dict) and 'recipe' in response_data:
                            recipe = response_data['recipe']
                            if isinstance(recipe, dict) and 'recipe_id' in recipe:
                                self.store_recipe_id(recipe['recipe_id'])
                                logger.info(f"Successfully extracted and stored recipe_id in memory: {recipe['recipe_id']}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from migrationPlan response: {e}")
            except Exception as e:
                logger.error(f"Error extracting recipe_id from migrationPlan response: {e}")

    def get_last_action(self) -> Optional[str]:
        """Retrieve the last action executed"""
        return self.state.get('last_action')

    def store_last_response(self, response: str):
        """Store the last response received"""
        self.state['last_response'] = response

    def get_last_response(self) -> Optional[str]:
        """Retrieve the last response received"""
        return self.state.get('last_response')

    def store_recipe_id(self, recipe_id: str):
        """Store the recipe ID"""
        logger.info(f"Storing recipe_id in memory: {recipe_id}")
        self.state['recipe_id'] = recipe_id

    def get_recipe_id(self) -> Optional[str]:
        """Retrieve the recipe ID"""
        recipe_id = self.state.get('recipe_id')
        if not recipe_id:
            logger.warning("No recipe_id found in memory")
            # Try to extract from last action if available
            last_action = self.get_last_action()
            if last_action and "migrationPlan" in last_action:
                try:
                    start_idx = last_action.find('{"success"')
                    if start_idx != -1:
                        end_idx = last_action.find('FUNCTION_CALL: migrationPlan|', start_idx)
                        if end_idx == -1:
                            end_idx = len(last_action)
                        json_str = last_action[start_idx:end_idx].strip()
                        if json_str:
                            response_data = json.loads(json_str)
                            if isinstance(response_data, dict) and 'recipe' in response_data:
                                recipe = response_data['recipe']
                                if isinstance(recipe, dict) and 'recipe_id' in recipe:
                                    recipe_id = recipe['recipe_id']
                                    self.store_recipe_id(recipe_id)
                                    logger.info(f"Successfully extracted and stored recipe_id from last action: {recipe_id}")
                except Exception as e:
                    logger.error(f"Error extracting recipe_id from last action: {e}")
        return recipe_id

    def clear(self):
        """Clear all memory state"""
        self.state.clear()
        try:
            self.storage.clear_preferences()
            logger.info("Memory and local storage cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing local storage: {e}")
            raise 