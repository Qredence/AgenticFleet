#!/usr/bin/env python3
import asyncio
import json

import websockets


async def test_websocket():
    """Test the WebSocket connection to the /ws/chat endpoint."""
    uri = "ws://localhost:8002/ws/chat"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:
        # Receive the welcome message
        welcome = await websocket.recv()
        welcome_data = json.loads(welcome)
        print(f"Received welcome: {welcome_data}")

        # Receive the settings message
        settings = await websocket.recv()
        settings_data = json.loads(settings)
        print(f"Received settings: {settings_data}")

        # Send a test message
        test_message = {
            "type": "TextMessage",
            "content": "Hello, this is a test message!",
            "source": "user",
        }
        print(f"Sending message: {test_message}")
        await websocket.send(json.dumps(test_message))

        # Wait for responses (will continue until we disconnect)
        print("Waiting for responses (press Ctrl+C to stop)...")
        try:
            while True:
                response = await websocket.recv()
                response_data = json.loads(response)
                print(f"Received: {response_data}")

                # If this is a request for user input, respond with something
                if response_data.get("type") == "UserInputRequestedEvent":
                    input_response = {
                        "type": "TextMessage",
                        "content": "This is my response to the input request",
                        "source": "user",
                    }
                    print(f"Sending response to input request: {input_response}")
                    await websocket.send(json.dumps(input_response))
        except KeyboardInterrupt:
            print("Test finished by user")


if __name__ == "__main__":
    asyncio.run(test_websocket())
