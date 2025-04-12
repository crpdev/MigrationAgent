from mcp.server.fastmcp import FastMCP
import subprocess
import logging
import logging.handlers
import os
import sys
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.handlers.RotatingFileHandler(
    'moderne_mcp.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
console_handler.setFormatter(log_format)
file_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Constants
MODERNE_CLI_JAR = "C:\\Users\\rajap\\tools\\moderne-cli-3.36.1.jar"
PROJECTS_BASE_PATH = os.getenv('PROJECTS_BASE_PATH')
logger.info(f"Moderne CLI JAR path: {MODERNE_CLI_JAR}")
logger.info(f"Projects base path: {PROJECTS_BASE_PATH}")

# Initialize MCP server
logger.info("Initializing Moderne MCP server")
mcp = FastMCP("ModerneMCP")

def get_full_project_path(project_name: str) -> str:
    """Get the full project path from the project name."""
    if not PROJECTS_BASE_PATH:
        logger.error("PROJECTS_BASE_PATH environment variable not set")
        raise ValueError("PROJECTS_BASE_PATH environment variable not set")
    return os.path.join(PROJECTS_BASE_PATH, project_name)

def verify_jar_exists():
    """Verify that the Moderne CLI JAR file exists."""
    if not os.path.exists(MODERNE_CLI_JAR):
        logger.error(f"Moderne CLI JAR not found at: {MODERNE_CLI_JAR}")
        raise FileNotFoundError(f"Moderne CLI JAR not found: {MODERNE_CLI_JAR}")
    logger.debug("Moderne CLI JAR file verified")

def run_moderne_command(command: list) -> dict:
    """Run a Moderne CLI command and return the result."""
    logger.debug(f"Executing Moderne CLI command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Command executed successfully")
            logger.debug(f"Command output: {result.stdout}")
        else:
            logger.error(f"Command failed with return code: {result.returncode}")
            logger.error(f"Error output: {result.stderr}")
            
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        logger.error("Error executing Moderne CLI command", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

def get_all_projects() -> List[str]:
    """Get list of all projects in PROJECTS_BASE_PATH."""
    if not PROJECTS_BASE_PATH:
        logger.error("PROJECTS_BASE_PATH environment variable not set")
        raise ValueError("PROJECTS_BASE_PATH environment variable not set")
        
    try:
        projects = [d for d in os.listdir(PROJECTS_BASE_PATH) 
                   if os.path.isdir(os.path.join(PROJECTS_BASE_PATH, d))]
        logger.info(f"Found {len(projects)} projects in {PROJECTS_BASE_PATH}")
        logger.debug(f"Projects found: {projects}")
        return projects
    except Exception as e:
        logger.error(f"Error reading projects directory: {e}", exc_info=True)
        raise

def verify_project_exists(project_name: str) -> bool:
    """Verify that a project exists in PROJECTS_BASE_PATH."""
    try:
        project_path = get_full_project_path(project_name)
        exists = os.path.exists(project_path)
        if exists:
            logger.debug(f"Project {project_name} found at {project_path}")
        else:
            logger.warning(f"Project {project_name} not found at {project_path}")
        return exists
    except Exception as e:
        logger.error(f"Error verifying project {project_name}", exc_info=True)
        return False

@mcp.tool(name="modBuildAll", description="Build all projects using Moderne CLI")
def mod_build_all() -> dict:
    """Build all projects in PROJECTS_BASE_PATH using Moderne CLI."""
    logger.info("Starting modBuildAll")
    
    try:
        projects = get_all_projects()
        if not projects:
            logger.warning("No projects found to build")
            return {"success": False, "error": "No projects found"}
            
        results = []
        success_count = 0
        
        for project in projects:
            logger.info(f"Building project: {project}")
            result = mod_build(project)
            results.append({
                "project": project,
                "success": result["success"],
                "error": result.get("error", None)
            })
            if result["success"]:
                success_count += 1
                
        return {
            "success": success_count > 0,
            "total_projects": len(projects),
            "successful_builds": success_count,
            "results": results
        }
        
    except Exception as e:
        logger.error("Error in modBuildAll", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp.tool(name="modUpgradeAll", description="Upgrade all projects using specified recipe")
def mod_upgrade_all(recipe: str) -> dict:
    """Upgrade all projects using specified recipe."""
    logger.info(f"Starting modUpgradeAll with recipe: {recipe}")
    
    try:
        projects = get_all_projects()
        if not projects:
            logger.warning("No projects found to upgrade")
            return {"success": False, "error": "No projects found"}
            
        results = []
        success_count = 0
        
        for project in projects:
            logger.info(f"Upgrading project: {project}")
            result = mod_upgrade(project, recipe)
            results.append({
                "project": project,
                "success": result["success"],
                "error": result.get("error", None)
            })
            if result["success"]:
                success_count += 1
                
        return {
            "success": success_count > 0,
            "total_projects": len(projects),
            "successful_upgrades": success_count,
            "results": results
        }
        
    except Exception as e:
        logger.error("Error in modUpgradeAll", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp.tool(name="modApplyUpgradeAll", description="Apply the last recipe run to all projects")
def mod_apply_upgrade_all() -> dict:
    """Apply the last recipe run to all projects using Moderne CLI."""
    logger.info("Starting modApplyUpgradeAll")
    
    try:
        projects = get_all_projects()
        if not projects:
            logger.warning("No projects found to apply upgrades")
            return {"success": False, "error": "No projects found"}
            
        results = []
        success_count = 0
        
        for project in projects:
            logger.info(f"Applying upgrade to project: {project}")
            result = mod_apply_upgrade(project)
            results.append({
                "project": project,
                "success": result["success"],
                "error": result.get("error", None)
            })
            if result["success"]:
                success_count += 1
                
        return {
            "success": success_count > 0,
            "total_projects": len(projects),
            "successful_applies": success_count,
            "results": results
        }
        
    except Exception as e:
        logger.error("Error in modApplyUpgradeAll", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp.tool(name="modBuild", description="Build a project using Moderne CLI")
def mod_build(project_name: str) -> dict:
    """Build a project using Moderne CLI."""
    logger.info(f"Starting modBuild for project: {project_name}")
    
    try:
        verify_jar_exists()
        
        if not verify_project_exists(project_name):
            return {"success": False, "error": f"Project not found: {project_name}"}
            
        project_path = get_full_project_path(project_name)
        command = ["java", "-jar", MODERNE_CLI_JAR, "build", project_path]
        return run_moderne_command(command)
        
    except Exception as e:
        logger.error("Error in modBuild", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp.tool(name="modUpgrade", description="Upgrade a project using specified recipe")
def mod_upgrade(project_name: str, recipe: str) -> dict:
    """Upgrade a project using specified recipe."""
    try:
        logger.info(f"Starting modUpgrade for project: {project_name}")
        logger.info(f"Using recipe: {recipe}")
        
        verify_jar_exists()
        
        if not verify_project_exists(project_name):
            return {"success": False, "error": f"Project not found: {project_name}"}
            
        project_path = get_full_project_path(project_name)
        command = ["java", "-jar", MODERNE_CLI_JAR, "run", project_path, "--recipe", recipe]
        return run_moderne_command(command)
        
    except Exception as e:
        logger.error("Error in modUpgrade", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp.tool(name="modApplyUpgrade", description="Apply the last recipe run using Moderne CLI")
def mod_apply_upgrade(project_name: str) -> dict:
    """Apply the last recipe run using Moderne CLI."""
    logger.info(f"Starting modApplyUpgrade for project: {project_name}")
    
    try:
        verify_jar_exists()
        
        if not verify_project_exists(project_name):
            return {"success": False, "error": f"Project not found: {project_name}"}
            
        project_path = get_full_project_path(project_name)
        command = ["java", "-jar", MODERNE_CLI_JAR, "git", "apply", project_path, "--last-recipe-run"]
        return run_moderne_command(command)
        
    except Exception as e:
        logger.error("Error in modApplyUpgrade", exc_info=True)
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    logger.info("Starting Moderne MCP server")
    mcp.run(transport="stdio")
    logger.info("Moderne MCP server stopped") 