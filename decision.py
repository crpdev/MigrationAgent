from typing import Tuple, Dict, Any
import logging
from datetime import datetime
import os
import google.generativeai as genai
import asyncio
from models import MemoryState, Decision
import json

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DecisionMaking:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.tools_description = None
        self.moderne_tools = []
        self.maven_tools = []
        self.workflow_steps = {
            'analyzeProject': 1,
            'migrationPlan': 2,
            'modUpgradeAll': 3
        }
        self.current_step = 1
        # Map common function names to actual tool names
        self.function_map = {
            'analyzeproject': 'analyzeProject',
            'migrationplan': 'migrationPlan',
            'modupgradeall': 'modUpgradeAll'
        }

    def update_workflow_state(self, function_name: str):
        """Update the current workflow step"""
        if function_name in self.workflow_steps:
            self.current_step = self.workflow_steps[function_name]

    def get_next_step(self) -> str:
        """Get the expected next step in the workflow"""
        next_step = self.current_step + 1
        for func, step in self.workflow_steps.items():
            if step == next_step:
                return func
        return None

    def get_actual_function_name(self, function_name: str) -> str:
        """Map function name to actual tool name"""
        normalized_name = function_name.lower().replace('_', '')
        return self.function_map.get(normalized_name, function_name)

    def is_valid_function(self, function_name: str) -> bool:
        """Check if function exists in available tools"""
        actual_name = self.get_actual_function_name(function_name)
        moderne_tool_names = [tool.name for tool in self.moderne_tools]
        maven_tool_names = [tool.name for tool in self.maven_tools]
        return actual_name in moderne_tool_names or actual_name in maven_tool_names

    async def initialize_tools(self, moderne_tools: list, maven_tools: list):
        """Initialize available tools description"""
        self.moderne_tools = moderne_tools
        self.maven_tools = maven_tools
        tools_description = []
        
        # Add Moderne tools
        tools_description.append("Moderne TOOLS:")
        for i, tool in enumerate(moderne_tools):
            try:
                params = tool.inputSchema
                desc = getattr(tool, 'description', 'No description available')
                name = getattr(tool, 'name', f'tool_{i}')
                
                if 'properties' in params:
                    param_details = []
                    for param_name, param_info in params['properties'].items():
                        param_type = param_info.get('type', 'unknown')
                        param_details.append(f"{param_name}: {param_type}")
                    params_str = ', '.join(param_details)
                else:
                    params_str = 'no parameters'

                tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                tools_description.append(tool_desc)
            except Exception as e:
                logger.error(f"Error processing Moderne tool {i}: {e}")

        # Add Maven tools
        tools_description.append("\nMAVEN TOOLS:")
        for i, tool in enumerate(maven_tools):
            try:
                params = tool.inputSchema
                desc = getattr(tool, 'description', 'No description available')
                name = getattr(tool, 'name', f'tool_{i}')
                
                if 'properties' in params:
                    param_details = []
                    for param_name, param_info in params['properties'].items():
                        param_type = param_info.get('type', 'unknown')
                        param_details.append(f"{param_name}: {param_type}")
                    params_str = ', '.join(param_details)
                else:
                    params_str = 'no parameters'

                tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                tools_description.append(tool_desc)
            except Exception as e:
                logger.error(f"Error processing Maven tool {i}: {e}")

        self.tools_description = "\n".join(tools_description)
        logger.info("Tools description initialized")

    def create_system_prompt(self, state: MemoryState) -> str:
        """Create system prompt with tools and user preferences"""
        user_prefs = {
            "project_path": str(state.preferences.project_path),
            "migration_type": state.preferences.migration_type.value,
            "release_type": state.preferences.release_type.value
        }
        
        # Get the next expected step
        next_step = self.get_next_step()
        workflow_hint = f"Expected next step: {next_step}" if next_step else ""
        
        # Check if we have a recipe_id in memory
        recipe_id = state.context.get("recipe_id", "")
        recipe_status = "Recipe ID available: " + recipe_id if recipe_id else "No recipe ID yet - run migrationPlan first"
        
        system_prompt = f"""You are a cognitive Java upgrade assistant.

Current User Preferences:
- Project Path: {user_prefs['project_path']}
- Migration Type: {user_prefs['migration_type']}
- Release Type: {user_prefs['release_type']}

Migration Workflow Steps (in order):
1. analyzeProject - Analyze project
2. migrationPlan - Generate migration plan
3. modUpgradeAll - Apply upgrade using recipe_id

Current Progress: Step {self.current_step} of 3
{workflow_hint}
{recipe_status}

Available tools:
{self.tools_description}

CRITICAL INSTRUCTION: You MUST respond with EXACTLY ONE LINE, with NO additional text, explanations, or newlines.
Choose ONE of these formats:

1. For function calls (using key=value format):
   FUNCTION_CALL: function_name|param1=value1|param2=value2|...

2. For final answers:
   FINAL_ANSWER: [your response]

Examples of VALID responses (each is ONE line with NO additional text):
FUNCTION_CALL: analyzeProject|project_path={user_prefs['project_path']}
FUNCTION_CALL: migrationPlan
FUNCTION_CALL: modUpgradeAll|project_path={user_prefs['project_path']}|recipe_id=org.openrewrite.java.spring.boot3.UpgradeSpringBoot_3_2

Examples of INVALID responses:
[X] Here's what we should do next...
    FUNCTION_CALL: analyzeProject
[X] Based on the previous step...
    FUNCTION_CALL: migrationPlan
[X] FUNCTION_CALL: modUpgradeAll
    Some additional explanation
[X] Multiple responses in one reply
"""
        
        return system_prompt

    async def generate_llm_response(self, prompt: str, timeout: int = 10) -> str:
        """Generate LLM response with timeout"""
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.model.generate_content(prompt)),
                timeout=timeout
            )
            # Clean up response - take only the last line if multiple lines
            response_text = response.text.strip().split('\n')[-1]
            logger.info(f"Raw LLM Response: {response.text}")
            logger.info(f"Cleaned LLM Response: {response_text}")
            return response_text
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            raise

    def process_llm_response(self, response: str, state: MemoryState = None) -> Tuple[str, Dict[str, str]]:
        """Process LLM response and extract function call details"""
        if response.startswith("FUNCTION_CALL:"):
            parts = response[14:].split("|")
            function_name = parts[0].strip()
            params = {}
            
            # Process parameters
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle recipe_id placeholder replacement
                    if key == "recipe_id" and value == "[from_migration_plan]" and state and state.context:
                        recipe_id = state.context.get("recipe_id")
                        if not recipe_id and "last_action" in state.context:
                            # Try to extract recipe_id from last action if it was a migrationPlan response
                            last_action = state.context["last_action"]
                            if "migrationPlan" in last_action:
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
                                                    logger.info(f"Extracted recipe_id from last action: {recipe_id}")
                                except Exception as e:
                                    logger.error(f"Error extracting recipe_id from last action: {e}")
                        
                        if recipe_id:
                            value = recipe_id
                            logger.info(f"Using recipe_id: {recipe_id}")
                        else:
                            raise ValueError("No recipe_id found in memory. Please run migrationPlan first.")
                    
                    params[key] = value
            
            return ("function", {"name": function_name, "params": params})
        elif response.startswith("FINAL_ANSWER:"):
            return ("answer", {"message": response[13:].strip()})
        else:
            raise ValueError(f"Invalid response format: {response}")

    def get_upgrade_recipe_id(self, spring_boot_version: str) -> str:
        """Determine the appropriate upgrade recipe based on Spring Boot version"""
        version_map = {
            "2.7": "UpgradeSpringBoot_3_2",
            "2.6": "UpgradeSpringBoot_3_2",
            "2.5": "UpgradeSpringBoot_3_2",
            "2.4": "UpgradeSpringBoot_3_1",
            "2.3": "UpgradeSpringBoot_3_1",
            "2.2": "UpgradeSpringBoot_3_0",
            "2.1": "UpgradeSpringBoot_3_0",
            "2.0": "UpgradeSpringBoot_3_0",
            "1.5": "UpgradeSpringBoot_2_7"
        }
        
        # Get major.minor version
        version_parts = spring_boot_version.split(".")
        if len(version_parts) >= 2:
            version_key = f"{version_parts[0]}.{version_parts[1]}"
            return version_map.get(version_key, "UpgradeSpringBoot_3_2")
        return "UpgradeSpringBoot_3_2"  # Default to latest if version format is unknown

    async def make_decision(self, state: MemoryState, query: str) -> Decision:
        """Make decision based on current state and query"""
        try:
            # Create system prompt
            system_prompt = self.create_system_prompt(state)
            
            # Generate LLM response
            llm_response = await self.generate_llm_response(f"{system_prompt}\n\nQuery: {query}")
            logger.info(f"LLM Response: {llm_response}")
            
            # Process response
            response_type, data = self.process_llm_response(llm_response, state)
            
            # Create context for decision
            context = {
                "preferences": {
                    "project_path": str(state.preferences.project_path),
                    "migration_type": state.preferences.migration_type.value,
                    "release_type": state.preferences.release_type.value
                },
                "workflow": {
                    "current_step": self.current_step,
                    "total_steps": len(self.workflow_steps)
                },
                "memory": state.context or {},
                "last_action": state.context.get("last_action") if state.context else None
            }
            
            if response_type == "function":
                # Update workflow state
                self.update_workflow_state(data["name"])
                
                # Validate function exists
                if not self.is_valid_function(data["name"]):
                    raise ValueError(f"Invalid function: {data['name']}")
                
                # Map to actual function name
                data["name"] = self.get_actual_function_name(data["name"])
                
                return Decision(
                    type="function",
                    data=data,
                    context=context
                )
            else:
                return Decision(
                    type="answer",
                    data=data,
                    context=context
                )
                
        except Exception as e:
            logger.error(f"Error in make_decision: {e}")
            return Decision(
                type="answer",
                data={"message": f"Error: {str(e)}"},
                context={"error": str(e), "workflow_state": self.current_step}
            ) 