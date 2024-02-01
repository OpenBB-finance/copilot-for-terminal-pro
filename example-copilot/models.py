from pydantic import BaseModel, Field
from enum import Enum


class RoleEnum(str, Enum):
    ai = "ai"
    human = "human"


class LlmMessage(BaseModel):
    role: RoleEnum = Field(
        description="The role of the entity that is creating the message"
    )
    content: str = Field(description="The content of the message")


class AgentQueryRequest(BaseModel):
    query: str
    context: str | None = Field(default=None, description="")
    messages: list[LlmMessage] | None = Field(
        default=None, description="A list of prior messages."
    )
