from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RevertRequest(BaseModel):
    version_number: Optional[int] = None


class MemoryCreateRequest(BaseModel):
    title: str
    content: str
    category: str = "personal"
    tags: List[str] = []
    action: str = "auto"
    memory_id: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    category_filter: Optional[str] = None
    top_k: int = 5


class ChatRequest(BaseModel):
    message: str
    category: Optional[str] = None
    model: Optional[str] = None


class AutoOrganizeRequest(BaseModel):
    content: str
    title: Optional[str] = None
    model: Optional[str] = None


class ModelSelectRequest(BaseModel):
    model: str


class AutoSuggestRequest(BaseModel):
    content: str
    title: Optional[str] = None
    model: Optional[str] = None


class PromptUpdateRequest(BaseModel):
    auto_suggest: Optional[str] = None
    auto_organize: Optional[str] = None
    smart_merge: Optional[str] = None
    graph_chat: Optional[str] = None

