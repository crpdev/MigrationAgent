from mcp.server.fastmcp import FastMCP
import logging
import logging.handlers
import sys
import os
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any, Union
import google.generativeai as genai
from google.generativeai import GenerativeModel
from dotenv import load_dotenv
from pydantic import BaseModel

class ProjectDetails(BaseModel):
    success: bool
    project_name: str
    jdk_version: Optional[str]
    spring_boot_version: Optional[str]
    all_jdk_versions: List[str]
    all_spring_boot_versions: List[str]

class ProjectAnalysis(BaseModel):
    success: bool
    projects: List[ProjectDetails]
    total_projects: int
    analyzed_projects: int

# Load environment variables
load_dotenv()

# Configure detailed logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Remove any existing handlers to avoid duplicate logs
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)

file_handler = logging.handlers.RotatingFileHandler(
    'maven_op.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
console_handler.setFormatter(log_format)
file_handler.setFormatter(log_format)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Initialize FastMCP with debug logging
logger.info("Initializing Maven Operation MCP Server")
mcp = FastMCP("MavenOp")
logger.info("FastMCP instance created")

# Get PROJECTS_BASE_PATH from environment
PROJECTS_BASE_PATH = os.getenv('PROJECTS_BASE_PATH')
logger.info(f"Projects base path: {PROJECTS_BASE_PATH}")

def get_full_project_path(project_name: str) -> str:
    """Get the full project path from the project name."""
    if not PROJECTS_BASE_PATH:
        logger.error("PROJECTS_BASE_PATH environment variable not set")
        raise ValueError("PROJECTS_BASE_PATH environment variable not set")
    return os.path.join(PROJECTS_BASE_PATH, project_name)

def serialize_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize MCP response to ensure JSON compatibility.
    
    Args:
        response: Raw response from MCP call
        
    Returns:
        Dict containing serialized response
    """
    try:
        logger.debug(f"Serializing response: {response}")
        # Convert any non-serializable objects to strings
        serialized = {}
        for key, value in response.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                serialized[key] = value
            elif isinstance(value, list):
                # Handle lists by serializing each element
                serialized[key] = [
                    str(item) if not isinstance(item, (str, int, float, bool, type(None)))
                    else item
                    for item in value
                ]
            else:
                serialized[key] = str(value)
        logger.debug(f"Serialized response: {serialized}")
        return serialized
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        return {"success": False, "error": "Response serialization failed"}

def find_pom_files(project_path: str) -> List[str]:
    """Find all pom.xml files in the project directory."""
    logger.debug(f"Searching for pom.xml files in: {project_path}")
    pom_files = []
    for root, dirs, files in os.walk(project_path):
        logger.debug(f"Scanning directory: {root}")
        if "pom.xml" in files:
            pom_path = os.path.join(root, "pom.xml")
            pom_files.append(pom_path)
            logger.debug(f"Found pom.xml at: {pom_path}")
    
    logger.info(f"Total pom.xml files found: {len(pom_files)}")
    return pom_files

def extract_jdk_version(pom_path: str) -> Optional[str]:
    """Extract JDK version from a pom.xml file."""
    logger.debug(f"Attempting to extract JDK version from: {pom_path}")
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
        logger.debug("Successfully parsed pom.xml")

        # Check various locations for Java version
        locations = [
            ".//mvn:properties/mvn:java.version",
            ".//mvn:properties/mvn:maven.compiler.source",
            ".//mvn:build/mvn:plugins//mvn:configuration/mvn:source",
        ]

        for xpath in locations:
            logger.debug(f"Checking xpath: {xpath}")
            version_elem = root.find(xpath, ns)
            if version_elem is not None and version_elem.text:
                version = version_elem.text
                logger.info(f"Found JDK version {version} at xpath {xpath}")
                return version

        logger.warning(f"No JDK version found in {pom_path}")
        return None
    except Exception as e:
        logger.error(f"Error parsing pom.xml at {pom_path}: {str(e)}", exc_info=True)
        return None

def extract_spring_boot_version(pom_path: str) -> Optional[str]:
    """Extract Spring Boot version from a pom.xml file."""
    logger.debug(f"Attempting to extract Spring Boot version from: {pom_path}")
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
        logger.debug("Successfully parsed pom.xml")

        # Check parent version first
        parent = root.find(".//mvn:parent", ns)
        if parent is not None:
            group_id = parent.find("mvn:groupId", ns)
            artifact_id = parent.find("mvn:artifactId", ns)
            version = parent.find("mvn:version", ns)
            
            if (group_id is not None and group_id.text == "org.springframework.boot" and 
                artifact_id is not None and artifact_id.text == "spring-boot-starter-parent" and
                version is not None):
                logger.info(f"Found Spring Boot version {version.text} in parent")
                return version.text

        # Check dependencies
        dependencies = root.findall(".//mvn:dependencies/mvn:dependency", ns)
        for dep in dependencies:
            group_id = dep.find("mvn:groupId", ns)
            artifact_id = dep.find("mvn:artifactId", ns)
            version = dep.find("mvn:version", ns)
            
            if (group_id is not None and group_id.text == "org.springframework.boot" and
                artifact_id is not None and "spring-boot" in artifact_id.text and
                version is not None):
                logger.info(f"Found Spring Boot version {version.text} in dependencies")
                return version.text

        logger.warning(f"No Spring Boot version found in {pom_path}")
        return None
    except Exception as e:
        logger.error(f"Error extracting Spring Boot version: {str(e)}", exc_info=True)
        return None

def analyze_project_impl(project_name: str) -> Dict[str, Any]:
    """
    Analyze a Maven project to identify JDK and Spring Boot versions.
    
    Args:
        project_name: Name of the Maven project
        
    Returns:
        Dict containing analysis results with JDK and Spring Boot versions
    """
    logger.info(f"Starting project analysis for: {project_name}")
    
    try:
        project_path = get_full_project_path(project_name)
        if not os.path.exists(project_path):
            logger.error(f"Project path does not exist: {project_path}")
            return {"success": False, "error": "Project path does not exist"}

        pom_files = find_pom_files(project_path)
        if not pom_files:
            logger.error("No pom.xml files found")
            return {"success": False, "error": "No pom.xml files found in the project"}

        # Extract versions from all pom files
        jdk_versions = set()
        spring_boot_versions = set()
        
        for pom_file in pom_files:
            logger.debug(f"Processing pom file: {pom_file}")
            
            # Get JDK version
            jdk_version = extract_jdk_version(pom_file)
            if jdk_version:
                jdk_versions.add(jdk_version)
                logger.debug(f"Added JDK version {jdk_version} to versions set")
            
            # Get Spring Boot version
            spring_version = extract_spring_boot_version(pom_file)
            if spring_version:
                spring_boot_versions.add(spring_version)
                logger.debug(f"Added Spring Boot version {spring_version} to versions set")

        # Prepare response
        response = {"success": True}
        
        # Add JDK version if found
        if jdk_versions:
            min_jdk = min(jdk_versions)
            response["jdk_version"] = min_jdk
            logger.info(f"Selected JDK version: {min_jdk}")
        else:
            logger.warning("No JDK versions found")
            response["jdk_version"] = None

        # Add Spring Boot version if found
        if spring_boot_versions:
            min_spring = min(spring_boot_versions)
            response["spring_boot_version"] = min_spring
            logger.info(f"Selected Spring Boot version: {min_spring}")
        else:
            logger.warning("No Spring Boot versions found")
            response["spring_boot_version"] = None

        # Add all found versions for reference
        response["all_jdk_versions"] = list(jdk_versions)
        response["all_spring_boot_versions"] = list(spring_boot_versions)
        
        logger.info("Analysis complete")
        return response
        
    except Exception as e:
        logger.error("Error during project analysis", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp.tool(name="analyzeProject", description="Analyze a Maven project to identify JDK version")
def analyze_project() -> dict:
    """
    Analyze a Maven project to identify JDK version.
    Reads the project name from PROJECTS_BASE_PATH directory.
    """
    try:
        logger.info("=== Starting analyzeProject ===")
        
        if not PROJECTS_BASE_PATH:
            logger.error("PROJECTS_BASE_PATH environment variable not set")
            return {"success": False, "error": "PROJECTS_BASE_PATH environment variable not set"}
            
        if not os.path.exists(PROJECTS_BASE_PATH):
            logger.error(f"Projects base path does not exist: {PROJECTS_BASE_PATH}")
            return {"success": False, "error": f"Projects base path does not exist: {PROJECTS_BASE_PATH}"}
            
        # Get list of directories in PROJECTS_BASE_PATH
        try:
            projects = [d for d in os.listdir(PROJECTS_BASE_PATH) 
                       if os.path.isdir(os.path.join(PROJECTS_BASE_PATH, d))]
        except Exception as e:
            logger.error(f"Error reading projects directory: {e}", exc_info=True)
            return {"success": False, "error": f"Error reading projects directory: {str(e)}"}
            
        if not projects:
            logger.error("No projects found in projects directory")
            return {"success": False, "error": "No projects found in projects directory"}
            
        logger.info(f"Found projects: {projects}")
        
        # Analyze each project
        results = []
        for project_name in projects:
            logger.info(f"Analyzing project: {project_name}")
            result = analyze_project_impl(project_name)
            if result.get("success", False):
                result["project_name"] = project_name
                results.append(result)
            else:
                logger.warning(f"Failed to analyze project {project_name}: {result.get('error', 'Unknown error')}")
        
        if not results:
            logger.error("No projects could be successfully analyzed")
            return {"success": False, "error": "No projects could be successfully analyzed"}
            
        # Combine results
        combined_result = {
            "success": True,
            "projects": results,
            "total_projects": len(projects),
            "analyzed_projects": len(results)
        }
        
        serialized = serialize_response(combined_result)
        logger.debug(f"Analysis results after serialization: {serialized}")
        
        logger.info("=== Completed analyzeProject ===")
        return serialized
        
    except Exception as e:
        logger.error("Error in analyzeProject", exc_info=True)
        return {"success": False, "error": str(e)}

def get_latest_java_version(llm: GenerativeModel) -> str:
    """Use Gemini LLM to identify the latest stable Java version."""
    logger.debug("Requesting latest Java version from LLM")
    try:
        prompt = """What is the latest stable version of Java/JDK available for production use?
        Respond with ONLY the version number (e.g., '21' for Java 21), nothing else."""
        
        logger.debug(f"Sending prompt to LLM: {prompt}")
        response = llm.generate_content(prompt)
        latest_version = response.text.strip()
        logger.info(f"LLM identified latest Java version: {latest_version}")
        return latest_version
    except Exception as e:
        logger.error("Error getting latest Java version from LLM", exc_info=True)
        logger.info("Falling back to default version: 21")
        return "21"

def get_latest_spring_boot_version(llm: GenerativeModel) -> str:
    """Use Gemini LLM to identify the latest stable Spring Boot version."""
    logger.debug("Requesting latest Spring Boot version from LLM")
    try:
        prompt = """What is the latest stable version of Spring Boot available for production use?
        Respond with ONLY the version number (e.g., '3.2.1'), nothing else."""
        
        logger.debug(f"Sending prompt to LLM: {prompt}")
        response = llm.generate_content(prompt)
        latest_version = response.text.strip()
        logger.info(f"LLM identified latest Spring Boot version: {latest_version}")
        return latest_version
    except Exception as e:
        logger.error("Error getting latest Spring Boot version from LLM", exc_info=True)
        logger.info("Falling back to default version: 3.2.1")
        return "3.2.1"

def score_recipe_match(recipe: Dict, target_version: str, is_spring_boot: bool, llm: GenerativeModel) -> float:
    """Use LLM to score how well a recipe matches the migration goal."""
    logger.debug(f"Scoring recipe match for {'Spring Boot' if is_spring_boot else 'Java'} version: {target_version}")
    logger.debug(f"Recipe being scored: {recipe['name']}")
    
    try:
        prompt = f"""As a Java and Spring Boot migration expert, score how well this recipe matches the migration goal.
        
        Migration Goal: {'Migrate to Spring Boot' if is_spring_boot else 'Migrate to Java'} {target_version}
        
        Recipe:
        {json.dumps(recipe, indent=2)}
        
        Respond with EXACTLY a number between 0 and 100, where:
        - 100 means perfect match (exact match for {'Spring Boot' if is_spring_boot else 'Java'} {target_version} migration)
        - 75+ means very relevant (mentions {'Spring Boot' if is_spring_boot else 'Java'} upgrade to similar version)
        - 50+ means somewhat relevant (mentions {'Spring Boot' if is_spring_boot else 'Java'} but different version)
        - 25+ means slightly relevant (mentions upgrades but not specific to {'Spring Boot' if is_spring_boot else 'Java'})
        - 0 means not relevant at all"""

        logger.debug(f"Sending scoring prompt to LLM")
        response = llm.generate_content(prompt)
        score = float(response.text.strip())
        logger.info(f"Recipe '{recipe['name']}' received score: {score}")
        return min(max(score, 0), 100)
    except Exception as e:
        logger.error(f"Error scoring recipe '{recipe['name']}'", exc_info=True)
        return 0

def find_best_recipe(recipes: List[Dict], target_version: str, is_spring_boot: bool, llm: GenerativeModel) -> Optional[Dict]:
    """Find the best matching recipe for the target version."""
    logger.info(f"Finding best recipe for {'Spring Boot' if is_spring_boot else 'Java'} version {target_version}")
    
    search_pattern = f"migrate to {'spring boot' if is_spring_boot else 'java'} {target_version}"
    logger.debug(f"Searching for pattern: {search_pattern}")
    
    exact_matches = [
        recipe for recipe in recipes
        if search_pattern.lower() in recipe["name"].lower()
    ]
    logger.debug(f"Found {len(exact_matches)} exact matches")

    if exact_matches:
        match = exact_matches[0]
        logger.info(f"Using exact match: {match['name']}")
        return {
            "recipe_id": match["id"],
            "recipe_name": match["name"],
            "recipe_description": match.get("description", ""),
            "match_type": "exact"
        }

    logger.info("No exact match found, scoring all recipes")
    scored_recipes = []
    for recipe in recipes:
        logger.debug(f"Scoring recipe: {recipe['name']}")
        score = score_recipe_match(recipe, target_version, is_spring_boot, llm)
        scored_recipes.append((recipe, score))

    scored_recipes.sort(key=lambda x: x[1], reverse=True)
    logger.debug("Recipes sorted by score")
    
    if scored_recipes and scored_recipes[0][1] > 70:
        best_match = scored_recipes[0][0]
        score = scored_recipes[0][1]
        logger.info(f"Selected best match: {best_match['name']} (score: {score})")
        return {
            "recipe_id": best_match["id"],
            "recipe_name": best_match["name"],
            "recipe_description": best_match.get("description", ""),
            "match_type": "scored",
            "match_score": score
        }
    
    return None

@mcp.tool(name="migrationPlan", description="Generate migration plan based on project analysis")
def migration_plan(input_data: ProjectAnalysis) -> dict:
    """
    Generate migration plan for a list of projects.
    
    Args:
        args: Dictionary containing analysis results with project versions
    """
    try:
        logger.info("=== Starting migrationPlan ===")
        logger.debug(f"Received args: {input_data}")
        
        # # Parse input projects
        # if not args or not isinstance(args, dict):
        #     logger.error("Invalid arguments format")
        #     return {"success": False, "error": "Invalid arguments format"}
            
        # input_data = args.get("content", "{}")
        if isinstance(input_data, str):
            input_data = json.loads(input_data)
        
        logger.debug(f"Parsed input data: {input_data}")
        
        if not input_data.get("success") or not input_data.get("projects"):
            logger.error("Invalid input data format or no projects found")
            return {"success": False, "error": "Invalid input data format or no projects found"}
            
        # Convert string project data to dictionaries
        try:
            projects_data = []
            for project_str in input_data["projects"]:
                # Replace single quotes with double quotes for valid JSON
                if isinstance(project_str, str):
                    project_str = project_str.replace("'", '"')
                    project_dict = json.loads(project_str)
                else:
                    project_dict = project_str
                projects_data.append(project_dict)
            
            logger.debug(f"Parsed projects data: {projects_data}")
        except Exception as e:
            logger.error(f"Error parsing project data: {e}", exc_info=True)
            return {"success": False, "error": f"Error parsing project data: {str(e)}"}
            
        # Initialize Gemini
        load_dotenv()
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not found in environment variables")
            return {"success": False, "error": "GEMINI_API_KEY not found"}
            
        genai.configure(api_key=GEMINI_API_KEY)
        llm = GenerativeModel("gemini-pro")
        logger.debug("Gemini LLM initialized successfully")

        # Get latest versions
        latest_java = get_latest_java_version(llm)
        latest_spring = get_latest_spring_boot_version(llm)
        logger.info(f"Latest versions - Java: {latest_java}, Spring Boot: {latest_spring}")
        
        # Load Moderne recipes
        try:
            with open("C:\\Users\\rajap\\moderne_recipes.json", 'r') as f:
                recipes = json.load(f)
            logger.debug(f"Loaded {len(recipes)} recipes")
        except Exception as e:
            logger.error("Failed to load recipes file", exc_info=True)
            return {"success": False, "error": f"Could not load recipes: {str(e)}"}

        # Process each project
        updated_projects = []
        for project in projects_data:
            if not project.get("success", False):
                logger.warning(f"Skipping failed project: {project}")
                continue
                
            logger.info(f"Processing project: {project.get('project_name')}")
            
            project_update = project.copy()
            project_update["latest_jdk_version"] = latest_java
            project_update["latest_spring_boot_version"] = latest_spring
            
            current_jdk = project.get("jdk_version")
            current_spring = project.get("spring_boot_version")
            
            # Determine if updates are needed
            needs_java_update = current_jdk and current_jdk != latest_java
            needs_spring_update = current_spring and current_spring != latest_spring
            
            if needs_spring_update or needs_java_update:
                # Prefer Spring Boot migration if both updates are needed
                if needs_spring_update:
                    logger.info(f"Finding Spring Boot migration recipe for version {latest_spring}")
                    recipe_match = find_best_recipe(recipes, latest_spring, True, llm)
                    if recipe_match:
                        project_update["migration_recipe"] = recipe_match
                        updated_projects.append(project_update)
                        continue
                
                # Fall back to Java migration if Spring Boot recipe not found or only Java needs update
                if needs_java_update:
                    logger.info(f"Finding Java migration recipe for version {latest_java}")
                    recipe_match = find_best_recipe(recipes, latest_java, False, llm)
                    if recipe_match:
                        project_update["migration_recipe"] = recipe_match
                
            updated_projects.append(project_update)
        
        result = {
            "success": True,
            "projects": updated_projects,
            "total_projects": len(projects_data),
            "processed_projects": len(updated_projects)
        }
        
        serialized = serialize_response(result)
        logger.debug(f"Migration plan results after serialization: {serialized}")
        
        logger.info("=== Completed migrationPlan ===")
        return serialized
        
    except Exception as e:
        logger.error("Error in migrationPlan", exc_info=True)
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    try:
        logger.info("=== Starting Maven MCP Server ===")
        logger.info("Starting server with stdio transport")
        logger.info("Waiting for incoming messages...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error("Error running MCP server", exc_info=True)
    finally:
        logger.info("=== Maven MCP Server Stopped ===") 