from models import Decision
from typing import Any, Dict, Optional
import asyncio
import logging
from mcp import ClientSession
from datetime import datetime
import os

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

class Action:
    def __init__(self):
        self.moderne_session: Optional[ClientSession] = None
        self.maven_session: Optional[ClientSession] = None
        self.moderne_tools: list = []
        self.maven_tools: list = []

    async def initialize_sessions(self, moderne_session: ClientSession, maven_session: ClientSession):
        """Initialize MCP sessions and cache available tools"""
        self.moderne_session = moderne_session
        self.maven_session = maven_session
        
        # Get available tools
        moderne_tools_result = await moderne_session.list_tools()
        maven_tools_result = await maven_session.list_tools()
        
        self.moderne_tools = moderne_tools_result.tools
        self.maven_tools = maven_tools_result.tools
        
        logger.info(f"Initialized with {len(self.moderne_tools)} Moderne tools and {len(self.maven_tools)} Maven tools")

    def parse_function_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate function parameters"""
        if not params:
            return {}
            
        result = {}
        for key, value in params.items():
            # Handle nested parameters if needed
            if isinstance(value, dict):
                result[key] = self.parse_function_params(value)
            else:
                result[key] = value
        return result

    async def execute_action(self, decision: Decision) -> str:
        """Execute actions based on decisions using MCP tools"""
        try:
            if decision.type == "function":
                function_name = decision.data["name"]
                params = self.parse_function_params(decision.data.get("params", {}))
                
                # Determine which session to use
                if function_name in [tool.name for tool in self.moderne_tools]:
                    session = self.moderne_session
                    logger.info(f"Using Moderne session for {function_name}")
                elif function_name in [tool.name for tool in self.maven_tools]:
                    session = self.maven_session
                    logger.info(f"Using Maven session for {function_name}")
                else:
                    error_msg = f"Unknown function: {function_name}"
                    logger.error(error_msg)
                    return f"FINAL_ANSWER: Error - {error_msg}"

                # Execute the tool
                try:
                    if params:
                        result = await session.call_tool(function_name, arguments=params)
                    else:
                        result = await session.call_tool(function_name)
                    
                    logger.info(f"Tool execution result: {result}")
                    return f"FUNCTION_CALL: {function_name}|" + "|".join(f"{k}={v}" for k, v in params.items())
                
                except Exception as e:
                    error_msg = f"Error executing {function_name}: {str(e)}"
                    logger.error(error_msg)
                    return f"FINAL_ANSWER: Error - {error_msg}"
            else:
                return f"FINAL_ANSWER: {decision.data['message']}"
                
        except Exception as e:
            error_msg = f"Error in execute_action: {str(e)}"
            logger.error(error_msg)
            return f"FINAL_ANSWER: Error - {error_msg}"

    @staticmethod
    def execute_mcp_tool(function_name: str, params: dict) -> Any:
        """Execute MCP tool based on function name and parameters"""
        # Implement actual MCP tool calls here
        pass 