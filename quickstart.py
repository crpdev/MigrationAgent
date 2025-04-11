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
    """Check if the GEMINI_API_KEY environment variable is set."""
    api_key = os.environ.get("GEMINI_API_KEY")
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

def main():
    """Run the quickstart process."""
    print_section("Welcome to Migration Agent Quickstart", 
        """
        This script will help you get started with the Migration Agent.
        The Migration Agent analyzes Java/Maven projects and provides
        migration recommendations for Java version and Spring Boot upgrades.
        """
    )
    
    # Check dependencies and environment
    if not check_api_key():
        return 1
    
    if not install_dependencies():
        return 1
    
    if not check_sample_project():
        return 1
    
    # Run the test agent
    if not run_test_agent():
        return 1
    
    # Ask if user wants to try interactive mode
    run_interactive_mode()
    
    print_section("Thank You", 
        """
        Thank you for trying the Migration Agent!
        
        For more information, please read the README.md file.
        """
    )
    return 0

if __name__ == "__main__":
    sys.exit(main()) 