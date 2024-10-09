import re
import json
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from magentic import (
    chatprompt,
    SystemMessage,
    UserMessage,
    AssistantMessage,
    AsyncStreamedStr,
)
from magentic.chat_model.litellm_chat_model import LitellmChatModel
from sse_starlette.sse import EventSourceResponse

from dotenv import load_dotenv
from .models import AgentQueryRequest
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


async def create_message_stream(
    content: AsyncStreamedStr,
) -> AsyncGenerator[dict, None]:
    async for chunk in content:
        yield {"event": "copilotMessageChunk", "data": json.dumps({"delta": chunk})}


@app.get("/copilots.json")
def get_copilot_description():
    """Widgets configuration file for the OpenBB Terminal Pro"""
    return JSONResponse(
        content=json.load(open((Path(__file__).parent.resolve() / "copilots.json")))
    )


@app.post("/v1/query")
async def query(request: AgentQueryRequest) -> EventSourceResponse:
    """Query the Copilot."""

    chat_messages = []
    for message in request.messages:
        if message.role == "ai":
            chat_messages.append(
                AssistantMessage(content=sanitize_message(message.content))
            )
        elif message.role == "human":
            chat_messages.append(UserMessage(content=sanitize_message(message.content)))

    chat_messages.insert(1, UserMessage(content=sanitize_message("# Context\n" + str(request.context))))

    @chatprompt(
        SystemMessage(SYSTEM_PROMPT),
        *chat_messages,
        model=LitellmChatModel(model="ollama_chat/llama3.1:8b-instruct-q6_K"),
    )
    async def _llm() -> AsyncStreamedStr:
        ...


    result = await _llm()
    return EventSourceResponse(
        content=create_message_stream(result),
        media_type="text/event-stream",
    )
