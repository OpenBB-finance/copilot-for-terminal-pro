import re
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


from dotenv import load_dotenv
from models import AgentQueryRequest
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


@app.post("/query")
def query(request: AgentQueryRequest) -> StreamingResponse:
    """Query the Copilot."""
    print(request)
    chat_messages = (
        [
            (message.role, sanitize_message(message.content))
            for message in request.messages
        ]
        if request.messages
        else []
    )

    template = ChatPromptTemplate.from_messages(
        [("system", SYSTEM_PROMPT), *chat_messages, ("human", "User query: {query}")]
    )

    output_parser = StrOutputParser()
    model = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.1)

    chain = template | model | output_parser
    stream = chain.stream(
        {
            "query": request.query,
            "context": request.context,
        }
    )
    return StreamingResponse(stream, media_type="text/event-stream")
