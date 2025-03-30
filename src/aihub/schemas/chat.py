from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: str
    agents: List[str]

class ChatResponse(BaseModel):
    response: str
    model: str
    agents: List[str] 