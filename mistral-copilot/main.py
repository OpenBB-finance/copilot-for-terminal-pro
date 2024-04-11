import os
import re
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from magentic import (
    AssistantMessage,
    FunctionCall,
    FunctionResultMessage,
    OpenaiChatModel,
    ParallelFunctionCall,
    SystemMessage,
    UserMessage,
    chatprompt,
    AsyncStreamedStr,
)

from dotenv import load_dotenv
from models import (
    AgentQueryRequest,
    FunctionCallResponse,
    LlmFunctionCall,
    LlmFunctionCallResult,
    RoleEnum,
)
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

    # Define LLM functions
    def _llm_get_widget_data(widget_uuid: str) -> FunctionCallResponse:
        """Retrieve data from a widget, only if it's UUID is listed in the context.

        # Usage
        - This function can only be called if a valid widget UUID is present.
        - This function can NOT be called if a valid widget UUID is not present.
        """

        return FunctionCallResponse(
            function="get_widget_data", input_arguments={"widget_uuid": widget_uuid}
        )

    # Prepare messages
    chat_messages = []
    for message in request.messages:
        print(message)
        if message.role == RoleEnum.human:
            if isinstance(message.content, str):
                chat_messages.append(UserMessage(sanitize_message(message.content)))
            else:
                raise HTTPException(
                    status_code=500, detail="Human messages must only be string."
                )
        elif message.role == RoleEnum.ai:
            if isinstance(message.content, str):
                chat_messages.append(
                    AssistantMessage(sanitize_message(message.content))
                )
            elif isinstance(message.content, LlmFunctionCall):
                function_call = FunctionCall(
                    function=_llm_get_widget_data,
                    **message.content.input_arguments,
                )
                chat_messages.append(AssistantMessage(function_call))
        elif message.role == RoleEnum.tool:
            if isinstance(message, LlmFunctionCallResult):
                chat_messages.append(
                    FunctionResultMessage(
                        content=sanitize_message(message.content),
                        function_call=function_call,  # type: ignore
                    )
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Tool message must have LlmFunctionCallResult.",
                )

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
        functions=[_llm_get_widget_data],
        model=OpenaiChatModel(
            base_url="https://api.mistral.ai/v1/",
            api_key=os.getenv("MISTRAL_API_KEY"),
            model="mistral-large-latest",
            temperature=0.2,
        ),
    )
    async def copilot(
        widgets: str, context: str
    ) -> ParallelFunctionCall | AsyncStreamedStr:
        ...

    # Query LLM
    response = await copilot(widgets=widgets_str, context=context_str)

    # Parse response
    if isinstance(response, FunctionCall):
        function_call_response = (
            response()
        )  # Create the response by calling the function
        return StreamingResponse(
            function_call_response.model_dump_json(),
            media_type="text/event-stream",  # type: ignore
        )
    return StreamingResponse(response, media_type="text/event-stream")  # type: ignore


def llm_retrieve_widget_data(widget_uuid: str) -> FunctionCallResponse:
    """Retrieve the data for a widget given a widget_uuid.

    Only retrieve a widget if its UUID exists.
    Do not retrieve a widget if its UUID does not exist.
    """
    return FunctionCallResponse(
        function="get_widget_data", input_arguments={"widget_uuid": widget_uuid}
    )
