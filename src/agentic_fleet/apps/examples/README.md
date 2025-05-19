# Basic Agent Chat Example

This example demonstrates how to use AgenticFleet with Chainlit UI and AutoGen agents to create an interactive chat application with multiple specialized agents.

## Features

- 🤖 Multiple specialized agents (WebSurfer, FileSurfer, Coder, Executor)
- 🌐 Web search and information gathering
- 📁 File operations and management
- 💻 Code generation and execution
- 🚀 Real-time streaming responses
- 📊 Task progress tracking
- 🔄 Automatic resource cleanup

## Prerequisites

1. Python 3.10 or higher
2. Azure OpenAI API access
3. Required Python packages (installed via pip):
   - chainlit
   - autogen-ext
   - autogen-agentchat
   - python-dotenv
   - pyyaml

## Setup

1. Create a `.env` file in the project root with your Azure OpenAI credentials:

   ```env
   AZURE_OPENAI_API_KEY=your_api_key
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_OPENAI_API_VERSION=your_api_version
   ```

2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Install browser automation dependencies (for WebSurfer):
   ```bash
   playwright install chromium
   ```

## Usage

1. Start the chat application:

   ```bash
   chainlit run basic_agent_chat.py
   ```

2. Open your browser and navigate to `http://localhost:8000`

3. Start chatting! You can:
   - Ask for web searches
   - Request file operations
   - Generate and execute code
   - Get help with various tasks

## Configuration

The `config.yaml` file contains settings for:

- Model parameters
- Agent configurations
- UI preferences
- Logging settings

Modify these settings to customize the behavior of your agents.

## Example Interactions

1. Web Search:

   ```
   User: "Search for the latest Python best practices"
   ```

2. Code Generation:

   ```
   User: "Write a Python function to calculate Fibonacci numbers"
   ```

3. File Operations:
   ```
   User: "Create a new file called example.py and write a hello world program"
   ```

## Error Handling

The example includes comprehensive error handling:

- Setup failures
- Agent processing errors
- Resource cleanup issues

All errors are logged and displayed in the UI with appropriate messages.

## Best Practices

1. Always use environment variables for sensitive data
2. Configure appropriate timeouts for agents
3. Implement proper error handling
4. Clean up resources when done
5. Monitor agent logs for issues

## Contributing

Feel free to:

- Report issues
- Suggest improvements
- Submit pull requests

## License

This example is part of AgenticFleet and is licensed under the same terms as the main project.
