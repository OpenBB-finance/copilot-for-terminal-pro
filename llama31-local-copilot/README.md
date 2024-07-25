# Local Llama 3.1 LLM Copilot
This example provides a basic copilot that runs locally on your machine via
[Ollama](https://ollama.com/).

## Overview
This implementation utilizes a FastAPI application to serve as the backend for
the copilot. The core functionality is powered by `magentic`, a robust, minimal
framework for working with Large Language Models (LLMs).

You're not limited to our setup! If you have preferences for different APIs or
LLM frameworks, feel free to adapt this implementation. The key is to adhere to
the schema defined by the `/query` endpoint and the specifications in
`copilot.json`.

This repository is a starting point. It's designed for you to experiment,
modify, and extend. You can build copilots with various capabilities, like RAG
(Retrieval-Augmented Generation), function calling, and more, all hosted on your
backend.

## Getting started

Here's how to get your copilot up and running:

### Prerequisites
For this example to work, you will need at least 8GB of VRAM (or 8GB unified
memory, in the case of Apple Silicon Macs) on your machine.

Ensure that you have installed `ollama`, and have the service running locally on your
computer.

Also ensure you have poetry, a tool for dependency management and packaging in
Python.

### Installation and Running

1. Clone this repository to your local machine.
2. Install the necessary dependencies:

``` sh
poetry install --no-root
```

3.Start the API server:

``` sh
poetry run uvicorn llama_copilot.main:app --port 7777 --reload
```

This command runs the FastAPI application, making it accessible on your network.

### Testing the Example Copilot
The example copilot has a small, basic test suite to ensure it's
working correctly. As you develop your copilot, you are highly encouraged to
expand these tests.

You can run the tests with:

``` sh
pytest tests
```

Note: Ollama must be installed and running to run the tests.

### Accessing the Documentation

Once the API server is running, you can view the documentation and interact with
the API by visiting: http://localhost:7777/docs
