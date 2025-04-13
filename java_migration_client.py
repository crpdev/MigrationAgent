import os
import asyncio
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import google.generativeai as genai
import win32api
import win32con

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"java_migration_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

async def generate_with_timeout(prompt, timeout=10):
    """Generate content with a timeout"""
    logger.info("Starting LLM generation...")
    
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            ),
            timeout=timeout
        )
        logger.info("LLM generation completed")
        logger.info(f"LLM Response:\n{response.text}")
        return response
    except Exception as e:
        logger.error(f"Error in LLM generation: {e}")
        raise

async def main():
    logger.info("Starting main execution...")
    try:
        # Create server connections for Maven and Moderne
        logger.info("Establishing connections to MCP servers...")
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
            
            logger.info("Connections established, creating sessions...")
            async with ClientSession(moderne_read, moderne_write) as moderne_session, \
                    ClientSession(maven_read, maven_write) as maven_session:
                
                logger.info("Sessions created, initializing...")
                await moderne_session.initialize()
                await maven_session.initialize()
                
                # Get available tools from all servers
                logger.info("Requesting tool lists...")
                moderne_tools_result = await moderne_session.list_tools()
                maven_tools_result = await maven_session.list_tools()
                
                moderne_tools = moderne_tools_result.tools
                maven_tools = maven_tools_result.tools
                
                logger.info(f"Successfully retrieved {len(moderne_tools)} Moderne MCP tools")
                logger.info(f"Successfully retrieved {len(maven_tools)} Maven MCP tools")   


                # Create system prompt with available tools
                logger.info("Creating system prompt...")
                
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
                        logger.info(f"Added description for Math tool: {tool_desc}")
                    except Exception as e:
                        logger.error(f"Error processing Math tool {i}: {e}")
                        tools_description.append(f"{i+1}. Error processing tool")

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
                        logger.info(f"Added description for Maven tool: {tool_desc}")
                    except Exception as e:
                        logger.error(f"Error processing Maven tool {i}: {e}")
                        tools_description.append(f"{i+1}. Error processing tool")

                tools_description = "\n".join(tools_description)
                logger.info("Successfully created tools description")

                print("Java/Maven Migration Agent initialized. Type 'exit' to quit.")
                
                system_prompt = f"""You are an java migration assistant that can perform pom file analysis operation.

Available tools:
{tools_description}

Respond with EXACTLY ONE of these formats:
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   The parameters must match the required input types for the function.
   
   Example: for analyzeProject(), use:
   FUNCTION_CALL: analyzeProject

   Example: for migrationPlan(), use:
   FUNCTION_CALL: migrationPlan

   Example: For mod_build_all(), use:
   FUNCTION_CALL: mod_build_all

   Example: For mod_upgrade_all(), use:
   FUNCTION_CALL: mod_upgrade_all
   
   Example: For mod_apply_upgrade_all(), use:
   FUNCTION_CALL: mod_apply_upgrade_all

2. For final answers:
   FINAL_ANSWER: [your response]

DO NOT include multiple responses. Give ONE response at a time.
Make sure to provide parameters in the correct order as specified in the function signature."""

                # Initial query for math operation
                projects_base_path = os.getenv("PROJECTS_BASE_PATH")
                query = f"Perform an analysis of the projects. Then send spring_boot_version to decide the migration plan. Then perform mod_build_all. Then perform mod_upgrade_all. Then perform mod_apply_upgrade_all."

                logger.info(f"Starting with query: {query}")
                
                # Use global iteration variables
                iteration = 0
                max_iterations = 4
                last_response = None
                iteration_response = []
                
                while iteration < max_iterations:
                    logger.info(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"
                        logger.info(f"Updated query: {current_query}")

                    # Get model's response with timeout
                    logger.info("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(prompt)
                        response_text = response.text.strip()
                        logger.info(f"LLM Response: {response_text}")
                    except Exception as e:
                        logger.error(f"Failed to get LLM response: {e}")
                        break
                    logger.info(f"IM HERE BEFORE CHECKING FUNCTIONS: {response_text.startswith("FUNCTION_CALL:")}")
                    if response_text.startswith("FUNCTION_CALL:"):
                        logger.info(f"Function call detected: {response_text}")
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        length = len(params)
                        logger.info(f"Length of params: {length}")
                        logger.info(f"Calling function {func_name} with params {params}")
                        try:
                            # Determine which session to use based on the function name
                            if func_name in [tool.name for tool in moderne_tools]:
                                if length == 0:
                                    result = await moderne_session.call_tool(func_name)
                                else:
                                    result = await moderne_session.call_tool(func_name, arguments={"arg1": "value"})
                            elif func_name in [tool.name for tool in maven_tools]:
                                if length == 0:
                                    result = await maven_session.call_tool(func_name)
                                else:
                                    result = await maven_session.call_tool(func_name, params)
                            else:
                                logger.error(f"Unknown function: {func_name}")
                                continue
                            
                            logger.info(f"Function call result: {result}")
                            last_response = result
                            iteration_response.append(result.content[0].text)
                            
                        except Exception as e:
                            logger.error(f"Error calling function {func_name}: {e}")
                            iteration_response.append(f"Error: {str(e)}")
                    
                    elif response_text.startswith("FINAL_ANSWER:"):
                        logger.info("Received final answer")
                        last_response = response_text
                        iteration_response.append(response_text)
                        break
                    
                    iteration += 1
                    
                    # Break if we've completed all steps
                    # if math_result and email_sent:
                    #     break
                
                logger.info("Workflow completed")
                logger.info(f"Final responses: {iteration_response}")
                
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 