import json
import os
from pathlib import Path
from fastapi.testclient import TestClient
from llama_copilot.main import app
import pytest
from unittest.mock import Mock, patch

from common.testing import capture_stream_response

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


def _mock_stream_generator(tokens: list[str]):
    async def mock_async_streamed_str():
        async def _async_generator():
            for token in tokens:
                yield token

        return _async_generator()

    return mock_async_streamed_str


@pytest.fixture
def mock_get_llm():
    """Since we cannot run Ollama in CI, we mock the LLM's responses if we're in CI.

    This doesn't help us test the Ollama output via CI directly, but at least it
    helps us test that the inputs to the custom copilot are handled correctly.

    If this test is running outside of CI (eg. locally), then the LLM is not
    mocked.
    """
    if os.environ.get("CI", "false").lower() == "true":
        with patch("llama_copilot.main._get_llm") as mock_get_llm:
            yield mock_get_llm
    else:
        # If not in CI, we don't want to mock the LLM, so we just yield a dummy
        # mock that does nothing.
        yield Mock()


def test_query(mock_get_llm):
    test_payload_path = (
        Path(__file__).parent.parent.parent / "test_payloads" / "single_message.json"
    )
    test_payload = json.load(open(test_payload_path))

    mock_get_llm.return_value = _mock_stream_generator(["2"])

    response = test_client.post("/v1/query", json=test_payload)
    event_name, captured_stream = capture_stream_response(response.text)
    assert response.status_code == 200
    assert event_name == "copilotMessageChunk"
    assert "2" in captured_stream


def test_query_conversation(mock_get_llm):
    test_payload_path = (
        Path(__file__).parent.parent.parent / "test_payloads" / "multiple_messages.json"
    )
    test_payload = json.load(open(test_payload_path))

    mock_get_llm.return_value = _mock_stream_generator(["4"])

    response = test_client.post("/v1/query", json=test_payload)
    event_name, captured_stream = capture_stream_response(response.text)
    assert response.status_code == 200
    assert event_name == "copilotMessageChunk"
    assert "4" in captured_stream


def test_query_with_context(mock_get_llm):
    test_payload_path = (
        Path(__file__).parent.parent.parent
        / "test_payloads"
        / "message_with_context.json"
    )
    test_payload = json.load(open(test_payload_path))

    mock_get_llm.return_value = _mock_stream_generator(["pizza"])

    response = test_client.post("/v1/query", json=test_payload)
    event_name, captured_stream = capture_stream_response(response.text)
    assert response.status_code == 200
    assert event_name == "copilotMessageChunk"
    assert "pizza" in captured_stream.lower()


def test_query_no_messages():
    test_payload = {
        "messages": [],
    }
    response = test_client.post("/v1/query", json=test_payload)
    "messages list cannot be empty" in response.text
