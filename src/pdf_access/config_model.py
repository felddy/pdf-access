from typing import Any, Dict, List
from pydantic import BaseModel, Field


class Plan(BaseModel):
    args: Dict[str, Any] = Field(dict())
    technique: str


class Publisher(BaseModel):
    metadata_search: Dict[str, str]
    passwords: List[str] = Field(list())
    plans: List[str]


class Source(BaseModel):
    in_path: str
    out_path: str
    out_suffix: str = Field("")
    post_process: List[str] = Field(list())
    publishers: List[str]


class Config(BaseModel):
    plans: Dict[str, Plan]
    publishers: Dict[str, Publisher]
    sources: Dict[str, Source]
