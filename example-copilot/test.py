import httpx

BASE_URL = "http://localhost:7777"

# Query, without context.
print("\n\nTesting query:")
print("==============")
with httpx.stream(
    "POST", f"{BASE_URL}/query", json={"query": "What is your name?"}
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)


# Query, with context.
print("\n\nTesting query with context:")
print("==============")
with httpx.stream(
    "POST",
    f"{BASE_URL}/query",
    json={
        "query": "What is the current stock price of TSLA?",
        "context": "The current price of TSLA is $99.95",
    },
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)


# Query, with history.
print("\n\nTesting query with chat history:")
print("==============")
with httpx.stream(
    "POST",
    f"{BASE_URL}/query",
    json={
        "query": "Ach.",
        "messages": [
            {"role": "human", "content": "Knock knock..."},
            {"role": "ai", "content": "Who's there?"},
        ],
    },
) as response:
    for chunk in response.iter_text():
        print(chunk, end="", flush=True)
