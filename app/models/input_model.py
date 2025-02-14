from langchain.pydantic_v1 import BaseModel, Field
from typing import List
from langchain_core.messages import BaseMessage


class Input(BaseModel):
    input: str
    chat_history: List[BaseMessage] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "location"}},
    )
