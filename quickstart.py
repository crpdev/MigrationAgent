#!/usr/bin/env python
"""
Quick start script for the Migration Agent.
This script helps new users set up and run the Migration Agent.
"""

import os
import sys
import subprocess
import textwrap
from pathlib import Path
from dotenv import load_dotenv
import logging
from subprocess import *

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_section(title, content):
    """Print a formatted section with a title and content."""
    width = 80
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width)
    # Format and print content with proper indentation
    for line in content.strip().split("\n"):
        print(textwrap.fill(line, width=width, subsequent_indent="  "))

def check_api_key():
    load_dotenv()
    """Check if the GEMINI_API_KEY environment variable is set."""
    api_key = os.getenv("GEMINI_API_KEY")
    # os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print_section("API Key Not Found", 
            """
            You need to set the GEMINI_API_KEY environment variable to use the Migration Agent.
            
            You can get an API key from https://makersuite.google.com/app/apikey
            
            Set it with one of these commands:
            
            On Windows:
            set GEMINI_API_KEY=your-api-key-here
            
            On macOS/Linux:
            export GEMINI_API_KEY=your-api-key-here
            """
        )
        return False
    return True

def install_dependencies():
    """Install required dependencies."""
    print_section("Installing Dependencies", "Installing required Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\nDependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("\nFailed to install dependencies. Please check your Python installation.")
        return False

def check_sample_project():
    """Check if the sample project exists."""
    sample_path = Path(__file__).parent / "tests" / "sample_project"
    if not sample_path.exists():
        print_section("Sample Project Not Found", 
            """
            The sample Maven project was not found. This is needed to test the Migration Agent.
            
            Please make sure you've downloaded the complete repository.
            """
        )
        return False
    return True

def run_test_agent():
    """Run the test_agent.py script to demonstrate functionality."""
    print_section("Running Test Agent", 
        """
        Now running the test agent to analyze the sample Maven project.
        This will show you how the Migration Agent works on a real project.
        """
    )
    try:
        subprocess.check_call([sys.executable, "test_agent.py"])
        return True
    except subprocess.CalledProcessError:
        print("\nFailed to run the test agent. Please check the error messages above.")
        return False

def run_interactive_mode():
    """Ask if the user wants to run in interactive mode."""
    print_section("Interactive Mode", 
        """
        Would you like to try the interactive mode to analyze your own projects?
        In this mode, you can provide the path to your own Maven project and
        get migration recommendations.
        """
    )
    while True:
        response = input("Enter 'y' to proceed or 'n' to exit: ").lower()
        if response == 'y':
            print("\nStarting interactive mode...")
            subprocess.call([sys.executable, "cli.py", "--interactive"])
            return True
        elif response == 'n':
            return False
        else:
            print("Please enter 'y' or 'n'.")

def test_run_moderne_cli_build():
    """Test method to execute a Java JAR file with arguments from the environment."""
    import subprocess

    # Path to the Java JAR file
    jar_file_path = "C:\\Users\\rajap\\tools\\moderne-cli-3.36.1.jar"

    # Get sample arguments from environment variables
    sample_arguments = os.getenv("SAMPLE_ARGUMENTS")

    if not sample_arguments:
        logger.error("No arguments provided in the environment variable SAMPLE_ARGUMENTS.")
        return

    logger.info("About to execute the Java JAR file...")

    # Execute the Java JAR file with the sample arguments
    try:
        # result = subprocess.call(["java", "-jar", jar_file_path, 'config', 'recipes', 'search', 'migrate', 'to', 'spring', 'boot', '3.4' ])
        result = subprocess.run(["java", "-jar", jar_file_path, "build", "C:\\Users\\rajap\\workspace\\EAG\\Assignment5-MigrationAgent-Cursor\\test\\sample-spring-boot"], capture_output=True, text=True)
        logger.info("Java JAR execution output: %s", result.stdout)
        logger.error("Java JAR execution errors: %s", result.stderr)

        # process = Popen(['java', '-jar', jar_file_path + "config recipes search migrate to spring boot 3.4"], stdout=PIPE, stderr=PIPE)
        # result = process.communicate()
        # print(result[0].decode('utf-8'))
    except subprocess.CalledProcessError as e:
        logger.error("An error occurred while executing the Java JAR file: %s", e)

    logger.info("Java JAR execution completed.")

def test_run_moderne_cli_upgrade():
    """Test method to execute a Java JAR file with arguments from the environment."""
    import subprocess

    # Path to the Java JAR file
    jar_file_path = "C:\\Users\\rajap\\tools\\moderne-cli-3.36.1.jar"

    # Get sample arguments from environment variables
    sample_arguments = os.getenv("SAMPLE_ARGUMENTS")

    if not sample_arguments:
        logger.error("No arguments provided in the environment variable SAMPLE_ARGUMENTS.")
        return

    logger.info("About to execute the Java JAR file...")

    # Execute the Java JAR file with the sample arguments
    try:
        # result = subprocess.call(["java", "-jar", jar_file_path, 'config', 'recipes', 'search', 'migrate', 'to', 'spring', 'boot', '3.4' ])
        result = subprocess.run(["java", "-jar", jar_file_path, "run", "C:\\Users\\rajap\\workspace\\EAG\\Assignment5-MigrationAgent-Cursor\\test\\sample-spring-boot", "--recipe", "UpgradeToJava21"], capture_output=True, text=True)
        logger.info("Java JAR execution output: %s", result.stdout)
        logger.error("Java JAR execution errors: %s", result.stderr)

        # process = Popen(['java', '-jar', jar_file_path + "config recipes search migrate to spring boot 3.4"], stdout=PIPE, stderr=PIPE)
        # result = process.communicate()
        # print(result[0].decode('utf-8'))
    except subprocess.CalledProcessError as e:
        logger.error("An error occurred while executing the Java JAR file: %s", e)

    logger.info("Java JAR execution completed.")

def test_run_moderne_cli_upgrade_apply():
    """Test method to execute a Java JAR file with arguments from the environment."""
    import subprocess

    # Path to the Java JAR file
    jar_file_path = "C:\\Users\\rajap\\tools\\moderne-cli-3.36.1.jar"

    # Get sample arguments from environment variables
    sample_arguments = os.getenv("SAMPLE_ARGUMENTS")

    if not sample_arguments:
        logger.error("No arguments provided in the environment variable SAMPLE_ARGUMENTS.")
        return

    logger.info("About to execute the Java JAR file...")

    # Execute the Java JAR file with the sample arguments
    try:
        # result = subprocess.call(["java", "-jar", jar_file_path, 'config', 'recipes', 'search', 'migrate', 'to', 'spring', 'boot', '3.4' ])
        result = subprocess.run(["java", "-jar", jar_file_path, "git", "apply", "C:\\Users\\rajap\\workspace\\EAG\\Assignment5-MigrationAgent-Cursor\\test\\sample-spring-boot", "--last-recipe-run"], capture_output=True, text=True)
        logger.info("Java JAR execution output: %s", result.stdout)
        logger.error("Java JAR execution errors: %s", result.stderr)

        # process = Popen(['java', '-jar', jar_file_path + "config recipes search migrate to spring boot 3.4"], stdout=PIPE, stderr=PIPE)
        # result = process.communicate()
        # print(result[0].decode('utf-8'))
    except subprocess.CalledProcessError as e:
        logger.error("An error occurred while executing the Java JAR file: %s", e)

    logger.info("Java JAR execution completed.")

def test_run_moderne_cli():
    """Test method to execute a Java JAR file with arguments from the environment."""
    import subprocess

    # Path to the Java JAR file
    jar_file_path = "C:\\Users\\rajap\\tools\\moderne-cli-3.36.1.jar"

    # Get sample arguments from environment variables
    sample_arguments = os.getenv("SAMPLE_ARGUMENTS")

    if not sample_arguments:
        logger.error("No arguments provided in the environment variable SAMPLE_ARGUMENTS.")
        return

    logger.info("About to execute the Java JAR file...")

    # Execute the Java JAR file with the sample arguments
    try:
        # result = subprocess.call(["java", "-jar", jar_file_path, 'config', 'recipes', 'search', 'migrate', 'to', 'spring', 'boot', '3.4' ])
        result = subprocess.run(["java", "-jar", jar_file_path, "config", "recipes", "search", "spring"], capture_output=True, text=True)
        logger.info("Java JAR execution output: %s", result.stdout)
        logger.error("Java JAR execution errors: %s", result.stderr)

        # process = Popen(['java', '-jar', jar_file_path + "config recipes search migrate to spring boot 3.4"], stdout=PIPE, stderr=PIPE)
        # result = process.communicate()
        # print(result[0].decode('utf-8'))
    except subprocess.CalledProcessError as e:
        logger.error("An error occurred while executing the Java JAR file: %s", e)

    logger.info("Java JAR execution completed.")

def main():
    load_dotenv()
    test_run_moderne_cli_build()
    test_run_moderne_cli_upgrade()
    # test_run_moderne_cli_upgrade_apply()
    # test_run_moderne_cli_build()
    # test_run_moderne_cli()

    """Run the quickstart process."""
    print_section("Welcome to Migration Agent Quickstart", 
        """
        This script will help you get started with the Migration Agent.
        The Migration Agent analyzes Java/Maven projects and provides
        migration recommendations for Java version and Spring Boot upgrades.
        """
    )
    
    # Check dependencies and environment
    # if not check_api_key():
    #     return 1
    
    # if not install_dependencies():
    #     return 1
    
    # if not check_sample_project():
    #     return 1
    
    # Run the test agent
    # if not run_test_agent():
    #     return 1
    
    # Ask if user wants to try interactive mode
    # run_interactive_mode()
    
    print_section("Thank You", 
        """
        Thank you for trying the Migration Agent!
        
        For more information, please read the README.md file.
        """
    )
    return 0

if __name__ == "__main__":
    sys.exit(main()) 