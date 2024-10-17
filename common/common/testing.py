from ast import literal_eval


def capture_stream_response(event_stream: str) -> tuple[str, str]:
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
