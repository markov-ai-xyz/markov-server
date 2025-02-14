from langchain.pydantic_v1 import BaseModel


class Output(BaseModel):
    output: str
