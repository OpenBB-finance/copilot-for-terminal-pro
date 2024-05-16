import httpx

BASE_URL = "http://localhost:7777"

# Query, without context.
print("\n\nTesting query:")
print("==============")
with httpx.stream(
    "POST",
    f"{BASE_URL}/v1/query",
    json={"messages": [{"role": "human", "content": "What is your name?"}]},
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)


# Query, with context.
print("\n\nTesting query with context:")
print("==============")
with httpx.stream(
    "POST",
    f"{BASE_URL}/v1/query",
    json={
        "messages": [
            {
                "role": "human",
                "content": "From the context, what is MONTY planning to invest in?",
            }
        ],
        "context": [
            {
                "uuid": "12345-abcde",
                "name": "Earnings transcript widget",
                "description": "Earnings transcript for MONTY",
                "metadata": {"ticker": "MONTY"},
                "content": "MONTY is planning on investing in shrubberies.",
            }
        ],
    },
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)


# Query, with history.
print("\n\nTesting query with chat history:")
print("==============")
with httpx.stream(
    "POST",
    f"{BASE_URL}/v1/query",
    json={
        "messages": [
            {
                "role": "human",
                "content": "Only provide Yes or No as your answer and NOTHING ELSE. Is AAPL a famous company?",
            },
            {"role": "ai", "content": "Yes."},
            {"role": "human", "content": "What about TSLA?"},
        ],
    },
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)

# Query, with function calling.
print("\n\nTesting query with function calling:")
print("==============")
with httpx.stream(
    "POST",
    f"{BASE_URL}/v1/query",
    json={
        "messages": [
            {"role": "human", "content": "What is the current stock price of TSLA?"}
        ],
        "widgets": [
            {
                "uuid": "12345-abcde",
                "name": "Stock price widget",
                "description": "Contains the stock price of a ticker.",
                "metadata": {"ticker": "TSLA"},
            },
            {
                "uuid": "7890-wxyz",
                "name": "Stock price widget",
                "description": "Contains the stock price of a ticker.",
                "metadata": {"ticker": "AMZN"},
            },
        ],
    },
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)


# Query, with function calling, and tool result
print("\n\nTesting query with function call and tool result:")
print("==============")
with httpx.stream(
    "POST",
    f"{BASE_URL}/v1/query",
    json={
        "messages": [
            {"role": "human", "content": "What is the current stock price of TSLA?"},
            # The appended function could should be the same as the initial "function call" response.
            {
                "role": "ai",
                "content": '{"function": "get_widget_data", "input_arguments": {"widget_uuid": "7890-zxcq"}}',
            },
            # Then provide the actual function call result
            {
                "role": "tool",
                "function": "get_widget_data",
                "input_arguments": {"widget_uuid": "7890-zxcq"},
                "content": "$99.95",
            },
        ],
        "widgets": [
            {
                "uuid": "12345-abcde",
                "name": "Stock price widget",
                "description": "Contains the stock price of a ticker.",
                "metadata": {"ticker": "TSLA"},
            },
            {
                "uuid": "7890-wxyz",
                "name": "Stock price widget",
                "description": "Contains the stock price of a ticker.",
                "metadata": {"ticker": "AMZN"},
            },
        ],
    },
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)
