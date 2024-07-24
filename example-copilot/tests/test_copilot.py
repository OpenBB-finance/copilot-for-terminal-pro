from ast import literal_eval
from fastapi.testclient import TestClient
from example_copilot.main import app
import pytest
import json

test_client = TestClient(app)

def _capture_stream_response(event_stream: str):
    captured_stream = ""
    lines = event_stream.split("\n")
    for line in lines:
        if line.startswith("event:"):
            event_type = line.split("event:")[1].strip()
        if line.startswith("data:"):
            data_payload = line.split("data:")[1].strip()
            data_dict_ = literal_eval(data_payload)
            captured_stream += data_dict_["delta"]
    return captured_stream
        


def test_query():
    test_payload = {"messages": [{"role": "human", "content": "what is 1 + 1?"}]}
    response = test_client.post("/v1/query", json=test_payload)
    captured_stream = _capture_stream_response(response.text)
    assert response.status_code == 200
    assert "2" in captured_stream

