from pydantic import BaseModel
from typing import Optional

class SkillCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True

class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class ModelCreate(BaseModel):
    name: str
    provider: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: Optional[int] = None
    max_context: Optional[int] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    config: Optional[str] = None  # JSON string
    is_active: bool = True

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    max_tokens: Optional[int] = None
    max_context: Optional[int] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    config: Optional[str] = None
    is_active: Optional[bool] = None
