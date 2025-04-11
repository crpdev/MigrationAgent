# Java/Maven Migration Agent

A Python-based agent that uses Google's Gemini LLM to analyze Java/Maven projects and provide migration recommendations.

## Features

- Analyzes Java/Maven projects to extract Java version, Spring Boot version, and dependencies
- Recursively processes multi-module Maven projects
- Identifies if projects are eligible for Java or Spring Boot upgrades
- Generates detailed migration plans with OpenRewrite recipes or Moderne CLI commands
- Provides actionable JSON output with migration recommendations

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Set your Gemini API key:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Alternatively, you can edit `migration_agent.py` to set your API key directly.

## Usage

### Command Line Interface

Analyze a Maven project:

```bash
python cli.py --path /path/to/maven/project
```

Save the analysis to a file:

```bash
python cli.py --path /path/to/maven/project --output analysis.json
```

Run in interactive mode:

```bash
python cli.py --interactive
```

### Direct Usage

You can also use the MigrationAgent directly in your Python code:

```python
from migration_agent import MigrationAgent

agent = MigrationAgent()
analysis = agent.analyze_maven_project("/path/to/maven/project")
migration_plan = agent.generate_migration_plan()
```

## Output Format

The agent provides a JSON output with the following structure:

```json
{
  "jdk_version_used": "1.8",
  "spring_boot_parent_version_used": "2.7.5",
  "total_dependencies_used": 25,
  "dependencies": [
    {
      "groupId": "org.springframework.boot",
      "artifactId": "spring-boot-starter-web",
      "version": "2.7.5"
    },
    ...
  ],
  "is_eligible_for_java_upgrade": true,
  "is_eligible_for_spring_upgrade": true,
  "conditions_matched": "Current Java version is 1.8 and Spring Boot version is 2.7.5",
  "latest_java_version": "21",
  "latest_spring_boot_version": "3.2.3",
  "migration_plan": {
    // Detailed migration steps and recommendations
  }
}
```

## License

MIT 