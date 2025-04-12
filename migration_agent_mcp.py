from fastmcp import FastMCP, Tool, Message
import logging
from migration_agent import MavenProjectAnalyzer, MigrationAgent
import json

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationAgentMCP:
    def __init__(self):
        self.mcp = FastMCP()
        self.maven_analyzer = MavenProjectAnalyzer(".")  # Default path, will be updated per request
        self.migration_agent = MigrationAgent()
        self.setup_tools()

    def setup_tools(self):
        """Register all MCP tools."""
        self.mcp.register_tool(
            Tool(
                name="analyzeMavenProject",
                description="Analyze a Maven project and return key information about versions and dependencies",
                function=self.analyze_maven_project_impl
            )
        )

        self.mcp.register_tool(
            Tool(
                name="generateMigrationPlan",
                description="Generate a detailed migration plan based on project analysis",
                function=self.generate_migration_plan_impl
            )
        )

        self.mcp.register_tool(
            Tool(
                name="runModerneCli",
                description="Run the moderne-cli tool to find and execute migration recipes",
                function=self.run_moderne_cli_impl
            )
        )

        self.mcp.register_tool(
            Tool(
                name="validateMigrationStep",
                description="Validate a migration step using LLM",
                function=self.validate_migration_step_impl
            )
        )

    def analyze_maven_project_impl(self, message: Message) -> dict:
        """Implementation of analyzeMavenProject tool."""
        try:
            project_path = message.content
            self.maven_analyzer = MavenProjectAnalyzer(project_path)
            analysis_result = self.maven_analyzer.analyze_project()
            return {
                "success": True,
                "analysis": analysis_result
            }
        except Exception as e:
            logger.error(f"Error in analyze_maven_project: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_migration_plan_impl(self, message: Message) -> dict:
        """Implementation of generateMigrationPlan tool."""
        try:
            analysis_json = json.loads(message.content)
            migration_plan = self.migration_agent.generate_migration_plan(analysis_json)
            return {
                "success": True,
                "migration_plan": migration_plan
            }
        except Exception as e:
            logger.error(f"Error in generate_migration_plan: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def run_moderne_cli_impl(self, message: Message) -> dict:
        """Implementation of runModerneCli tool."""
        try:
            migration_plan_keyword = message.content
            result = self.migration_agent.run_moderne_cli(migration_plan_keyword)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error in run_moderne_cli: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def validate_migration_step_impl(self, message: Message) -> dict:
        """Implementation of validateMigrationStep tool."""
        try:
            data = json.loads(message.content)
            step_result = data.get("step_result")
            step_name = data.get("step_name")
            
            validation_result = self.migration_agent.validate_migration_step(step_result, step_name)
            return {
                "success": True,
                "should_proceed": validation_result
            }
        except Exception as e:
            logger.error(f"Error in validate_migration_step: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def start(self, host: str = "localhost", port: int = 21000):
        """Start the MCP server."""
        logger.info(f"Starting Migration Agent MCP Server on {host}:{port}")
        self.mcp.start(host=host, port=port)

def main():
    server = MigrationAgentMCP()
    server.start()

if __name__ == "__main__":
    main() 