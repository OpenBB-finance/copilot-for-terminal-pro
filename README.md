# Bring your own Copilot to Terminal

Welcome to the example repository for integrating a custom copilot into the OpenBB Terminal!

This guide provides everything you need to create and add your own custom copilots, enhancing the capabilities of Terminal Pro in a way that fits your unique requirements.

## Overview

To integrate a custom copilot, you'll need to create a custom copilot backend that OpenBB Terminal connects to. OpenBB Terminal will send requests to your backend, which will respond with various Server-Sent Events ([SSEs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)). This ensures real-time responses and seamless communication between Terminal Pro and your custom copilot.

## How OpenBB Terminal submits requests to your Copilot

When using a custom copilot, OpenBB Terminal will make POST requests to your custom copilot's `/v1/query` endpoint. These requests will contain information such as the current conversation's messages, any explicitly-added context, information about widgets on the currently-active dashboard, URLs to retrieve, etc.

### API Request Schema

```json
{
  "messages": [
    {
      "role": "tool",
      "function": "string",
      "input_arguments": {},
      "data": {
        "content": "string"
      }
    },
    {
      "role": "tool",
      "function": "string",
      "input_arguments": {},
      "data": {
        "content": "string"
      },
      "content": "string"
    }
  ],
  "context": [
    {
      "uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "string",
      "description": "string",
      "data": {
        "content": "string"
      },
      "metadata": {}
    }
  ],
  "allow_direct_retrieval": true,
  "widgets": [
    {
      "uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "string",
      "description": "string",
      "metadata": {}
    }
  ],
  "custom_direct_retrieval_endpoints": [
    {
      "sourceName": "string",
      "widgetId": "string",
      "name": "string",
      "description": "string",
      "endpoint": "string",
      "params": [
        {
          "paramName": "string",
          "type": "string",
          "description": "string",
          "value": "string",
          "options": [
            {}
          ],
          "label": "string"
        }
      ]
    }
  ],
  "urls": [
    "string"
  ],
  "force_web_search": true,
  "force_findb_search": true
}
```

- messages: The chat history, including both user and assistant messages as well as function calls and function call results.
- context: Widgets that have been added as explicit context by the user. [Optional]
- allow_direct_retrieval: A boolean value indicating whether the copilot can directly retrieve data.
- widgets: A list of widgets currently in use by the user for function calling. [Optional]
- custom_direct_retrieval_endpoints: A list of custom endpoints for direct data retrieval. [Optional]
- urls: A list of URLs for web search functionality. [Optional]
- force_web_search: A boolean value indicating whether the copilot should perform a web search. [Optional]
- force_findb_search: A boolean value indicating whether the copilot should perform a FinDB search. [Optional]

**Note:** OpenBB Terminal makes requests to this endpoint each time the user submits a query to your custom Copilot.

## Components of a custom copilot

To integrate your custom copilot with Terminal Pro, you need to configure the copilots.json file. This file defines how your custom copilot connects with Terminal Pro, including which features it supports and where requests should be sent.

- `example_copilot`: This is the unique identifier for your copilot.
- `name`: The display name of your copilot. This name is used within the Terminal Pro UI to allow users to identify and select the copilot.
- `description`: A short description of your copilot.
- `image`: A URL to an image representing your copilot. This image will be displayed in the Terminal Pro interface.
- `hasStreaming`: A boolean value indicating if the copilot supports streaming responses via SSEs. If set to `true`, Terminal Pro will expect the copilot to return responses in real-time chunks.
- `hasFunctionCalling`: A boolean value indicating if the copilot supports function calling. If set to `true`, Terminal Pro will be able to make specific function calls such as retrieving widget data or accessing client-side resources.
- `hasDocuments`: A boolean value indicating if the copilot supports processing documents, such as user-uploaded files. If set to `false`, document processing features will not be available for this copilot.
- `endpoints`: A set of URLs that Terminal Pro will use to interact with your copilot. In this example:
  - `query`: The URL for the main endpoint where Terminal Pro sends user queries (POST requests). This endpoint is where your copilot listens for incoming messages and responds accordingly.

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

## Copilot Responses

Your custom copilot must respond to OpenBB Terminal's request using Server-Sent Events (SSEs).

OpenBB Terminal accepts the following SSEs:

- `copilotMessageChunk`: Used to return streamed copilot tokens (partial responses) back to OpenBB Terminal. These responses can be streamed as they are generated.
- `copilotFunctionCall`: Used to request data (e.g., widget data) or perform a specific function. This instructs Terminal Pro to take further action on the client's side.

Sending a `copilotMessageChunk` Event

``` json
{
  "event": "copilotMessageChunk",
  "data": {
    "delta": "<token>"
  }
}
```

## Function Calling

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

The widget UUID is obtained from the OpenBB Terminal's request payload. It sends all widgets that are currently active on the dashboard to the copilot.

Example payload snippet:

```json
{
  ...
  "widgets": [
    {
      "uuid": "c276369e-e469-4689-b5fe-3f8c76f7c45a",
      "name": "Price Performance",
      "description": "Interactive chart for asset price performance",
      "metadata": {
        "symbol": "TSLA",
        "source": "Financial Modelling Prep",
        "lastUpdated": 1728925996386
      }
    }
  ]
  ...
}
```

Currently, the only function call supported by the OpenBB Terminal is `get_widget_data`, which retrieves data from a specific widget.

### Handling Function Calls in Your Copilot

Once a function call is required, the copilot should send a copilotFunctionCall event. Terminal Pro will execute the specified function and return the result. You must handle these function calls correctly to continue the conversation.

Let's walk through the process:

The copilot receives a request from Terminal Pro that has the following query

```json
{
  "allow_direct_retrieval": true,
  "context": [],
  "custom_direct_retrieval_endpoints": [
    {
      "description": "",
      "category": "My Data",
      "subCategory": ""
    }
  ],
  "force_findb_search": false,
  "force_web_search": false,
  "messages": [
    {
      "role": "human",
      "content": "What is the latest price of AAPL?"
    }
  ],
  "urls": [],
  "widgets": [
    {
      "uuid": "38181a68-9650-4940-84fb-a3f29c8869f3",
      "name": "Historical Stock Price",
      "description": "Historical Stock Price",
      "metadata": {
        "symbol": "AAPL",
        "source": "Financial Modelling Prep",
        "lastUpdated": 1728994470324
      }
    }
  ]
}
```

As there is a widget available for the requested data, the copilot should emit a `copilotFunctionCall` event to retrieve the data.

```json
{
  "event": "copilotFunctionCall",
  "data": {
    "function": "get_widget_data",
    "input_arguments": {
      "widget_uuid": "38181a68-9650-4940-84fb-a3f29c8869f3"
    }
  }
}
```

Then Terminal Pro will respond with the data from the widget:

```json
{
  "custom_direct_retrieval_endpoints": [
    {
      "description": "",
      "category": "My Data",
      "subCategory": ""
    }
  ],
  "messages": [
    {
      "role": "human",
      "content": "What is the latest price of AAPL?"
    },
    {
      "role": "ai",
      "content": "{\"function\":\"get_widget_data\",\"input_arguments\":{\"widget_uuid\":\"38181a68-9650-4940-84fb-a3f29c8869f3\"},\"copilot_function_call_arguments\":{\"widget_uuid\":\"38181a68-9650-4940-84fb-a3f29c8869f3\"}}"
    },
    {
      "role": "tool",
      "function": "get_widget_data",
      "content": "",
      "copilot_function_call_arguments": {
        "widget_uuid": "38181a68-9650-4940-84fb-a3f29c8869f3"
      },
      "input_arguments": {
        "widget_uuid": "38181a68-9650-4940-84fb-a3f29c8869f3"
      },
      "data_source": "backend",
      "data": [
        {
          "date": "2024-10-14T00:00:00-04:00",
          "open": "..."
        }
      ]
    }
  ],
  "widgets": [
    {
      "uuid": "38181a68-9650-4940-84fb-a3f29c8869f3",
      "name": "Historical Stock Price",
      "description": "Historical Stock Price",
      "metadata": {
        "symbol": "AAPL",
        "source": "Financial Modelling Prep",
        "lastUpdated": 1728994470324
      }
    }
  ]
}
```

Now, we have the data from the widget, and the copilot can use this data to respond to the user's query.
This result will be included in the subsequent responses to complete the flow.

**Note:** The copilot must also include the function call response in any further requests to maintain context.

## Example requests and responses

### Simple Query

Chatting with the copilot is straightforward. Here's an example of a simple query:

```json
{
  "messages": [
    {
      "role": "human",
      "content": "Hi there. Who are you?"
    }
  ],
}
```

### Including specific content

If a user wants the Copilot to use data from a specific widget, the user can explicitly add it as context inside the UI. OpenBB Terminal will then include this context in the query to the copilot.

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
