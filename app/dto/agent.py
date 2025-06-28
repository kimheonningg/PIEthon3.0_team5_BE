from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field
from uuid import UUID

class ChatToolCall(BaseModel):
    """Tool call in a chat response."""
    id: str
    name: str
    args: str
    result: Optional[Any] = None

class ChatResponseData(BaseModel):
    """Data in a chat response."""
    text: str
    tool_calls: List[ChatToolCall] = []

class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    success: bool = True
    message: str = "Success"
    conversation_id: Optional[str] = None  # Include conversation ID for frontend
    response: Optional[ChatResponseData] = None

class ChatMessage(BaseModel):
    """A chat message."""
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

# Updated chat request with conversation support
class ChatRequest(BaseModel):
    """Request for the chat endpoint."""
    query: str = Field(..., description="User's query/question")
    patient_mrn: str = Field(..., description="MRN of the patient")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (creates new if None)")

# Simple conversation list DTO
class ConversationInfo(BaseModel):
    """Basic conversation information."""
    conversation_id: str
    title: str
    created_at: str
    last_updated: str
    message_count: int

class ChatStreamChunk(BaseModel):
    """Chunk of a streaming chat response."""
    text: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    done: bool = False
    error: Optional[str] = None

class ChatStreamResponse(BaseModel):
    """Full streaming chat response (for documentation only)."""
    chunks: List[ChatStreamChunk]

class SimpleChatRequest(BaseModel):
    """Simple request for the chat endpoint."""
    patient_mrn: str = Field(..., description="MRN of the patient")
    message: str = Field(..., description="Message from the user")

class SimpleChatToolCall(BaseModel):
    """Tool call in a simple chat response."""
    id: str
    name: str
    args: str
    result: Optional[Any] = None

class SimpleChatResponse(BaseModel):
    """Response from the simple chat endpoint."""
    success: bool = True
    message: str = "Success"
    conversation_id: Optional[str] = None  # Include conversation ID for frontend
    text: str = ""
    tool_calls: List[SimpleChatToolCall] = []