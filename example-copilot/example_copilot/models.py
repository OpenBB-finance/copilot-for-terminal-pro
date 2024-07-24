from typing import Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class RoleEnum(str, Enum):
    ai = "ai"
    human = "human"


class LlmMessage(BaseModel):
    role: RoleEnum = Field(
        description="The role of the entity that is creating the message"
    )
    content: str = Field(description="The content of the message")


class ContextualWidget(BaseModel):
    uuid: str = Field(description="The UUID of the widget.")
    name: str = Field(description="The name of the widget.")
    description: str = Field(
        description="A description of the data contained in the widget"
    )
    metadata: dict[Any, Any] | None = Field(
        default=None,
        description="Additional widget metadata (eg. the selected ticker, etc)",
    )
    content: str = Field(description="The data content of the widget")


class AgentQueryRequest(BaseModel):
    messages: list[LlmMessage] = Field(
        description="A list of messages to submit to the copilot."
    )
    context: str | list[ContextualWidget] | None = Field(
        default=None,
        description="Additional context. Can either be a string, or a list of user-selected widgets.",
    )
    use_docs: bool = Field(
        default=None, description="Set True to use uploaded docs when answering query."
    )

    @validator("messages")
    def check_messages_not_empty(cls, value):
        if not value:
            raise ValueError("messages list cannot be empty.")
        return value
