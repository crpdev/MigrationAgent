#!/usr/bin/env python
import argparse
import os
import json
from migration_agent import MigrationAgent

def main():
    parser = argparse.ArgumentParser(description="Java/Maven Migration Agent")
    parser.add_argument("--path", type=str, help="Path to the Maven project to analyze")
    parser.add_argument("--output", type=str, help="Path to save the analysis report as JSON")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    args = parser.parse_args()
    
    agent = MigrationAgent()
    
    if args.interactive:
        # Run in interactive mode
        agent.run()
    elif args.path:
        # Run in single-analysis mode
        if not os.path.exists(args.path) or not os.path.isdir(args.path):
            print(f"Error: Path '{args.path}' does not exist or is not a directory")
            return 1
            
        print(f"Analyzing Maven project at: {args.path}")
        analysis_result = agent.analyze_maven_project(args.path)
        
        # Print analysis summary
        try:
            analysis = json.loads(analysis_result)
            print("\nAnalysis Summary:")
            print(f"Java Version: {analysis['jdk_version_used']}")
            print(f"Spring Boot Version: {analysis['spring_boot_parent_version_used']}")
            print(f"Total Dependencies: {analysis['total_dependencies_used']}")
            
            if analysis['is_eligible_for_java_upgrade'] or analysis['is_eligible_for_spring_upgrade']:
                print("\nUpgrade Recommendations:")
                if analysis['is_eligible_for_java_upgrade']:
                    print(f"- Upgrade Java from {analysis['jdk_version_used']} to {analysis['latest_java_version']}")
                if analysis['is_eligible_for_spring_upgrade']:
                    print(f"- Upgrade Spring Boot from {analysis['spring_boot_parent_version_used']} to {analysis['latest_spring_boot_version']}")
                
                # Generate migration plan
                print("\nGenerating migration plan...")
                migration_plan = agent.generate_migration_plan()
                analysis = json.loads(migration_plan)
        except:
            print(analysis_result)
        
        # Save to file if output path is provided
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    if isinstance(analysis_result, str):
                        f.write(analysis_result)
                    else:
                        json.dump(analysis_result, f, indent=2)
                print(f"\nAnalysis saved to: {args.output}")
            except Exception as e:
                print(f"Error saving analysis: {str(e)}")
    else:
        parser.print_help()
        
    return 0

if __name__ == "__main__":
    exit(main()) 