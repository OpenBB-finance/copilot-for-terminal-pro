# Bring your own Copilot to Terminal

Welcome to the example repository for integrating custom copilots into the OpenBB Terminal.

This repository provides everything you need to build and add your own custom
copilots to OpenBB Copilot.

Here are a few common reasons why you might want to build your own copilot:
- You have a unique data source that you don't want to add as a custom integration to OpenBB Terminal.
- You want to use a specific LLM.
- You want to use a local LLM.
- You want a Copilot that is self-hosted on your infrastructure.
- You are running on-premise in a locked-down environment that doesn't allow data to leave your VPC.


## Overview

To integrate a custom copilot, you'll need to create a custom API backend that
OpenBB Terminal connects to. OpenBB Terminal will make requests to your backend, allowing you to interact with your custom copilot from Terminal Pro.

Your custom API backend will respond with Server-Sent Events
([SSEs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)).

## Handling requests from OpenBB Terminal

OpenBB Terminal will make POST requests to the `query` endpoint defined in your
`copilots.json` file (more on this later). The payload of this request will
contain data such as the current conversation's messages, any explicitly-added
context, information about widgets on the currently-active dashboard, URLs to
retrieve, and so on.

### API Request Schema

The core of the query request schema you must implement is as follows:

```python
{
  "messages": [  # <-- the chat messages between the user and the copilot (including function calls and results)
    {
      "role": "human",  # <-- each message has a role: "human", "ai", or "tool"
      "content": "Hi there."  # <-- the content of the message
    }
  ],
  "context": [  # <-- explicitly added context by the user (optional)
    {
      "uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # <-- the UUID of the widget
      "name": "<widget name>",  # <-- the name of the widget
      "description": "<widget description>",  # <-- the description of the widget
      "data": {
        "content": "<data>"  # <-- the data of the widget
      },
      "metadata": {
        "<metadata key>": "<metadata value>",  # <-- the metadata of the widget
        ...
      }
    },
    ...
  ],
  "widgets": [  # <-- the widgets currently visible on the active dashboard on Terminal Pro (optional)
    {
      "uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # <-- the UUID of the widget
      "name": "<widget name>",  # <-- the name of the widget
      "description": "<widget description>",  # <-- the description of the widget
      "metadata": {
        "<metadata key>": "<metadata value>",  # <-- the metadata of the widget
        ...
      }
    },
    ...
  ],
}
```

We'll go over each of these fields in more detail below.

#### `messages`
This is the list of messages between the user and the copilot. This includes the
user's messages, the copilot's messages, function calls, and function call
results. Each message has a `role` and `content`.

The simplest example is when no function calling is involved, which simply
consists of an array of `human` and `ai` messages.

OpenBB Terminal automatically appends all return `ai` messages (from your Copilot)
to the `messages` array of any follow-up request.

```python
# Only one human message
{
  "messages": [
    {
      "role": "human", 
      "content": "Hi there."
    }
  ],
  ...
}
```

```python
# Multiple messages
{
  "messages": [
    {
      "role": "human", 
      "content": "Hi there."
    },
    {
      "role": "ai", 
      "content": "Hi there, I'm a copilot. How are you?"
    },
    {
      "role": "human", 
      "content": "I'm fine, thank you. What is the weather in Tokyo?"
    }
  ],
  ...
}
```

Function calls to Terminal Pro (such as when retrieving widget data), as well as the results of those function calls (containing the widget data), are also included in the `messages` array. For information on function calling, see the "Function Calling" section below.

#### `context`

This is an optional array of widget data that will be sent by OpenBB Terminal
when widgets have been added as context explicitly by the user. This happens
when the user clicks on the "Add as Context" button on a widget in OpenBB
Terminal.

<img src="https://github.com/user-attachments/assets/6c84dc5b-7615-4483-a956-67ac526d5800" alt="explicit_context" width="70%"/>

The `context` field works as follows:

```python
{
  ...
  "context": [
    {
      "uuid": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # <-- each widget has a UUID
      "name": "Analyst Estimates",
      "description": "Contains analyst estimates for a ticker",
      "data": {
        "content": "<data>"  # <-- the data of the widget could either be a JSON string or plaintext (you must choose how to handle this in your copilot)
      },
      "metadata": {  # <-- additional metadata about the widget
        "symbol": "AAPL",
        "period": "quarter",
        "source": "Financial Modelling Prep",
        "lastUpdated": 1728998071322
      }
    },
    {
      "uuid": "8b2e5f79-3a1d-4c9e-b6f8-1e7d2a9c0b3d",  # <-- the context can have multiple widgets
      "name": "Earnings Transcripts",  
      "description": "Contains earnings transcripts for a ticker",
      "data": {
        "content": "<data>"  # <-- the data of the widget
      },
      "metadata": {
        "symbol": "AAPL",
        "period": "quarter",
        "source": "Intrinio",
        "lastUpdated": 1728998071322
      }
    },
    ...
  ],
  ...
}
```

#### `widgets`

This is an array of widgets that are currently visible on the active dashboard
on Terminal Pro.
**This is only useful if you're planning on implementing function calling in
*your custom copilot** (which is recommended, but not required), which
allows it to request widget data from the user's currently-active dashboard on
OpenBB Terminal.

```python
{
  ...
  "widgets": [
    {
      "uuid": "c276369e-e469-4689-b5fe-3f8c76f7c45a",
      "name": "Stock Price Quote Widget",
      "description": "Contains the current stock price of a ticker",
      "metadata": {
        "ticker": "AAPL"
      }
    },
    {
      "uuid": "9f8e7d6c-5b4a-3c2e-1d0f-9e8d7c6b5a4b",
      "name": "Financial Ratios Widget",
      "description": "Displays key financial ratios for a company",
      "metadata": {
        "ticker": "AAPL",
        "period": "TTM"
      }
    },
    ...
  ],
  ...
}
```

## Responding to OpenBB Terminal

Your custom copilot must respond to OpenBB Terminal's request using Server-Sent Events (SSEs).

OpenBB Terminal can process the following SSEs:

- `copilotMessageChunk`: Used to return streamed copilot tokens (partial responses) back to OpenBB Terminal. These responses can be streamed as they are generated.
- `copilotFunctionCall`: Used to request data (e.g., widget data) or perform a specific function. This instructs Terminal Pro to take further action on the client's side. This is only necessary if you're planning on implementing function calling in your custom copilot.

#### `copilotMessageChunk`
The message chunk SSE has the following format:

```
event: copilotMessageChunk
data: {"delta":"H"}  # <-- the `data` field must be a JSON object.
```
The `delta` must be a string, but can be of any length. We suggest streaming
back each chunk you receive from your LLM as soon as it's generated as a `delta`.

For example, if you wanted to stream back the message "Hi", you would send the
following SSEs:

```
event: copilotMessageChunk
data: {"delta":"H"}

event: copilotMessageChunk
data: {"delta":"i"}

event: copilotMessageChunk
data: {"delta":"!"}
```

#### `copilotFunctionCall` (only required for function calling)
The function call SSE has the following format:

```
event: copilotFunctionCall
data: {"function":"get_widget_data","input_arguments":{"widget_uuid":"c276369e-e469-4689-b5fe-3f8c76f7c45a"}}
```

Again, the `data` field must be a JSON object. The `function` field is the name
of the function to be called (currently only `get_widget_data` is supported),
and the `input_arguments` field is a dictionary of arguments to be passed to the
function. For the `get_widget_data` function, the only required argument is
`widget_uuid`, which is the UUID of the widget to retrieve data for (from one of
the UUIDs in the `widgets` array of the request).


## Configuring your custom copilot for OpenBB Terminal (`copilots.json`)

To integrate your custom copilot with Terminal Pro, you need to configure and a
serve a `copilots.json` file. This file defines how your custom copilot connects
with Terminal Pro, including which features it supports and where requests
should be sent.

Here is an example copilots.json configuration:

```python
{
  "example_copilot": { # <-- the ID of your copilot
    "name": "Mistral Example Co. Copilot", # <-- the display name of your copilot
    "description": "AI-powered financial copilot that uses Mistral Large as its LLM.", # <-- a short description of your copilot
    "image": "<url>", # <-- a URL to an image icon for your copilot
    "hasStreaming": true, # <-- whether your copilot supports streaming responses via SSEs. This must always be true.
    "hasFunctionCalling": true, # <-- whether your copilot supports function calling
    "endpoints": {
      "query": "<url>" # <-- the URL that Terminal Pro will send requests to. For example, "http://localhost:7777/v1/query"
    }
  }
}
```

Your `copilots.json` file must be served at `<your-host>/copilots.json`, for example, `http://localhost:7777/copilots.json`.

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
