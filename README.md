# Java Migration Cognitive Agent

A cognitive agent that assists in Java project migration using functional programming principles and LLM-powered decision making. The agent follows a structured workflow to analyze Java projects, create migration plans, and execute upgrades using Moderne and Maven tools.

## Architecture

The system is built using a cognitive architecture with the following components:

### 1. Perception Layer
- Handles user input collection and validation
- Captures project path, migration type, and release type
- Validates inputs against defined constraints
- Manages saved preferences and user choices
- Provides option to use or update saved settings

### 2. Memory Layer
- Maintains immutable state using Pydantic models
- Stores user preferences and context
- Provides pure functions for state updates
- Handles recipe_id extraction and storage
- Manages persistent storage of preferences
- Implements fallback mechanisms for data retrieval

### 3. Decision Making Layer
- Integrates with Google Gemini LLM
- Processes tool descriptions and maintains workflow state
- Generates structured decisions based on context
- Follows a defined migration workflow:
  1. Project Analysis
  2. Migration Planning
  3. Upgrade Execution
- Handles recipe_id replacement in commands
- Maintains workflow progress tracking

### 4. Action Layer
- Executes decisions through MCP tools
- Integrates with Moderne and Maven tooling
- Handles error cases and provides feedback
- Manages tool session lifecycle
- Provides detailed execution results

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
├── storage.py           # Local storage management
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

3. If you have saved preferences:
   - Choose to use all saved preferences (y)
   - Select specific preferences to update (select)
   - Enter all new preferences (n)

4. The agent will:
   - Analyze the project structure
   - Determine Spring Boot version
   - Create a migration plan
   - Extract and store recipe_id
   - Execute necessary upgrades

## Migration Workflow

1. **Project Analysis** (`analyzeProject`)
   - Identifies JDK version
   - Detects Spring Boot version
   - Analyzes project structure
   - Validates project compatibility

2. **Migration Planning** (`migrationPlan`)
   - Generates migration strategy
   - Determines upgrade recipe
   - Extracts and stores recipe_id
   - Validates migration feasibility

3. **Upgrade Execution** (`modUpgradeAll`)
   - Uses stored recipe_id from migration plan
   - Applies the upgrade recipe
   - Handles necessary migrations
   - Reports upgrade results
   - Validates successful completion
   - Provides clear success/failure status

## State Management

The system implements robust state management:

1. **User Preferences**
   - Stored in local storage
   - Persists between sessions
   - Can be updated selectively

2. **Recipe ID Handling**
   - Automatic extraction from migrationPlan
   - Multiple fallback mechanisms
   - Stored in both memory and state
   - Validated before use

3. **Context Management**
   - Maintains workflow state
   - Tracks execution progress
   - Stores tool responses
   - Manages error states

## Available Tools

### Moderne Tools
- `modUpgradeAll` - Upgrades projects using specified recipe
  - Parameters:
    - project_path: string
    - recipe_id: string (automatically handled)

### Maven Tools
- `analyzeProject` - Analyzes Maven project
  - Parameters:
    - project_path: string
- `migrationPlan` - Generates migration plan
  - Returns:
    - recipe_id
    - target_version
    - migration details

## Error Handling

The system provides comprehensive error handling:
- Input validation with clear messages
- Tool execution monitoring and retries
- LLM response validation and fallbacks
- State consistency checks
- Recipe ID validation and extraction
- Graceful failure handling

## Logging

Logs are stored in the `logs` directory:
- `cognitive_agent_*.log` - Main agent logs
- `decision_*.log` - Decision making logs
- Includes:
  - Tool execution results
  - Recipe ID extraction
  - State updates
  - Error messages
  - Workflow progress

## Best Practices

1. Always provide absolute paths for project locations
2. Ensure all required tools are installed and accessible
3. Verify Java and Maven versions match project requirements
4. Check logs for detailed execution information
5. Review saved preferences before use
6. Monitor migration plan output
7. Verify recipe ID extraction success

## Troubleshooting

Common issues and solutions:

1. **LLM Connection Error**
   - Verify GEMINI_API_KEY in .env
   - Check internet connection
   - Verify API quota availability

2. **Tool Execution Failed**
   - Ensure Moderne CLI is installed
   - Verify Maven installation
   - Check project path exists
   - Validate tool permissions

3. **Invalid Project Structure**
   - Verify pom.xml exists
   - Check Java version compatibility
   - Validate Spring Boot version

4. **Recipe ID Issues**
   - Ensure migrationPlan executed successfully
   - Check logs for extraction errors
   - Verify recipe ID format
   - Try clearing saved state

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - See LICENSE file for details

## Completion States

The agent provides clear completion states:

1. **Successful Migration**
   - All upgrades applied successfully
   - Positive success status in response
   - Clear success message shown
   - Process ends immediately

2. **Failed Migration**
   - Upgrade errors detected
   - Negative success status
   - Detailed error message provided
   - Process terminates with failure

3. **Incomplete Migration**
   - Maximum iterations reached
   - Last action status checked
   - Appropriate status message shown
   - Logs available for review

## Response Format

The agent provides structured responses:

```
FINAL_ANSWER: [Migration completed successfully. All upgrades were applied.]
```
or
```
FINAL_ANSWER: [Migration failed. Please check the logs for details.]
```

These responses indicate:
- Final migration status
- Success/failure of upgrades
- Next steps if needed
- Reference to logs for details 