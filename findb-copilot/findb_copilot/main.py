import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, AsyncGenerator

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from magentic import (
    AssistantMessage,
    AsyncStreamedStr,
    FunctionCall,
    FunctionResultMessage,
    OpenaiChatModel,
    SystemMessage,
    UserMessage,
    chatprompt,
)
from sse_starlette.sse import EventSourceResponse

from .models import (
    AgentQueryRequest,
    RoleEnum,
)
from .prompts import SYSTEM_PROMPT
from .services import VectorSearchService

load_dotenv(".env")
FIN_DB_HOST_URL = os.getenv("FIN_DB_HOST_URL")
if not FIN_DB_HOST_URL:
    raise ValueError("FIN_DB_HOST_URL not set")

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


async def create_message_stream(
    content: AsyncStreamedStr,
) -> AsyncGenerator[dict, None]:
    async for chunk in content:
        yield {"event": "copilotMessageChunk", "data": {"delta": chunk}}


@app.get("/copilots.json")
def get_copilot_description():
    """Widgets configuration file for the OpenBB Terminal Pro"""
    return JSONResponse(content=json.load(open((Path(__file__).parent.resolve() / "copilots.json"))))


@app.post("/v1/query")
async def query(
    request: AgentQueryRequest,
    vector_search_service: Annotated[VectorSearchService, Depends(VectorSearchService)],
) -> EventSourceResponse:
    """Query the Copilot."""

    current_date = datetime.now().strftime("%Y-%m-%d")

    # Define LLM functions
    async def _llm_search_documents(query: str, symbol: str) -> str:
        """Use natural language to query a database containing sec filings and earning transcripts about a symbol."""
        results = await vector_search_service.search(query=query, symbol=symbol)
        return results

    # Prepare messages
    chat_messages = []
    for message in request.messages:
        if message.role == RoleEnum.human:
            if isinstance(message.content, str):
                chat_messages.append(UserMessage(sanitize_message(message.content)))
            else:
                raise HTTPException(status_code=500, detail="Human messages can only be string.")
        elif message.role == RoleEnum.ai:
            if isinstance(message.content, str):
                chat_messages.append(AssistantMessage(sanitize_message(message.content)))
            else:
                raise HTTPException(
                    status_code=500,
                    detail="LLM messages can only be strings",
                )

    # Prepare context
    context_str = ""
    if request.context:
        if isinstance(request.context, list):
            for context_widget in request.context:
                context_str += str(context_widget.model_dump_json()) + "\n\n"
        elif isinstance(request.context, str):
            context_str = request.context

    response = None
    while not isinstance(response, AsyncStreamedStr):

        @chatprompt(
            SystemMessage(SYSTEM_PROMPT),
            *chat_messages,
            functions=[_llm_search_documents],
            model=OpenaiChatModel(
                model="gpt-4o-mini",
                temperature=0.2,
            ),
        )
        async def copilot(context: str, today: str = current_date) -> FunctionCall | AsyncStreamedStr: ...

        # Query LLM
        response = await copilot(context=context_str)

        # Handle function call
        if isinstance(response, FunctionCall):
            chat_messages.append(AssistantMessage(response))
            chat_messages.append(FunctionResultMessage(content=await response(), function_call=response))
        else:
            break

    return EventSourceResponse(
        content=create_message_stream(response),
        media_type="text/event-stream",
    )
