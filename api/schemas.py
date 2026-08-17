from typing import List, Optional
from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    title: str = Field(..., description="Title of the memory")
    content: str = Field(..., description="Content of the memory")
    category: str = Field(default="personal", description="Memory category")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    action: str = Field(default="auto", description="Action type: auto, insert, update, append, delete")
    memory_id: Optional[str] = Field(default=None, description="Optional existing memory ID")


class MemoryMergeRequest(BaseModel):
    memory_ids: List[str] = Field(..., min_length=2, description="List of at least 2 memory IDs to merge")
    target_title: Optional[str] = Field(default=None, description="Optional custom unified title")
    target_category: Optional[str] = Field(default=None, description="Optional target category")
    target_tags: Optional[List[str]] = Field(default=None, description="Optional list of tags for merged note")
    delete_sources: bool = Field(default=True, description="Whether to delete/trash original source memories after merge")
    instruction: Optional[str] = Field(default=None, description="Optional custom LLM merge instructions")
    use_ai: Optional[bool] = Field(default=None, description="Optional explicit toggle for AI synthesis vs deterministic merge")


class MemoryOrganizeRequest(BaseModel):
    instruction: Optional[str] = Field(default=None, description="Optional instruction or goal (e.g. summarize into key takeaways, polish formatting)")
    use_ai: bool = Field(default=True, description="Whether to use AI for restructuring and organizing")


class RevertRequest(BaseModel):
    version_number: Optional[int] = Field(default=None, description="Version number to revert to")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    category_filter: Optional[str] = Field(default=None, description="Optional category filter")
    top_k: int = Field(default=5, description="Number of results to return")


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message to companion")
    model: Optional[str] = Field(default=None, description="Model override")
    provider: Optional[str] = Field(default=None, description="LLM provider: openai or ollama")


class AuditActionRequest(BaseModel):
    auto_fix: bool = Field(default=False, description="Whether to automatically reconcile orphan records")
