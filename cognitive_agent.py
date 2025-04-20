from dataclasses import dataclass
from typing import Dict, Optional, Callable, Any, List, Tuple
from enum import Enum
import os
from pathlib import Path
import json
from functools import partial
from models import MemoryState
from perception import Perception
from memory import Memory
from decision import DecisionMaking
from action import Action
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"cognitive_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# Type definitions
class MigrationType(str, Enum):
    JAVA = "java"
    PYTHON = "python"

class ReleaseType(str, Enum):
    STABLE = "stable"
    RELEASE_CANDIDATE = "rc"

@dataclass(frozen=True)
class UserPreferences:
    project_path: Path
    migration_type: MigrationType
    release_type: ReleaseType

@dataclass(frozen=True)
class MemoryState:
    preferences: UserPreferences
    context: Dict[str, Any] = None

# Perception Layer
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

# Memory Layer
def save_to_memory(state: MemoryState, key: str, value: Any) -> MemoryState:
    """Pure function to update memory state"""
    new_context = dict(state.context or {})
    new_context[key] = value
    return MemoryState(preferences=state.preferences, context=new_context)

def get_from_memory(state: MemoryState, key: str) -> Optional[Any]:
    """Pure function to retrieve from memory"""
    return state.context.get(key) if state.context else None

# Decision Making Layer
def process_llm_response(response: str) -> Tuple[str, Dict[str, str]]:
    """Pure function to process LLM responses"""
    if response.startswith("FUNCTION_CALL:"):
        parts = response[14:].split("|")
        function_name = parts[0]
        params = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=")
                params[key.strip()] = value.strip()
        return ("function", {"name": function_name, "params": params})
    elif response.startswith("FINAL_ANSWER:"):
        return ("answer", {"message": response[13:].strip()})
    else:
        raise ValueError(f"Invalid response format: {response}")

def make_decision(state: MemoryState, llm_response: str) -> Dict[str, Any]:
    """Pure function for decision making"""
    response_type, data = process_llm_response(llm_response)
    
    context = {
        "preferences": {
            "project_path": str(state.preferences.project_path),
            "migration_type": state.preferences.migration_type.value,
            "release_type": state.preferences.release_type.value
        },
        "memory": state.context or {}
    }
    
    return {
        "type": response_type,
        "data": data,
        "context": context
    }

# Action Layer
def execute_action(decision: Dict[str, Any]) -> str:
    """Pure function to execute actions based on decisions"""
    if decision["type"] == "function":
        # Here you would implement the actual MCP tool calls
        function_name = decision["data"]["name"]
        params = decision["data"]["params"]
        return f"FUNCTION_CALL: {function_name}|" + "|".join(f"{k}={v}" for k, v in params.items())
    else:
        return f"FINAL_ANSWER: {decision['data']['message']}"

async def generate_llm_response(prompt: str, timeout: int = 10) -> str:
    """Generate LLM response with timeout"""
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: model.generate_content(prompt)),
            timeout=timeout
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in LLM generation: {e}")
        raise

async def cognitive_cycle(initial_state: MemoryState = None) -> None:
    """Main cognitive cycle implementing the OODA loop with MCP integration"""
    try:
        # Initialize MCP servers
        moderne_mcp_server_params = StdioServerParameters(
            command="python",
            args=["moderne_mcp_server.py"]
        )

        maven_mcp_server_params = StdioServerParameters(
            command="python",
            args=["maven_op.py"]
        )

        async with stdio_client(moderne_mcp_server_params) as (moderne_read, moderne_write), \
                stdio_client(maven_mcp_server_params) as (maven_read, maven_write):
            
            async with ClientSession(moderne_read, moderne_write) as moderne_session, \
                    ClientSession(maven_read, maven_write) as maven_session:
                
                # Initialize sessions
                await moderne_session.initialize()
                await maven_session.initialize()

                # Initialize Action layer with sessions
                action_layer = Action()
                await action_layer.initialize_sessions(moderne_session, maven_session)

                # Initialize Decision Making layer
                decision_layer = DecisionMaking()
                await decision_layer.initialize_tools(action_layer.moderne_tools, action_layer.maven_tools)

                # Perception - Get user preferences
                preferences = Perception.get_user_input()
                
                # Initialize Memory
                state = Memory.create_initial_state(preferences) if not initial_state else initial_state
                
                # Initial query based on preferences
                initial_query = f"""Analyze the Java project at {preferences.project_path}. Then create a migration plan to get the recipe_id. Then upgrade by passing the recipe_id. Then apply the last recipe run to all projects by performing mod_apply_upgrade_all"""
                
                # Main cognitive cycle
                iteration = 0
                max_iterations = 3
                current_query = initial_query
                
                while iteration < max_iterations:
                    logger.info(f"\n--- Iteration {iteration + 1} ---")
                    logger.info(f"Query: {current_query}")
                    
                    # Decision Making with LLM
                    decision = await decision_layer.make_decision(state, current_query)
                    
                    # Action
                    result = await action_layer.execute_action(decision)
                    
                    # Update Memory
                    state = Memory.save_to_memory(state, "last_action", result)
                    
                    # Update query for next iteration
                    if result.startswith("FINAL_ANSWER:"):
                        print(result)
                        break
                    else:
                        print(result)
                        current_query = f"Previous action: {result}\nWhat should I do next to continue the migration process?"
                    
                    iteration += 1
                
                if iteration >= max_iterations:
                    logger.warning("Reached maximum iterations")
                    print("FINAL_ANSWER: [Maximum iterations reached. Please review the migration progress.]")
                
    except Exception as e:
        logger.error(f"Error in cognitive cycle: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(cognitive_cycle()) 