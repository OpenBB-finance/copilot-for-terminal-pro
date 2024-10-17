from ast import literal_eval
import json
from fastapi.testclient import TestClient
from example_copilot.main import app
import pytest
from pathlib import Path

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


def _capture_stream_response(event_stream: str):
    captured_stream = ""
    lines = event_stream.split("\n")
    for line in lines:
        if line.startswith("event:"):
            event_type = line.split("event:")[1].strip()
        if event_type == "copilotMessageChunk" and line.startswith("data:"):
            data_payload = line.split("data:")[1].strip()
            data_dict_ = literal_eval(data_payload)
            captured_stream += data_dict_["delta"]
    return captured_stream


def test_query():
    test_payload_path = (
        Path(__file__).parent.parent.parent / "test_payloads" / "single_message.json"
    )
    test_payload = json.load(open(test_payload_path))

    response = test_client.post("/v1/query", json=test_payload)
    captured_stream = _capture_stream_response(response.text)
    assert response.status_code == 200
    assert "2" in captured_stream


def test_query_conversation():
    test_payload_path = (
        Path(__file__).parent.parent.parent / "test_payloads" / "multiple_messages.json"
    )
    test_payload = json.load(open(test_payload_path))

    response = test_client.post("/v1/query", json=test_payload)
    captured_stream = _capture_stream_response(response.text)
    assert response.status_code == 200
    assert "4" in captured_stream


def test_query_with_context():
    test_payload_path = (
        Path(__file__).parent.parent.parent
        / "test_payloads"
        / "message_with_context.json"
    )
    test_payload = json.load(open(test_payload_path))
    response = test_client.post("/v1/query", json=test_payload)
    captured_stream = _capture_stream_response(response.text)
    assert response.status_code == 200
    assert "pizza" in captured_stream.lower()


def test_query_no_messages():
    test_payload = {
        "messages": [],
    }
    response = test_client.post("/v1/query", json=test_payload)
    "messages list cannot be empty" in response.text
