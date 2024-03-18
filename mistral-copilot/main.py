import re
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from magentic import (
    AssistantMessage,
    FunctionCall,
    SystemMessage,
    UserMessage,
    chatprompt,
    AsyncStreamedStr,
)
from magentic.chat_model.litellm_chat_model import LitellmChatModel

from dotenv import load_dotenv
from models import AgentQueryRequest, FunctionCallResponse, RoleEnum
from prompts import SYSTEM_PROMPT


load_dotenv(".env")
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:1420",
    "http://localhost:5050",
    "https://pro.openbb.dev",
    "https://pro.openbb.co",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sanitize_message(message: str) -> str:
    """Sanitize a message by escaping forbidden characters."""
    cleaned_message = re.sub(r"(?<!\{)\{(?!{)", "{{", message)
    cleaned_message = re.sub(r"(?<!\})\}(?!})", "}}", cleaned_message)
    return cleaned_message


@app.get("/copilots.json")
def get_copilot_description():
    """Widgets configuration file for the OpenBB Terminal Pro"""
    return JSONResponse(
        content=json.load(open((Path(__file__).parent.resolve() / "copilots.json")))
    )


@app.post("/v1/query")
async def query(request: AgentQueryRequest) -> StreamingResponse:
    """Query the Copilot."""

    # Prepare messages
    chat_messages = []
    for message in request.messages:
        if message.role == RoleEnum.human:
            chat_messages.append(UserMessage(sanitize_message(message.content)))
        elif message.role == RoleEnum.ai:
            chat_messages.append(AssistantMessage(sanitize_message(message.content)))

    # Prepare context
    context_str = ""
    if request.context:
        if isinstance(request.context, list):
            for context_widget in request.context:
                context_str += str(context_widget.model_dump_json()) + "\n\n"
        elif isinstance(request.context, str):
            context_str = request.context

    # Prepare widgets
    widgets_str = ""
    if request.widgets:
        for widget in request.widgets:
            widgets_str += str(widget.model_dump_json()) + "\n\n"

    @chatprompt(
        SystemMessage(SYSTEM_PROMPT),
        *chat_messages,
        model=LitellmChatModel(
            "mistral/mistral-large-latest",
            temperature=0.1,
        ),
    )
    async def copilot(widgets: str, context: str) -> FunctionCall | AsyncStreamedStr:
        ...

    # Query LLM
    response = await copilot(widgets=widgets_str, context=context_str)

    # Parse response
    if isinstance(response, FunctionCall):
        function_call_response = (
            response()
        )  # Create the response by calling the function
        return StreamingResponse(
            function_call_response.model_dump_json(), media_type="text/event-stream"
        )
    return StreamingResponse(response, media_type="text/event-stream")


def llm_retrieve_widget_data(widget_uuid: str) -> FunctionCallResponse:
    """Retrieve the data for a widget given a widget_uuid.

    Only retrieve a widget if its UUID exists.
    Do not retrieve a widget if its UUID does not exist.
    """
    return FunctionCallResponse(
        function="get_widget_data", input_arguments={"widget_uuid": widget_uuid}
    )
