from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class RoleEnum(str, Enum):
    ai = "ai"
    human = "human"
    tool = "tool"


class LlmMessage(BaseModel):
    role: RoleEnum = Field(description="The role of the entity that is creating the message")
    content: str = Field(description="The content of the message or the result of a function call.")


class Widget(BaseModel):
    uuid: str = Field(description="The UUID of the widget.")
    name: str = Field(description="The name of the widget.")
    description: str = Field(description="A description of the data contained in the widget")
    metadata: dict[Any, Any] | None = Field(
        default=None,
        description="Additional widget metadata (eg. the selected ticker, etc)",
    )


class ContextualWidget(Widget):
    content: str = Field(description="The data content of the widget")


class AgentQueryRequest(BaseModel):
    messages: list[LlmMessage] = Field(description="A list of messages to submit to the copilot.")
    context: str | list[ContextualWidget] | None = Field(default=None, description="Additional context.")

    @field_validator("messages")
    def check_messages_not_empty(cls, value):
        if not value:
            raise ValueError("messages list cannot be empty.")
        return value


class VectorSearchResult(BaseModel):
    content: str
    symbol: str
    page_number: int | None = None
    chunk_number: int | None = None
    company_name: str
    document_date: datetime
    document_type: str
    form_type: Literal["10-Q", "10-K"] | None = None
    fiscal_quarter: str
    fiscal_year: int
    period: str
    s3_uri: str
