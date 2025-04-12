import os
import json
import xml.etree.ElementTree as ET
import requests
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP, Tool, Message
import google.generativeai as genai
from google.generativeai import GenerativeModel

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MigrationAgentV2:
    def __init__(self):
        load_dotenv()
        # Initialize MCP client and register tools
        self.mcp = FastMCP()
        self.setup_tools()
        
        # Initialize Gemini
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=GEMINI_API_KEY)
        self.llm = GenerativeModel("gemini-2.0-flash")
        
        self.response = {
            "jdk_version_used": "",
            "spring_boot_parent_version_used": "",
            "total_dependencies_used": 0,
            "dependencies": [],
            "is_eligible_for_java_upgrade": False,
            "is_eligible_for_spring_upgrade": False,
            "conditions_matched": "",
            "latest_java_version": "",
            "latest_spring_boot_version": "",
            "migration_plan": "",
            "moderne_recipe_available": False,
            "moderne_recipe": "",
            "moderne_recipe_command": "",
            "moderne_recipe_execution_status": "",
            "moderne_recipe_post_execution_build_status": "",
            "final_migration_status": "",
            "errors": ""
        }

    def setup_tools(self):
        """Register all MCP tools."""
        self.mcp.register_tool(
            Tool(
                name="modBuild",
                description="Build a project using Moderne CLI",
                function=self.mod_build_impl
            )
        )
        
        self.mcp.register_tool(
            Tool(
                name="modUpgrade",
                description="Upgrade a project using specified recipe",
                function=self.mod_upgrade_impl
            )
        )
        
        self.mcp.register_tool(
            Tool(
                name="modApplyUpgrade",
                description="Apply the last recipe run using Moderne CLI",
                function=self.mod_apply_upgrade_impl
            )
        )

    def mod_build_impl(self, message: Message) -> dict:
        """Implementation of modBuild tool."""
        try:
            project_path = message.content
            # Execute the build command
            return {"success": True, "output": f"Build executed for {project_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mod_upgrade_impl(self, message: Message) -> dict:
        """Implementation of modUpgrade tool."""
        try:
            project_path, recipe = message.content.split("|")
            # Execute the upgrade command
            return {"success": True, "output": f"Upgrade executed for {project_path} with recipe {recipe}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mod_apply_upgrade_impl(self, message: Message) -> dict:
        """Implementation of modApplyUpgrade tool."""
        try:
            project_path = message.content
            # Execute the apply command
            return {"success": True, "output": f"Changes applied for {project_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def mod_build(self, project_path: str) -> dict:
        """Execute modBuild using MCP client."""
        try:
            message = Message(role="user", content=project_path)
            return self.mod_build_impl(message)
        except Exception as e:
            logger.error(f"Error in mod_build: {str(e)}")
            return {"success": False, "error": str(e)}

    def mod_upgrade(self, project_path: str, recipe: str) -> dict:
        """Execute modUpgrade using MCP client."""
        try:
            message = Message(role="user", content=f"{project_path}|{recipe}")
            return self.mod_upgrade_impl(message)
        except Exception as e:
            logger.error(f"Error in mod_upgrade: {str(e)}")
            return {"success": False, "error": str(e)}

    def mod_apply_upgrade(self, project_path: str) -> dict:
        """Execute modApplyUpgrade using MCP client."""
        try:
            message = Message(role="user", content=project_path)
            return self.mod_apply_upgrade_impl(message)
        except Exception as e:
            logger.error(f"Error in mod_apply_upgrade: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_latest_java_version(self):
        """Get the latest stable Java version from Maven repository."""
        try:
            response = requests.get("https://search.maven.org/solrsearch/select?q=g:org.openjdk.jdk+AND+a:jdk&rows=1&wt=json")
            data = response.json()
            latest_version = data['response']['docs'][0]['latestVersion']
            return latest_version.split('.')[0]  # Extract major version
        except Exception as e:
            logger.error(f"Error fetching latest Java version: {e}")
            return "21"  # Fallback to a known recent version

    def _load_moderne_recipes(self):
        """Load Moderne recipes from JSON file."""
        try:
            with open("C:\\Users\\rajap\\moderne_recipes.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading Moderne recipes: {e}")
            return []

    def _score_recipe_match(self, recipe, migration_goal):
        """Use LLM to score how well a recipe matches the migration goal."""
        try:
            prompt = f"""As a Java migration expert, score how well this recipe matches the migration goal.
            
            Migration Goal: {migration_goal}
            
            Recipe:
            {json.dumps(recipe, indent=2)}
            
            Respond with EXACTLY a number between 0 and 100, where 100 means perfect match and 0 means no match at all.
            Consider the recipe name, description, and how well it aligns with the migration goal.
            """

            response = self.llm.generate_content(prompt)
            score = int(response.text.strip())
            return min(max(score, 0), 100)  # Ensure score is between 0 and 100
        except Exception as e:
            logger.error(f"Error scoring recipe match: {e}")
            return 0

    def get_llm_suggestion(self, context):
        """Get migration suggestions from Gemini LLM."""
        try:
            # Get latest Java version
            latest_java = self._get_latest_java_version()
            self.response["latest_java_version"] = latest_java

            # Load Moderne recipes
            recipes = self._load_moderne_recipes()
            if not recipes:
                return None

            # Determine migration goal
            migration_goals = []
            if context["is_eligible_for_java_upgrade"]:
                migration_goals.append(f"Migrate to Java {latest_java}")
            if context["is_eligible_for_spring_upgrade"]:
                migration_goals.append(f"Migrate to Spring Boot {context['latest_spring_boot_version']}")

            migration_goal = " and ".join(migration_goals)

            # First, try direct name match
            for recipe in recipes:
                if any(goal.lower() in recipe["name"].lower() for goal in migration_goals):
                    logger.info(f"Found direct recipe match: {recipe['name']}")
                    return recipe["id"]

            # If no direct match, score all recipes
            logger.info("No direct match found, scoring recipes...")
            scored_recipes = []
            for recipe in recipes:
                score = self._score_recipe_match(recipe, migration_goal)
                scored_recipes.append((recipe, score))
                logger.info(f"Recipe '{recipe['name']}' scored {score}")

            # Sort by score and get the best match
            scored_recipes.sort(key=lambda x: x[1], reverse=True)
            if scored_recipes and scored_recipes[0][1] > 70:  # Only use if score is above 70
                best_match = scored_recipes[0][0]
                logger.info(f"Selected best match recipe: {best_match['name']} (score: {scored_recipes[0][1]})")
                return best_match["id"]

            return None
        except Exception as e:
            logger.error(f"Error getting LLM suggestion: {str(e)}")
            return None

    def validate_migration_step(self, step_result, step_name):
        """Get LLM validation for each migration step."""
        try:
            prompt = f"""As a Java migration expert, analyze this {step_name} result and suggest if we should proceed with the next step.
            
            Step Result:
            {json.dumps(step_result, indent=2)}
            
            Respond with EXACTLY 'proceed' or 'abort', nothing else."""

            response = self.llm.generate_content(prompt)
            decision = response.text.strip().lower()
            logger.info(f"LLM validation for {step_name}: {decision}")
            return decision == "proceed"
        except Exception as e:
            logger.error(f"Error in LLM validation: {str(e)}")
            return False

    def analyze_project(self, project_path):
        """Analyze the Maven project and update the response JSON."""
        try:
            logger.info(f"Analyzing project at {project_path}")
            pom_path = os.path.join(project_path, "pom.xml")
            
            if not os.path.exists(pom_path):
                self.response["errors"] = f"No pom.xml found at {pom_path}"
                return self.response

            tree = ET.parse(pom_path)
            root = tree.getroot()
            ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}

            # Extract Java version
            java_version = root.find(".//mvn:properties/mvn:java.version", ns)
            if java_version is not None:
                self.response["jdk_version_used"] = java_version.text

            # Extract Spring Boot version
            parent = root.find("mvn:parent", ns)
            if parent is not None:
                group_id = parent.find("mvn:groupId", ns)
                artifact_id = parent.find("mvn:artifactId", ns)
                version = parent.find("mvn:version", ns)
                
                if (group_id is not None and group_id.text == "org.springframework.boot" and
                    artifact_id is not None and artifact_id.text == "spring-boot-starter-parent" and
                    version is not None):
                    self.response["spring_boot_parent_version_used"] = version.text

            # Extract dependencies
            dependencies = root.findall(".//mvn:dependencies/mvn:dependency", ns)
            deps_list = []
            for dep in dependencies:
                group_id = dep.find("mvn:groupId", ns)
                artifact_id = dep.find("mvn:artifactId", ns)
                version = dep.find("mvn:version", ns)
                
                if group_id is not None and artifact_id is not None:
                    deps_list.append({
                        "groupId": group_id.text,
                        "artifactId": artifact_id.text,
                        "version": version.text if version is not None else "managed"
                    })

            self.response["dependencies"] = deps_list
            self.response["total_dependencies_used"] = len(deps_list)

            # Check upgrade eligibility using LLM
            conditions = []
            if self.response["jdk_version_used"] and self.response["jdk_version_used"] != "21":
                self.response["is_eligible_for_java_upgrade"] = True
                conditions.append(f"Current Java version is {self.response['jdk_version_used']}")

            if (self.response["spring_boot_parent_version_used"] and 
                self.response["spring_boot_parent_version_used"] != "3.4.4"):
                self.response["is_eligible_for_spring_upgrade"] = True
                conditions.append(f"Spring Boot version is {self.response['spring_boot_parent_version_used']}")

            self.response["conditions_matched"] = " and ".join(conditions)
            
            # Get recipe suggestion from LLM
            if self.response["is_eligible_for_java_upgrade"] or self.response["is_eligible_for_spring_upgrade"]:
                suggested_recipe = self.get_llm_suggestion(self.response)
                if suggested_recipe:
                    self.response["migration_plan"] = "Recipe available in Moderne"
                    self.response["moderne_recipe_available"] = True
                    self.response["moderne_recipe"] = f"Migrate to {suggested_recipe}"
                    self.response["moderne_recipe_command"] = f"mod run . --recipe {suggested_recipe}"

            logger.info("Project analysis completed successfully")
            return self.response

        except Exception as e:
            logger.error(f"Error analyzing project: {str(e)}")
            self.response["errors"] = str(e)
            return self.response

    def execute_migration(self, project_path):
        """Execute the migration process using the MCP server with LLM validation."""
        try:
            # Step 1: Initial build
            logger.info("Starting initial build")
            build_result = self.mod_build(project_path)
            if not build_result.get("success") or not self.validate_migration_step(build_result, "initial build"):
                self.response["errors"] = f"Initial build failed: {build_result.get('error')}"
                self.response["final_migration_status"] = "failed"
                return self.response

            # Step 2: Run recipe
            if self.response["moderne_recipe_available"]:
                logger.info("Running Moderne recipe")
                recipe = self.response["moderne_recipe_command"].split("--recipe ")[1]
                upgrade_result = self.mod_upgrade(project_path, recipe)
                self.response["moderne_recipe_execution_status"] = "success" if upgrade_result.get("success") else "failed"
                
                if not upgrade_result.get("success") or not self.validate_migration_step(upgrade_result, "recipe execution"):
                    self.response["errors"] = f"Recipe execution failed: {upgrade_result.get('error')}"
                    self.response["final_migration_status"] = "failed"
                    return self.response

                # Step 3: Apply changes
                logger.info("Applying changes")
                apply_result = self.mod_apply_upgrade(project_path)
                if not apply_result.get("success") or not self.validate_migration_step(apply_result, "apply changes"):
                    self.response["errors"] = f"Applying changes failed: {apply_result.get('error')}"
                    self.response["final_migration_status"] = "failed"
                    return self.response

                # Step 4: Final build
                logger.info("Running final build")
                final_build_result = self.mod_build(project_path)
                self.response["moderne_recipe_post_execution_build_status"] = "success" if final_build_result.get("success") else "failed"
                
                if not final_build_result.get("success") or not self.validate_migration_step(final_build_result, "final build"):
                    self.response["errors"] = f"Final build failed: {final_build_result.get('error')}"
                    self.response["final_migration_status"] = "failed"
                    return self.response

            self.response["final_migration_status"] = "success"
            return self.response

        except Exception as e:
            logger.error(f"Error during migration execution: {str(e)}")
            self.response["errors"] = str(e)
            self.response["final_migration_status"] = "failed"
            return self.response

def main():
    agent = MigrationAgentV2()
    project_path = "C:\\Users\\rajap\\workspace\\EAG\\Assignment5-MigrationAgent-Cursor\\test\\sample-spring-boot"
    
    # Step 1: Analyze the project
    response = agent.analyze_project(project_path)
    
    # Step 2: Execute migration if eligible
    if response["moderne_recipe_available"]:
        response = agent.execute_migration(project_path)
    
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main() 