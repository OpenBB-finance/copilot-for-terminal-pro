import re
import json
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from magentic import (
    AssistantMessage,
    FunctionCall,
    FunctionResultMessage,
    SystemMessage,
    UserMessage,
    chatprompt,
    AsyncStreamedStr,
)
from magentic.chat_model.mistral_chat_model import MistralChatModel
from sse_starlette.sse import EventSourceResponse

from dotenv import load_dotenv
from common.models import (
    AgentQueryRequest,
    FunctionCallResponse,
    FunctionCallSSE,
    FunctionCallSSEData,
    LlmFunctionCall,
    LlmFunctionCallResult,
    RoleEnum,
)
from .prompts import SYSTEM_PROMPT


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


async def create_response_stream(
    response: AsyncStreamedStr | FunctionCall,
) -> AsyncGenerator[dict, None]:
    if isinstance(response, AsyncStreamedStr):
        async for chunk in response:
            yield {"event": "copilotMessageChunk", "data": json.dumps({"delta": chunk})}
    elif isinstance(response, FunctionCall):
        function_call_response: FunctionCallResponse = response()
        yield FunctionCallSSE(
            event="copilotFunctionCall",
            data=FunctionCallSSEData(
                function=function_call_response.function,
                input_arguments=function_call_response.input_arguments,
                copilot_function_call_arguments=function_call_response.input_arguments,
            ),
        ).model_dump()


@app.get("/copilots.json")
def get_copilot_description():
    """Widgets configuration file for the OpenBB Terminal Pro"""
    return JSONResponse(
        content=json.load(open((Path(__file__).parent.resolve() / "copilots.json")))
    )


@app.post("/v1/query")
async def query(request: AgentQueryRequest) -> EventSourceResponse:
    """Query the Copilot."""

    # Define LLM functions
    def _llm_get_widget_data(widget_uuid: str) -> FunctionCallResponse:
        """Retrieve data from a widget, only if it's UUID is listed in the context.

        # Usage
        - This function can only be called if a valid widget UUID is present.
        - This function can NOT be called if a valid widget UUID is not present.
        """
        print("Function call")
        print(widget_uuid)
        return FunctionCallResponse(
            function="get_widget_data", input_arguments={"widget_uuid": widget_uuid}
        )

    # Prepare messages
    chat_messages = []
    for message in request.messages:
        if message.role == RoleEnum.human:
            if isinstance(message.content, str):
                chat_messages.append(UserMessage(sanitize_message(message.content)))
            else:
                raise HTTPException(
                    status_code=500, detail="Human messages can only be string."
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
        functions = [_llm_get_widget_data]
    else:
        functions = None

    @chatprompt(
        SystemMessage(SYSTEM_PROMPT),
        *chat_messages,
        functions=functions,
        model=MistralChatModel(
            model="mistral-large-2407",
            temperature=0.2,
        ),
    )
    async def copilot(
        widgets: str, context: str
    ) -> FunctionCall | AsyncStreamedStr: ...

    # Query LLM
    response = await copilot(widgets=widgets_str, context=context_str)

    return EventSourceResponse(
        content=create_response_stream(response),
        media_type="text/event-stream",
    )


def llm_retrieve_widget_data(widget_uuid: str) -> FunctionCallResponse:
    """Retrieve the data for a widget given a widget_uuid.

    Only retrieve a widget if its UUID exists.
    Do not retrieve a widget if its UUID does not exist.
    """
    return FunctionCallResponse(
        function="get_widget_data", input_arguments={"widget_uuid": widget_uuid}
    )
