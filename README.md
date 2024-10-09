# Bring your own Copilot to Terminal Pro

Welcome to the example repository for integrating a custom copilot into the OpenBB Terminal Pro!

This guide provides everything you need to create and add your own custom copilots, enhancing the capabilities of Terminal Pro in a way that fits your unique requirements.

## Overview

To integrate a custom copilot, you'll need to create a backend that interacts with Terminal Pro. Terminal Pro will send requests to your copilot, which will respond accordingly via Server-Sent Events ([SSEs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)). This ensures real-time responses and seamless communication between Terminal Pro and your custom copilot.

This guide will cover:

- Understanding the message and context structure
- How to handle function calls and interact with widgets
- Explanation of the copilot configuration (copilots.json)
- Examples of common use cases and scenarios

## Requirements for Compatibility

Custom copilots are expected to follow the defined schema for queries, SSE responses, and function calling. These requirements ensure seamless integration with OpenBB Terminal Pro.

## How Terminal Pro submits requests to your Copilot

Terminal Pro will submit POST requests to your custom copilot's `/v1/query` endpoint. These requests will contain information such as the user's message  (`messages`), any additional `context`, `widgets` data, user-uploaded files (`user_files`), relevant URLs (`urls`), and more. Your copilot must respond via SSEs for real-time interaction.

### API Request Schema Example

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

- messages: The chat history, including both user and assistant messages.
- context: Structured context to include additional information like personal data or metadata.
- widgets: A list of widgets currently in use by the user for function calling.
- user_files: UUIDs of uploaded files.
- urls: A list of URLs for web search functionality.

**Note:** Terminal Pro makes requests to this endpoint each time the user interacts with the copilot.

## How the Copilot Responds

Your custom copilot must respond to Terminal Pro's request using Server-Sent Events (SSEs).

Here's a breakdown of how your copilot can respond:

Sending a `copilotMessageChunk` Event

The copilotMessageChunk event is used to stream back generated tokens (partial responses) to Terminal Pro. These responses are streamed as they are generated, providing a seamless experience to the use

``` json
{
  "event": "copilotMessageChunk",
  "data": {
    "delta": "<token>"
  }
}
```

These delta values are streamed by Terminal Pro to form the final message.

## Adding Function Calling to your Custom Copilot

If your copilot needs to request data (e.g., widget data) or perform a specific function, you will emit a copilotFunctionCall event. This instructs Terminal Pro to take further action on the client's side.

Function Call Example `copilotFunctionCall`:

```json
{
  "event": "copilotFunctionCall",
  "data": {
    "function": "get_widget_data",
    "input_arguments": {
      "widget_uuid": "c276369e-e469-4689-b5fe-3f8c76f7c45a"
    }
  }
}
```

### Handling Function Calls in Your Copilot

Once a function call is required, the copilot should send a copilotFunctionCall event. Terminal Pro will execute the specified function and return the result. You must handle these function calls correctly to continue the conversation.

For example, if your copilot requests widget data:

- Emit the copilotFunctionCall SSE.
- Wait for Terminal Pro to provide the result.
- Include the result in subsequent responses to complete the flow.

**Note:** The copilot must also include the function call response in any further requests to maintain context.

## Understanding the Copilot Configuration (copilots.json)

To integrate your custom copilot with Terminal Pro, you need to configure the copilots.json file. This file defines how your custom copilot connects with Terminal Pro, including which features it supports and where requests should be sent.

Here's an example copilots.json configuration:

```json
{
  "example_copilot": {
    "name": "Mistral Example Co. Copilot",
    "description": "AI-powered financial copilot that uses Mistral Large as its LLM.",
    "image": "https://github.com/OpenBB-finance/copilot-for-terminal-pro/assets/14093308/5c7518ad-3997-4fd7-9549-909eddd272c4",
    "hasStreaming": true,
    "hasFunctionCalling": true,
    "hasDocuments": false,
    "endpoints": {
      "query": "http://localhost:7777/v1/query"
    }
  }
}
```

- `example_copilot`: This is the unique identifier for your copilot.
- `name`: The display name of your copilot. This name is used within the Terminal Pro UI to allow users to identify and select the copilot.
- `description`: A short description of your copilot.
- `image`: A URL to an image representing your copilot. This image will be displayed in the Terminal Pro interface.
- `hasStreaming`: A boolean value indicating if the copilot supports streaming responses via SSEs. If set to `true`, Terminal Pro will expect the copilot to return responses in real-time chunks.
- `hasFunctionCalling`: A boolean value indicating if the copilot supports function calling. If set to `true`, Terminal Pro will be able to make specific function calls such as retrieving widget data or accessing client-side resources.
- `hasDocuments`: A boolean value indicating if the copilot supports processing documents, such as user-uploaded files. If set to `false`, document processing features will not be available for this copilot.
- `endpoints`: A set of URLs that Terminal Pro will use to interact with your copilot. In this example:
  - `query`: The URL for the main endpoint where Terminal Pro sends user queries (POST requests). This endpoint is where your copilot listens for incoming messages and responds accordingly.

## Example Scenarios and Use Cases

### Requesting Widget Data

If a user asks, "What is the current stock price of AAPL?" , Terminal Pro will send the active widgets in your dashboard alongside your query. Your copilot can then emit a `copilotFunctionCall` to retrieve this data if there is a widget that can provide the information.

Request:

```json
{
  "messages": [
    {
      "role": "human",
      "content": "What is the current stock price of AAPL?"
    }
  ],
  "widgets": [
    {
      "uuid": "c276369e-e469-4689-b5fe-3f8c76f7c45a",
      "name": "stock price quote widget",
      "description": "Contains the current stock price of a ticker",
      "metadata": {
        "ticker": "AAPL"
      }
    }
  ]
}
```

Copilot Response:

```json
{
  "event": "copilotFunctionCall",
  "data": {
    "function": "get_widget_data",
    "input_arguments": {
      "widget_uuid": "c276369e-e469-4689-b5fe-3f8c76f7c45a"
    }
  }
}
```

### Including Explicit Context

If a user wants the Copilot to use data from a specific widget, the user can explicitly add it as context inside the UI. Terminal Pro will then include this context in the query to the copilot.

<img src="https://openbb-assets.s3.amazonaws.com/docs/custom_copilot/custom_copilot_chat_example.gif" alt="query custom copilot" />

Request:

```json
{
  "allow_direct_retrieval": true,
  "context": [
    {
      "uuid": "b61f8b98-47ad-436f-99c3-5b74d7a4e364",
      "name": "Historical Stock Price",
      "description": "Contains historical stock prices for a specific ticker.",
      "metadata": {
        "ticker": "AAPL"
      },
      "content": null
    }
  ],
  "custom_direct_retrieval_endpoints": [],
  "force_findb_search": false,
  "force_web_search": false,
  "messages": [
    {
      "role": "human",
      "content": "What is the most recent OHLCV of AAPL?"
    }
  ],
  "urls": [],
  "use_docs": false,
  "user_files": false,
  "widgets": []
}
```

In this scenario:

- The `allow_direct_retrieval` is true, which means that the copilot can attempt to directly fetch data using the context or available endpoints.
- The `context` contains information about historical stock prices for AAPL, which the copilot can use to answer the question.
- `force_findb_search` and `force_web_search` are both false, meaning that the copilot should not perform any additional searches. In our case, our Copilot doesn't even support these features.
- `messages` contain the user's current question, maintaining the conversational flow.
  
The copilot will utilize the available context to fetch the necessary OHLCV data, and if required, make a function call or utilize additional retrieval methods.

``` text
The most recent Open, High, Low, Close, and Volume (OHLCV) data for Apple Inc. (AAPL) is:

- **Open:** $224.50
- **High:** $225.69
- **Low:** $224.055
- **Close:** $224.14
- **Volume:** 12,952,911

This is as of October 7, 2024.
```