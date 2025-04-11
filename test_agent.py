#!/usr/bin/env python

import os
import json
from migration_agent import MigrationAgent

def test_migration_agent():
    """Test the MigrationAgent by analyzing the sample project."""
    agent = MigrationAgent()
    
    # Get the path to the sample project
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_project_path = os.path.join(current_dir, 'tests', 'sample_project')
    
    print(f"Analyzing sample project at: {sample_project_path}")
    
    if not os.path.exists(sample_project_path):
        print(f"Error: Sample project path does not exist: {sample_project_path}")
        return
    
    # Analyze the project
    try:
        analysis_result = agent.analyze_maven_project(sample_project_path)
        analysis = json.loads(analysis_result)
        
        print("\nAnalysis Summary:")
        print(f"Java Version: {analysis['jdk_version_used']}")
        print(f"Spring Boot Version: {analysis['spring_boot_parent_version_used']}")
        print(f"Total Dependencies: {analysis['total_dependencies_used']}")
        
        print("\nDependencies:")
        for dep in analysis['dependencies']:
            print(f"- {dep['groupId']}:{dep['artifactId']}:{dep['version']}")
        
        if analysis['is_eligible_for_java_upgrade'] or analysis['is_eligible_for_spring_upgrade']:
            print("\nUpgrade Recommendations:")
            if analysis['is_eligible_for_java_upgrade']:
                print(f"- Upgrade Java from {analysis['jdk_version_used']} to {analysis['latest_java_version']}")
            if analysis['is_eligible_for_spring_upgrade']:
                print(f"- Upgrade Spring Boot from {analysis['spring_boot_parent_version_used']} to {analysis['latest_spring_boot_version']}")
            
            # Generate migration plan
            print("\nGenerating migration plan...")
            migration_plan = agent.generate_migration_plan()
            
            # Save the result to a file for inspection
            with open('migration_analysis.json', 'w') as f:
                f.write(migration_plan)
            print("Migration plan saved to 'migration_analysis.json'")
    
    except Exception as e:
        print(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    test_migration_agent() 