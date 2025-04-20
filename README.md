# Java Migration Cognitive Agent

A cognitive agent that assists in Java project migration using functional programming principles and LLM-powered decision making. The agent follows a structured workflow to analyze Java projects, create migration plans, and execute upgrades using Moderne and Maven tools.

## Architecture

The system is built using a cognitive architecture with the following components:

### 1. Perception Layer
- Handles user input collection and validation
- Captures project path, migration type, and release type
- Validates inputs against defined constraints

### 2. Memory Layer
- Maintains immutable state using Pydantic models
- Stores user preferences and context
- Provides pure functions for state updates

### 3. Decision Making Layer
- Integrates with Google Gemini LLM
- Processes tool descriptions and maintains workflow state
- Generates structured decisions based on context
- Follows a defined migration workflow:
  1. Project Analysis
  2. Migration Planning
  3. Upgrade Execution

### 4. Action Layer
- Executes decisions through MCP tools
- Integrates with Moderne and Maven tooling
- Handles error cases and provides feedback

## Prerequisites

- Python 3.8+
- Windows 10/11 or compatible OS
- Java Development Kit (JDK) 8 or higher
- Maven 3.6+
- Moderne CLI tools
- Google Cloud API access

## Dependencies

Create a `requirements.txt` file with:

```
pydantic>=2.0.0
python-dotenv>=1.0.0
google-generativeai>=0.3.0
mcp-client>=1.0.0
asyncio>=3.4.3
```

## Environment Setup

1. Create a `.env` file with:
```
GEMINI_API_KEY=your_gemini_api_key
PROJECTS_BASE_PATH=your_default_projects_path
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
├── cognitive_agent.py     # Main orchestrator
├── models.py             # Pydantic data models
├── perception.py         # Input handling
├── memory.py            # State management
├── decision.py          # LLM integration
├── action.py            # Tool execution
├── .env                 # Environment variables
└── requirements.txt     # Dependencies
```

## Usage

1. Start the cognitive agent:
```bash
python cognitive_agent.py
```

2. Enter the required information when prompted:
   - Project path (full path to Java project)
   - Migration type (java/python)
   - Release type (stable/rc)

3. The agent will:
   - Analyze the project structure
   - Determine Spring Boot version
   - Create a migration plan
   - Execute necessary upgrades

## Migration Workflow

1. **Project Analysis** (`analyzeProject`)
   - Identifies JDK version
   - Detects Spring Boot version
   - Analyzes project structure

2. **Migration Planning** (`migrationPlan`)
   - Generates migration strategy
   - Determines upgrade recipe

3. **Upgrade Execution** (`modUpgradeAll`)
   - Applies the upgrade recipe
   - Handles necessary migrations

## Available Tools

### Moderne Tools
- `modUpgradeAll` - Upgrades projects using specified recipe
  - Parameters:
    - project_path: string
    - recipe_id: string

### Maven Tools
- `analyzeProject` - Analyzes Maven project
  - Parameters:
    - project_path: string
- `migrationPlan` - Generates migration plan

## Error Handling

The system provides comprehensive error handling:
- Input validation
- Tool execution monitoring
- LLM response validation
- State consistency checks

## Logging

Logs are stored in the `logs` directory:
- `cognitive_agent_*.log` - Main agent logs
- `decision_*.log` - Decision making logs

## Best Practices

1. Always provide absolute paths for project locations
2. Ensure all required tools are installed and accessible
3. Verify Java and Maven versions match project requirements
4. Check logs for detailed execution information

## Troubleshooting

Common issues and solutions:

1. **LLM Connection Error**
   - Verify GEMINI_API_KEY in .env
   - Check internet connection

2. **Tool Execution Failed**
   - Ensure Moderne CLI is installed
   - Verify Maven installation
   - Check project path exists

3. **Invalid Project Structure**
   - Verify pom.xml exists
   - Check Java version compatibility

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - See LICENSE file for details 