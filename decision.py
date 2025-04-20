from typing import Tuple, Dict, Any
import logging
from datetime import datetime
import os
import google.generativeai as genai
import asyncio
from models import MemoryState, Decision

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
        # Map common function names to actual tool names
        self.function_map = {
            'analyzeproject': 'analyzeProject',
            'migrationplan': 'migrationPlan',
            'modbuildall': 'modBuildAll',
            'modupgradeall': 'modUpgradeAll',
            'modapplyupgradeall': 'modApplyUpgradeAll',
            'modbuild': 'modBuild',
            'modupgrade': 'modUpgrade',
            'modapplyupgrade': 'modApplyUpgrade'
        }

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
        
        system_prompt = f"""You are a Java migration assistant that helps with project analysis and migration.

Current User Preferences:
- Project Path: {user_prefs['project_path']}
- Migration Type: {user_prefs['migration_type']}
- Release Type: {user_prefs['release_type']}

Available tools:
{self.tools_description}

You must respond with EXACTLY ONE line in one of these formats:
1. For function calls:
   FUNCTION_CALL: function_name|param1=value1|param2=value2|...
   
2. For final answers:
   FINAL_ANSWER: [your response]

IMPORTANT:
- Think before responding
- Verify each step
- Follow the exact format
- No additional text or explanations
- One response per iteration
- Validate all inputs before use
- Parameters must match the required input types for the function
- Use EXACT function names as shown in the tools list

Example responses:
FUNCTION_CALL: analyzeProject
FUNCTION_CALL: migrationPlan
FUNCTION_CALL: modBuildAll
FUNCTION_CALL: modUpgradeAll|recipe_id=UpgradeSpringBoot_3_2
FUNCTION_CALL: modApplyUpgradeAll
FINAL_ANSWER: [Migration completed successfully]"""
        
        return system_prompt

    async def generate_llm_response(self, prompt: str, timeout: int = 10) -> str:
        """Generate LLM response with timeout"""
        try:
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: self.model.generate_content(prompt)),
                timeout=timeout
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            raise

    def process_llm_response(self, response: str) -> Tuple[str, Dict[str, str]]:
        """Process LLM responses into structured format"""
        if response.startswith("FUNCTION_CALL:"):
            parts = response[14:].split("|")
            function_name = parts[0].strip()
            
            # Get actual function name and validate
            actual_function_name = self.get_actual_function_name(function_name)
            if not self.is_valid_function(actual_function_name):
                raise ValueError(f"Invalid function name: {function_name}")
            
            params = {}
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=")
                    params[key.strip()] = value.strip()
            return ("function", {"name": actual_function_name, "params": params})
        elif response.startswith("FINAL_ANSWER:"):
            return ("answer", {"message": response[13:].strip()})
        else:
            raise ValueError(f"Invalid response format: {response}")

    async def make_decision(self, state: MemoryState, query: str) -> Decision:
        """Generate decision using LLM based on state and query"""
        try:
            # Create system prompt with current context
            system_prompt = self.create_system_prompt(state)
            
            # Combine system prompt and query
            full_prompt = f"{system_prompt}\n\nQuery: {query}"
            logger.info(f"Sending prompt to LLM:\n{full_prompt}")
            
            # Get LLM response
            llm_response = await self.generate_llm_response(full_prompt)
            logger.info(f"LLM Response: {llm_response}")
            
            # Process response
            response_type, data = self.process_llm_response(llm_response)
            
            # Create context
            context = {
                "preferences": {
                    "project_path": str(state.preferences.project_path),
                    "migration_type": state.preferences.migration_type.value,
                    "release_type": state.preferences.release_type.value
                },
                "memory": state.context
            }
            
            return Decision(
                type=response_type,
                data=data,
                context=context
            )
            
        except Exception as e:
            logger.error(f"Error in make_decision: {e}")
            # Return error decision
            return Decision(
                type="answer",
                data={"message": f"Error in decision making: {str(e)}"},
                context={"error": str(e)}
            ) 