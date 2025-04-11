import os
import json
import xml.etree.ElementTree as ET
import requests
from fastmcp import FastMCP, Tool, Message
import subprocess
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the Gemini client (you'll need to add your API key)
from google.generativeai import configure, GenerativeModel
import google.generativeai as genai

# Configure the Gemini API - Replace with your actual API key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your-api-key-here")
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel("gemini-2.0-flash")

class MavenProjectAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.java_version = None
        self.spring_boot_version = None
        self.dependencies = []
        self.modules = []
        self.latest_java_versions = ["11", "17", "21"]
        self.latest_spring_boot_version = self._get_latest_spring_boot_version()
        logger.debug(f"Initialized MavenProjectAnalyzer for {project_path}")
        
    def _get_latest_spring_boot_version(self):
        try:
            logger.debug("Fetching latest Spring Boot version from Maven Central")
            response = requests.get("https://search.maven.org/solrsearch/select?q=g:org.springframework.boot+AND+a:spring-boot-starter-parent&rows=1&wt=json")
            data = response.json()
            return data['response']['docs'][0]['latestVersion']
        except Exception as e:
            logger.error(f"Error fetching latest Spring Boot version: {e}")
            return "3.2.3"  # Fallback to a known recent version
    
    def analyze_project(self):
        logger.debug(f"Analyzing project at {self.project_path}")
        root_pom_path = os.path.join(self.project_path, "pom.xml")
        if os.path.exists(root_pom_path):
            self._analyze_pom(root_pom_path, is_parent=True)
            
            # Process child modules recursively
            for module in self.modules:
                module_pom_path = os.path.join(self.project_path, module, "pom.xml")
                if os.path.exists(module_pom_path):
                    self._analyze_pom(module_pom_path, is_parent=False)
        else:
            logger.error(f"No pom.xml found at {root_pom_path}")
            raise FileNotFoundError(f"No pom.xml found at {root_pom_path}")
            
        return self._generate_report()
    
    def _analyze_pom(self, pom_path, is_parent=False):
        try:
            logger.debug(f"Analyzing POM file at {pom_path}")
            tree = ET.parse(pom_path)
            root = tree.getroot()
            
            # Handle XML namespace
            ns = {"mvn": "http://maven.apache.org/POM/4.0.0"}
            
            # Extract Java version
            java_version_property = root.find(".//mvn:properties/mvn:java.version", ns)
            maven_compiler_source = root.find(".//mvn:properties/mvn:maven.compiler.source", ns)
            
            if java_version_property is not None:
                self.java_version = java_version_property.text
            elif maven_compiler_source is not None:
                self.java_version = maven_compiler_source.text
                
            # Extract Spring Boot version if it's a parent
            parent = root.find("mvn:parent", ns)
            if parent is not None:
                group_id = parent.find("mvn:groupId", ns)
                artifact_id = parent.find("mvn:artifactId", ns)
                version = parent.find("mvn:version", ns)
                
                if (group_id is not None and group_id.text == "org.springframework.boot" and
                    artifact_id is not None and artifact_id.text == "spring-boot-starter-parent" and
                    version is not None):
                    self.spring_boot_version = version.text
            
            # Extract dependencies
            dependencies = root.findall(".//mvn:dependencies/mvn:dependency", ns)
            for dep in dependencies:
                group_id = dep.find("mvn:groupId", ns)
                artifact_id = dep.find("mvn:artifactId", ns)
                version = dep.find("mvn:version", ns)
                
                if group_id is not None and artifact_id is not None:
                    dependency_info = {
                        "groupId": group_id.text,
                        "artifactId": artifact_id.text,
                        "version": version.text if version is not None else "managed"
                    }
                    self.dependencies.append(dependency_info)
            
            # Extract modules if this is a parent POM
            if is_parent:
                modules = root.findall(".//mvn:modules/mvn:module", ns)
                for module in modules:
                    if module.text not in self.modules:
                        self.modules.append(module.text)
                        
        except Exception as e:
            logger.error(f"Error analyzing POM file {pom_path}: {e}")
    
    def _generate_report(self):
        logger.debug("Generating project analysis report")
        # Determine if eligible for upgrades
        is_eligible_for_java_upgrade = False
        is_eligible_for_spring_upgrade = False
        conditions_matched = []
        
        if self.java_version and self.java_version not in self.latest_java_versions:
            is_eligible_for_java_upgrade = True
            conditions_matched.append(f"Current Java version is {self.java_version}")
        
        if self.spring_boot_version and self.spring_boot_version != self.latest_spring_boot_version:
            is_eligible_for_spring_upgrade = True
            conditions_matched.append(f"Spring Boot version is {self.spring_boot_version}")
            
        # Create the report
        report = {
            "jdk_version_used": self.java_version or "Unknown",
            "spring_boot_parent_version_used": self.spring_boot_version or "Not using Spring Boot",
            "total_dependencies_used": len(self.dependencies),
            "dependencies": self.dependencies,
            "is_eligible_for_java_upgrade": is_eligible_for_java_upgrade,
            "is_eligible_for_spring_upgrade": is_eligible_for_spring_upgrade,
            "conditions_matched": " and ".join(conditions_matched),
            "latest_java_version": self.latest_java_versions[-1],
            "latest_spring_boot_version": self.latest_spring_boot_version,
            "migration_plan": ""
        }
        
        return report

class MigrationAgent:
    def __init__(self):
        self.mcp = FastMCP()
        self.chat_history = []
        self.project_analysis = None
        
        # Register tools
        self.mcp.register_tool(
            Tool(
                name="analyze_maven_project",
                description="Analyzes a Java/Maven project structure and returns dependency information",
                function=self.analyze_maven_project
            )
        )
        
        self.mcp.register_tool(
            Tool(
                name="generate_migration_plan",
                description="Generates a detailed migration plan based on the project analysis",
                function=self.generate_migration_plan
            )
        )
        
        self.mcp.register_tool(
            Tool(
                name="run_moderne_cli",
                description="Runs the moderne-cli tool to find migration recipes",
                function=self.run_moderne_cli
            )
        )
        logger.debug("Initialized MigrationAgent with registered tools")
        
    def analyze_maven_project(self, project_path):
        """Analyzes a Maven project and returns key information about versions and dependencies."""
        try:
            logger.debug(f"Starting analysis of Maven project at {project_path}")
            analyzer = MavenProjectAnalyzer(project_path)
            self.project_analysis = analyzer.analyze_project()
            logger.debug("Project analysis completed")
            return json.dumps(self.project_analysis, indent=2)
        except Exception as e:
            logger.error(f"Error analyzing Maven project: {str(e)}")
            return f"Error analyzing Maven project: {str(e)}"
    
    def run_moderne_cli(self, migration_plan_keyword):
        """Reads the moderne_recipes.json file and returns the recipe matching the migration_plan_keyword."""
        try:
            logger.debug(f"Reading recipes from JSON file for keyword: {migration_plan_keyword}")
            with open(r'C:\Users\rajap\moderne_recipes.json', 'r') as file:
                recipes = json.load(file)
            
            for recipe in recipes:
                if migration_plan_keyword.lower() in recipe['name'].lower() or migration_plan_keyword.lower() in recipe['description'].lower():
                    logger.debug(f"Selected recipe: {recipe['name']}")
                    recipe_name = recipe['id'].split('.')[-1]
                    moderne_recipe_command = f"mod run . --recipe {recipe_name}"
                    return recipe['name'], moderne_recipe_command
            
            logger.debug("No matching recipe found in JSON file")
            return "No matching recipes found", ""
        except FileNotFoundError:
            logger.error("moderne_recipes.json file not found")
            return "Recipes file not found", ""
        except json.JSONDecodeError:
            logger.error("Error decoding JSON from recipes file")
            return "Error decoding recipes file", ""
        except Exception as e:
            logger.error(f"Error reading recipes: {str(e)}")
            return f"Error reading recipes: {str(e)}", ""
    
    def generate_migration_plan(self, analysis_json=None):
        """Generates a migration plan based on the analysis results."""
        if analysis_json:
            try:
                analysis = json.loads(analysis_json)
            except:
                analysis = self.project_analysis
        else:
            analysis = self.project_analysis
            
        if not analysis:
            logger.error("No project analysis available to generate migration plan")
            return "No project analysis available. Please run analyze_maven_project first."
        
        # Add the chat history to provide context
        context = "\n".join([f"{msg.role}: {msg.content}" for msg in self.chat_history])
        
        # Use Gemini to generate the migration plan
        prompt = f"""
        Based on the following Java/Maven project analysis and our conversation history, create a detailed migration plan:
        
        Project Analysis:
        {json.dumps(analysis, indent=2)}
        
        Conversation History:
        {context}
        
        Create a detailed and actionable migration plan that includes:
        1. Specific steps to upgrade Java version (if applicable)
        2. Steps to upgrade Spring Boot (if applicable)
        3. Suggest appropriate OpenRewrite recipes or Moderne CLI commands
        4. Potential risks and mitigation strategies
        5. Testing strategies for the migration
        
        Format the migration plan as JSON that can be added to the analysis results.
        """
        
        try:
            logger.debug("Generating migration plan using Gemini LLM")
            response = model.generate_content(prompt)
            migration_plan = response.text
            
            # Try to parse as JSON and extract just the migration plan part
            try:
                plan_json = json.loads(migration_plan)
                analysis["migration_plan"] = plan_json
            except:
                # If not valid JSON, just add the text as-is
                analysis["migration_plan"] = migration_plan
                
            # Run moderne-cli to get the recipe
            if analysis.get("is_eligible_for_java_upgrade"):
                keyword = f"migrate to java {analysis['latest_java_version']}"
            elif analysis.get("is_eligible_for_spring_upgrade"):
                keyword = f"migrate to spring boot {analysis['latest_spring_boot_version']}"
            else:
                keyword = ""
            
            if keyword:
                logger.debug(f"Fetching moderne-cli recipe for keyword: {keyword}")
                moderne_recipe, moderne_recipe_command = self.run_moderne_cli(keyword)
                analysis["moderne_recipes"] = moderne_recipe
                analysis["moderne_recipe_command"] = moderne_recipe_command
            
            self.project_analysis = analysis
            logger.debug("Migration plan generation completed")
            return json.dumps(analysis, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating migration plan: {str(e)}")
            return f"Error generating migration plan: {str(e)}"
    
    def add_message_to_history(self, role, content):
        """Adds a message to the conversation history."""
        logger.debug(f"Adding message to history: {role}: {content}")
        self.chat_history.append(Message(role=role, content=content))
    
    def run(self):
        """Run the migration agent and handle the conversation."""
        logger.debug("Starting MigrationAgent run loop")
        print("Java/Maven Migration Agent initialized. Type 'exit' to quit.")
        print("Please provide the path to your Maven project:")
        
        while True:
            user_input = input("> ")
            if user_input.lower() == "exit":
                logger.debug("Exiting MigrationAgent run loop")
                break
                
            self.add_message_to_history("user", user_input)
            
            if os.path.exists(user_input) and os.path.isdir(user_input):
                analysis_result = self.analyze_maven_project(user_input)
                print(analysis_result)
                self.add_message_to_history("assistant", analysis_result)
                
                print("\nWould you like me to generate a migration plan? (yes/no)")
                if input("> ").lower() == "yes":
                    migration_plan = self.generate_migration_plan()
                    print(migration_plan)
                    self.add_message_to_history("assistant", migration_plan)
            else:
                if self.project_analysis:
                    # Use Gemini to respond to the user query based on the analysis
                    prompt = f"""
                    Based on the following Java/Maven project analysis and the user's query, provide a helpful response:
                    
                    Project Analysis:
                    {json.dumps(self.project_analysis, indent=2)}
                    
                    User Query: {user_input}
                    
                    Provide a concise and helpful response.
                    """
                    
                    try:
                        logger.debug("Generating response to user query using Gemini LLM")
                        response = model.generate_content(prompt)
                        print(response.text)
                        self.add_message_to_history("assistant", response.text)
                    except Exception as e:
                        logger.error(f"Error generating response: {str(e)}")
                else:
                    print("Please provide a valid path to a Maven project directory.")

if __name__ == "__main__":
    agent = MigrationAgent()
    agent.run() 