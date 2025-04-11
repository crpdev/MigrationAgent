from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

@dataclass
class Message:
    role: str
    content: str
    
@dataclass
class Tool:
    name: str
    description: str
    function: Callable

class FastMCP:
    """
    A lightweight implementation of a Multi-Call Protocol (MCP) system
    for handling tool-based interactions in LLM agents.
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        
    def register_tool(self, tool: Tool):
        """Register a tool with the MCP system."""
        self.tools[tool.name] = tool
        
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a registered tool with the provided arguments."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' is not registered")
        
        tool = self.tools[tool_name]
        return tool.function(**kwargs)
    
    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Get descriptions of all registered tools in a format suitable for LLMs."""
        tool_descriptions = []
        for name, tool in self.tools.items():
            tool_descriptions.append({
                "name": name,
                "description": tool.description
            })
        return tool_descriptions
    
    def process_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Process a message to identify and execute tool calls.
        Returns the result of the tool execution or None if no tool call was detected.
        """
        # This is a simplified implementation
        # In a real implementation, you would parse the message to identify tool calls
        # and extract the arguments
        
        # For now, we'll just return None to indicate no tool call was detected
        return None 