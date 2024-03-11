from typing import Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class RoleEnum(str, Enum):
    ai = "ai"
    human = "human"
    tool = "tool"


class LlmFunctionCall(BaseModel):
    role: RoleEnum = RoleEnum.tool
    function: str = Field(description="The name of the called function.")
    input_arguments: dict[str, Any] | None = Field(
        default=None, description="The input arguments passed to the function"
    )
    content: str = Field(description="The result of the function call.")


class LlmMessage(BaseModel):
    role: RoleEnum = Field(
        description="The role of the entity that is creating the message"
    )
    content: str = Field(
        description="The content of the message or the result of a function call."
    )


class Widget(BaseModel):
    uuid: str = Field(description="The UUID of the widget.")
    name: str = Field(description="The name of the widget.")
    description: str = Field(
        description="A description of the data contained in the widget"
    )
    metadata: dict[Any, Any] | None = Field(
        default=None,
        description="Additional widget metadata (eg. the selected ticker, etc)",
    )


class ContextualWidget(Widget):
    content: str = Field(description="The data content of the widget")


class AgentQueryRequest(BaseModel):
    messages: list[LlmFunctionCall | LlmMessage] = Field(
        description="A list of messages to submit to the copilot."
    )
    context: str | list[ContextualWidget] | None = Field(
        default=None, description="Additional context."
    )
    use_docs: bool = Field(
        default=None, description="Set True to use uploaded docs when answering query."
    )
    widgets: list[Widget] = Field(
        default=None, description="A list of widgets for the copilot to consider."
    )

    @validator("messages")
    def check_messages_not_empty(cls, value):
        if not value:
            raise ValueError("messages list cannot be empty.")
        return value


class FunctionCallResponse(BaseModel):
    function: str = Field(description="The name of the function to call.")
    input_arguments: dict | None = Field(
        default=None, description="The input arguments to the function."
    )
