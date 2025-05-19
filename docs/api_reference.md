# API Reference

This document provides detailed information about AgenticFleet's API endpoints and usage.

## Core Components

### ApplicationManager

The main application manager class that handles the AgenticFleet instance.

```python
from agentic_fleet.core.application import ApplicationManager

app_manager = ApplicationManager(
    host="localhost",
    port=8000,
    debug=False
)
```

#### Methods

- `start()`: Start the application
- `stop()`: Stop the application
- `restart()`: Restart the application
- `status()`: Get application status

### Agent System

#### MagenticOneGroupChat

The core agent coordination system.

```python
from agentic_fleet.core.agents import MagenticOneGroupChat

chat = MagenticOneGroupChat(
    model="gpt-4",
    temperature=0.7,
    agents=["web_surfer", "file_surfer", "coder", "executor"]
)
```

#### Available Agents

1. **WebSurfer**

   ```python
   from agentic_fleet.agents import WebSurfer

   web_surfer = WebSurfer(
       browser="chromium",
       headless=True
   )
   ```

2. **FileSurfer**

   ```python
   from agentic_fleet.agents import FileSurfer

   file_surfer = FileSurfer(
       workspace_dir="./workspace"
   )
   ```

3. **Coder**

   ```python
   from agentic_fleet.agents import Coder

   coder = Coder(
       language="python",
       style_guide="pep8"
   )
   ```

4. **Executor**

   ```python
   from agentic_fleet.agents import Executor

   executor = Executor(
       sandbox=True,
       timeout=30
   )
   ```

## HTTP API Endpoints

### Authentication

#### OAuth Login

```http
POST /api/auth/login
Content-Type: application/json

{
    "provider": "github",
    "code": "oauth_code"
}
```

#### Logout

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

### Chat

#### Start Chat Session

```http
POST /api/chat/start
Authorization: Bearer <token>
Content-Type: application/json

{
    "model": "gpt-4",
    "temperature": 0.7,
    "agents": ["web_surfer", "file_surfer"]
}
```

#### Send Message

```http
POST /api/chat/message
Authorization: Bearer <token>
Content-Type: application/json

{
    "session_id": "session_uuid",
    "content": "Your message here",
    "attachments": []
}
```

#### Get Chat History

```http
GET /api/chat/history/{session_id}
Authorization: Bearer <token>
```

### File Operations

#### Upload File

```http
POST /api/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file_data>
```

#### List Files

```http
GET /api/files/list
Authorization: Bearer <token>
```

### System Status

#### Get System Status

```http
GET /api/system/status
Authorization: Bearer <token>
```

#### Get Agent Status

```http
GET /api/system/agents
Authorization: Bearer <token>
```

## WebSocket API

### Chat WebSocket

Connect to real-time chat:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat/{session_id}");
```

#### Message Format

```json
{
  "type": "message",
  "content": "Message content",
  "timestamp": "2025-02-24T15:57:56+01:00",
  "agent": "web_surfer"
}
```

## Error Handling

All API endpoints return standard error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  }
}
```

Common error codes:

- `AUTH_REQUIRED`: Authentication required
- `INVALID_TOKEN`: Invalid authentication token
- `SESSION_NOT_FOUND`: Chat session not found
- `AGENT_ERROR`: Agent execution error
- `RATE_LIMIT`: Rate limit exceeded

## Rate Limiting

API endpoints are rate-limited by default:

- 100 requests per minute per IP
- 1000 requests per hour per user
- WebSocket connections limited to 5 per user

## Versioning

The API follows semantic versioning. Current version: v1.
Access specific API versions using the `/api/v1/` prefix.
