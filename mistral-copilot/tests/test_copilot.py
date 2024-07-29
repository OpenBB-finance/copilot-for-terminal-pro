from ast import literal_eval
from fastapi.testclient import TestClient
from mistral_copilot.main import app
import pytest

test_client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_sse_starlette_appstatus_event():
    """
    Fixture that resets the appstatus event in the sse_starlette app.
    Should be used on any test that uses sse_starlette to stream events.
    """
    # See https://github.com/sysid/sse-starlette/issues/59
    from sse_starlette.sse import AppStatus

    AppStatus.should_exit_event = None


def _capture_stream_response(event_stream: str) -> tuple[str, str]:
    if "copilotFunctionCall" in event_stream:
        event_name = "copilotFunctionCall"
        event_stream = event_stream.split("\n")
        data_payload = event_stream[1].split("data:")[-1].strip()
        return event_name, data_payload

    captured_stream = ""
    event_name = ""
    lines = event_stream.split("\n")
    for line in lines:
        if line.startswith("event:"):
            event_type = line.split("event:")[1].strip()
        if event_type == "copilotMessageChunk" and line.startswith("data:"):
            event_name = "copilotMessageChunk"
            data_payload = line.split("data:")[1].strip()
            data_dict_ = literal_eval(data_payload)
            captured_stream += data_dict_["delta"]
    return event_name, captured_stream


def test_query():
    test_payload = {"messages": [{"role": "human", "content": "what is 1 + 1?"}]}
    response = test_client.post("/v1/query", json=test_payload)
    event_name, captured_stream = _capture_stream_response(response.text)
    assert response.status_code == 200
    assert event_name == "copilotMessageChunk"
    assert "2" in captured_stream


def test_query_conversation():
    test_payload = {
        "messages": [
            {"role": "human", "content": "what is 1 + 1?"},
            {"role": "ai", "content": "2"},
            {"role": "human", "content": "what is 2 + 2?"},
        ]
    }
    response = test_client.post("/v1/query", json=test_payload)
    event_name, captured_stream = _capture_stream_response(response.text)
    assert response.status_code == 200
    assert event_name == "copilotMessageChunk"
    assert "4" in captured_stream


def test_query_with_context():
    test_payload = {
        "messages": [
            {"role": "human", "content": "What is my favourite food?"},
        ],
        "context": [
            {
                "uuid": "ff6368ec-a397-4baf-9f5a-fecd9fd797a3",
                "name": "favourite_food",
                "description": "The user's favourite food",
                "content": "pizza",
            }
        ],
    }
    response = test_client.post("/v1/query", json=test_payload)
    event_name, captured_stream = _capture_stream_response(response.text)
    assert response.status_code == 200
    assert event_name == "copilotMessageChunk"
    assert "pizza" in captured_stream.lower()


def test_query_no_messages():
    test_payload = {
        "messages": [],
    }
    response = test_client.post("/v1/query", json=test_payload)
    "messages list cannot be empty" in response.text


def test_query_function_call():
    test_payload = {
        "messages": [{"role": "human", "content": "what is the weather in london?"}],
        "widgets": [
            {
                "uuid": "ff6368ec-a397-4baf-9f5a-fecd9fd797a3",
                "name": "get_weather",
                "description": "Get the weather for a location",
            }
        ],
    }
    response = test_client.post("/v1/query", json=test_payload)
    event_name, captured_stream = _capture_stream_response(response.text)

    function_call = literal_eval(captured_stream)

    assert response.status_code == 200
    assert event_name == "copilotFunctionCall"
    assert function_call["function"] == "get_widget_data"
    assert function_call["input_arguments"] == {
        "widget_uuid": "ff6368ec-a397-4baf-9f5a-fecd9fd797a3"
    }
