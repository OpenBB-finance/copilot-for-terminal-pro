import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import os
import openai
from openai import OpenAI

OPENAI_API_KEY = "***REMOVED***"

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
openai.api_key = OPENAI_API_KEY

client = OpenAI()

from typing import List, Union, Dict

from pydantic import BaseModel

class GohAnalystOutput(BaseModel):
    output: str

class GohAnalystInput(BaseModel):
    query: str
    context: str

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


@app.get("/")
def read_root():
    return {"Info": "Bring my collection of copilots to the OpenBB Terminal Pro"}


@app.get("/copilots.json")
def get_copilots():
    """Widgets configuration file for the OpenBB Terminal Pro"""
    return JSONResponse(
        content=json.load((Path(__file__).parent.resolve() / "copilots.json").open())
    )


@app.post("/gohanalyst", response_model=GohAnalystOutput)
def gohanalyst(body: GohAnalystInput):
    """Return output from GohAnalyst"""
    query = body.query
    context = body.context

    completion = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "You are an expert financial analyst with 30 years of experience. You write answers that are extremely concise and short, but slightly sarcastic."},
            {"role": "user", "content": f"## Context\n\nYou have the following context available to answer your query:\n${context}\n\n## User query\n{query}"}
        ]
    )
    result = completion.choices[0].message.content

    print(result)
    
    # convert df to json
    return {"output": result}