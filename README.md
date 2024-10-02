# Bring your own Copilot to Terminal Pro

Welcome to the example repository for integrating a custom copilot into OpenBB
Terminal Pro. This repository provides reference implementations to help you
create and add your own custom copilots to enhance the capabilities of Terminal
Pro.

## Requirements for Compatibility

Custom copilots are expected to follow the defined schema for queries, SSE responses, and function calling. These requirements ensure seamless integration with OpenBB Terminal Pro.

### Query Endpoint

Custom copilots should expose a `/v1/query` endpoint that accepts POST requests. The request body should include a list of `messages` and, optionally, `context`, `widgets`, `user_files`, and `urls`.

**Request Example:**

```json
{
  "messages": [
    {
      "role": "human",
      "content": "Hi there. Who are you?"
    }
  ],
  "context": null,
  "widgets": [],
  "urls": []
}
```

* messages: The chat history, including both user and assistant messages.
* context: Structured context to include additional information like personal data or metadata.
* widgets: A list of widgets currently in use by the user for function calling.
* user_files: UUIDs of uploaded files.
* urls: A list of URLs for web search functionality.

## Server-Sent Events (SSEs)

The copilot must stream its response via SSEs, with two primary event types: `copilotMessageChunk` and `copilotFunctionCall`.

### `copilotMessageChunk` Event

This event streams partial responses (tokens) back to the client as they are generated.

Event Schema:

```json
{
  "event": "copilotMessageChunk",
  "data": {
    "delta": "<token>"
  }
}
```

### `copilotFunctionCall` Event

This event indicates that the copilot requires a function call, typically for retrieving data from the client or widgets.

Event Schema:

```json
{
  "event": "copilotFunctionCall",
  "data": {
    "function": "<function_name>",
    "input_arguments": {
      "<argument_name>": "<value>"
    }
  }
}
```

## Function Calling

Custom copilots can request data from widgets or perform operations on client-side resources. Function calls are returned as a single SSE event and include the function name and any required arguments.

Function Call Example:

```json
{
  "function": "get_widget_data",
  "input_arguments": {
    "widget_uuid": "c276369e-e469-4689-b5fe-3f8c76f7c45a"
  }
}
```

The function call response must then be included in subsequent queries to complete the flow.

### SSE Parsing

Clients must parse the SSEs and concatenate message chunks to form the full response. For function calls, clients should execute the requested function and include the result in the next API request.

```python
def handle_stream(response):
    for chunk in response.iter_text():
        if "event: copilotMessageChunk" in chunk:
            delta = ast.literal_eval(chunk.split("data: ")[1])["delta"]
            print(delta, end='', flush=True)
        elif "event: copilotFunctionCall" in chunk:
            function_call = ast.literal_eval(chunk.split("data: ")[1])
            print(function_call)
```
