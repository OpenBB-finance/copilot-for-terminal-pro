# FinDB Example Copilot
This example provides a GPT-4o-mini copilot that is able to query the vector
database. 

## Overview
This implementation utilizes a FastAPI application to serve as the backend for
the copilot. The core functionality is powered by `magentic`, a more recent framework
for working with Large Language Models (LLMs).

You're not limited to our setup! If you have preferences for different APIs or
LLM frameworks, feel free to adapt this implementation. The key is to adhere to
the schema defined by the `/v1/query` endpoint and the specifications in
`copilot.json`.

This repository is a starting point. It's designed for you to experiment,
modify, and extend. You can build copilots with various capabilities, like RAG
(Retrieval-Augmented Generation), function calling, and more, all hosted on your
backend.

## Getting started

Here's how to get your copilot up and running:

### Prerequisites

Ensure you have poetry, a tool for dependency management and packaging in
Python, as well as your Mistral API key.

### Installation and Running

1. Clone this repository to your local machine.
2. Set the Mistral API key as an environment variable in your .bashrc or .zshrc file:

``` sh
# in .zshrc or .bashrc
export OPENAI_API_KEY=<your-api-key>
```

3. Install the necessary dependencies:

``` sh
poetry install --no-root
```

4.Start the API server:

``` sh
uvicorn findb_copilot.main:app --host 0.0.0.0 --port 7777 --reload
```

This command runs the FastAPI application, making it accessible on your network.

### Accessing the Documentation

Once the API server is running, you can view the documentation and interact with
the API by visiting: http://localhost:7777/docs
