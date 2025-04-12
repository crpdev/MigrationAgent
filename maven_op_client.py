from mcp.server.fastmcp import FastMCP
import logging
import logging.handlers
import sys
import os
import json
from typing import Dict, Any

# Configure detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.handlers.RotatingFileHandler(
    'maven_op_client.log',
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

# Initialize MCP client
logger.info("Initializing Maven Op Client")
mcp = FastMCP()
logger.debug("FastMCP client initialized")

def serialize_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize MCP response to ensure JSON compatibility.
    
    Args:
        response: Raw response from MCP call
        
    Returns:
        Dict containing serialized response
    """
    try:
        # Convert any non-serializable objects to strings
        serialized = {}
        for key, value in response.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                serialized[key] = value
            else:
                serialized[key] = str(value)
        return serialized
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        return {"success": False, "error": "Response serialization failed"}

def analyze_project(project_path: str) -> Dict[str, Any]:
    """
    Analyze a Maven project to identify JDK version.
    
    Args:
        project_path: Path to the Maven project
        
    Returns:
        Dict containing analysis results
    """
    logger.info(f"Analyzing project at: {project_path}")
    
    try:
        if not os.path.exists(project_path):
            logger.error(f"Project path does not exist: {project_path}")
            return {"success": False, "error": "Project path does not exist"}

        logger.debug("Sending analyzeProject request")
        response = mcp.call_tool("analyzeProject", project_path)
        logger.debug("Received raw response")
        
        # Serialize response before returning
        serialized_response = serialize_response(response)
        logger.debug(f"Serialized response: {serialized_response}")
        return serialized_response
        
    except Exception as e:
        logger.error("Error analyzing project", exc_info=True)
        return {"success": False, "error": str(e)}

def get_migration_plan(current_jdk: str) -> Dict[str, Any]:
    """
    Get migration plan for the specified JDK version.
    
    Args:
        current_jdk: Current JDK version
        
    Returns:
        Dict containing migration plan
    """
    logger.info(f"Getting migration plan for JDK version: {current_jdk}")
    
    try:
        logger.debug("Sending migrationPlan request")
        response = mcp.call("migrationPlan", current_jdk)
        logger.debug("Received raw response")
        
        # Serialize response before returning
        serialized_response = serialize_response(response)
        logger.debug(f"Serialized response: {serialized_response}")
        return serialized_response
        
    except Exception as e:
        logger.error("Error getting migration plan", exc_info=True)
        return {"success": False, "error": str(e)}

def build_project(project_path: str) -> Dict[str, Any]:
    """
    Build a project using Moderne CLI.
    
    Args:
        project_path: Path to the project to build
        
    Returns:
        Dict containing build results
    """
    logger.info(f"Building project at: {project_path}")
    
    try:
        if not os.path.exists(project_path):
            logger.error(f"Project path does not exist: {project_path}")
            return {"success": False, "error": "Project path does not exist"}

        logger.debug("Sending modBuild request")
        response = mcp.call("modBuild", project_path)
        logger.debug("Received raw response")
        
        # Serialize response before returning
        serialized_response = serialize_response(response)
        logger.debug(f"Serialized response: {serialized_response}")
        return serialized_response
        
    except Exception as e:
        logger.error("Error building project", exc_info=True)
        return {"success": False, "error": str(e)}

def upgrade_project(project_path: str, recipe: str) -> Dict[str, Any]:
    """
    Upgrade a project using specified recipe.
    
    Args:
        project_path: Path to the project to upgrade
        recipe: Recipe ID to apply
        
    Returns:
        Dict containing upgrade results
    """
    logger.info(f"Upgrading project at: {project_path} with recipe: {recipe}")
    
    try:
        if not os.path.exists(project_path):
            logger.error(f"Project path does not exist: {project_path}")
            return {"success": False, "error": "Project path does not exist"}

        message = f"{project_path}|{recipe}"
        logger.debug(f"Sending modUpgrade request with message: {message}")
        response = mcp.call("modUpgrade", message)
        logger.debug("Received raw response")
        
        # Serialize response before returning
        serialized_response = serialize_response(response)
        logger.debug(f"Serialized response: {serialized_response}")
        return serialized_response
        
    except Exception as e:
        logger.error("Error upgrading project", exc_info=True)
        return {"success": False, "error": str(e)}

def apply_upgrade(project_path: str) -> Dict[str, Any]:
    """
    Apply the last recipe run to a project.
    
    Args:
        project_path: Path to the project
        
    Returns:
        Dict containing apply results
    """
    logger.info(f"Applying upgrade to project at: {project_path}")
    
    try:
        if not os.path.exists(project_path):
            logger.error(f"Project path does not exist: {project_path}")
            return {"success": False, "error": "Project path does not exist"}

        logger.debug("Sending modApplyUpgrade request")
        response = mcp.call("modApplyUpgrade", project_path)
        logger.debug("Received raw response")
        
        # Serialize response before returning
        serialized_response = serialize_response(response)
        logger.debug(f"Serialized response: {serialized_response}")
        return serialized_response
        
    except Exception as e:
        logger.error("Error applying upgrade", exc_info=True)
        return {"success": False, "error": str(e)}

def run_migration_workflow(project_path: str) -> None:
    """
    Run the complete migration workflow for a project.
    
    Args:
        project_path: Path to the project to migrate
    """
    logger.info(f"Starting migration workflow for project: {project_path}")
    
    try:
        # Step 1: Analyze project
        analysis_result = analyze_project(project_path)
        logger.info(f"Analysis result: {json.dumps(analysis_result, indent=2)}")
        
        if not analysis_result.get("success"):
            logger.error("Project analysis failed. Stopping workflow.")
            return
            
        # Step 2: Get migration plan
        jdk_version = analysis_result.get("jdk_version")
        migration_result = get_migration_plan(jdk_version)
        logger.info(f"Migration plan: {json.dumps(migration_result, indent=2)}")
        
        if not migration_result.get("success"):
            logger.error("Migration plan generation failed. Stopping workflow.")
            return
            
        # Step 3: Build project
        build_result = build_project(project_path)
        logger.info(f"Build result: {json.dumps(build_result, indent=2)}")
        
        if not build_result.get("success"):
            logger.error("Project build failed. Stopping workflow.")
            return
            
        # Step 4: Apply upgrade
        recipe_id = migration_result.get("recipe_id")
        upgrade_result = upgrade_project(project_path, recipe_id)
        logger.info(f"Upgrade result: {json.dumps(upgrade_result, indent=2)}")
        
        if not upgrade_result.get("success"):
            logger.error("Project upgrade failed. Stopping workflow.")
            return
            
        # Step 5: Apply changes
        apply_result = apply_upgrade(project_path)
        logger.info(f"Apply result: {json.dumps(apply_result, indent=2)}")
        
        if apply_result.get("success"):
            logger.info("Migration workflow completed successfully")
        else:
            logger.error("Failed to apply changes")
            
    except Exception as e:
        logger.error(f"Error in migration workflow: {e}", exc_info=True)

def main():
    """Main function to run test cases."""
    try:
        logger.info("Starting Maven Op Client tests")
        
        # Test cases
        test_projects = [
            "C:\\Users\\rajap\\workspace\\EAG\\Assignment5-MigrationAgent-Cursor\\test\\sample-spring-boot",
            "C:\\Users\\rajap\\workspace\\EAG\\Assignment5-MigrationAgent-Cursor\\test\\invalid-path",
        ]
        
        for project_path in test_projects:
            logger.info(f"\nTesting project: {project_path}")
            run_migration_workflow(project_path)
            
        logger.info("Tests completed successfully")
    except Exception as e:
        logger.error("Error running tests", exc_info=True)
    finally:
        logger.info("Test execution finished")

if __name__ == "__main__":
    main() 