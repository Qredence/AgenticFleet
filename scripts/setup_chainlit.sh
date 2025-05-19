#!/bin/bash
# Setup script for Chainlit and dependencies with MCP support

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

echo "===== Installing Chainlit v2.4.4.00 with MCP Support ====="

# Force numpy to a version that works with autogen-ext and the project
echo "Installing compatible numpy version..."
pip install "numpy>=1.26,<2.0" --force-reinstall

# Install Chainlit with the specific version
echo "Installing Chainlit v2.4.4.00..."
pip install chainlit==2.4.4.00

# Install MCP packages
echo "Installing MCP dependencies..."
pip install "mcp-sdk>=0.2.0"
pip install "mcp-api-client>=0.1.0"
pip install "chainlit[mcp]>=2.4.4"

# Install autogen dependencies with specific versions
echo "Installing AutoGen dependencies with exact versions..."
pip install "autogen-agentchat==0.5.1" --no-deps
pip install "autogen-core==0.5.1" --no-deps

# Install autogen-ext with exact versions and pre-releases allowed
echo "Installing AutoGen extensions (allowing pre-releases)..."
if command -v uv &> /dev/null; then
    # If uv is available
    uv pip install "autogen-ext==0.5.1" "autogen-ext[magentic-one]==0.5.1" --prerelease=allow --no-deps
    uv pip install "magika==0.6.1rc2" --prerelease=allow --no-deps
else
    # Fallback to pip
    pip install "autogen-ext==0.5.1" "autogen-ext[magentic-one]==0.5.1" --pre --no-deps
    pip install "magika==0.6.1rc2" --pre --no-deps
fi

# Install remaining project dependencies
echo "Installing remaining project dependencies..."
pip install -e . --no-deps

echo "===== Setup Complete ====="
echo ""
echo "You can now run the Chainlit app with either:"
echo "1. chainlit run src/agentic_fleet/chainlit_app.py"
echo "2. python -m src.agentic_fleet.chainlit_app"
echo ""
echo "For MCP connections:"
echo "1. Click 'Add MCP' in the UI settings panel"
echo "2. Select 'stdio' to connect to local tools"
echo "3. Enter tool name and command (e.g., 'math-tool' and 'npx @modelcontextprotocol/math-tool')"
