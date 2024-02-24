from typing import Any, Dict, List
import re
from pydantic import BaseModel, Field, validator


class Plan(BaseModel):
    args: Dict[str, Any] = Field(default_factory=dict)
    technique: str


class Publisher(BaseModel):
    metadata_search: Dict[str, str]
    path_regex: re.Pattern = re.compile(".*")
    passwords: List[str] = Field(default_factory=list)
    plans: List[str]

    @validator("path_regex", pre=True)
    def compile_path_regex(cls, v):
        if isinstance(v, str):
            return re.compile(v)
        return v


class Source(BaseModel):
    in_path: str
    out_path: str
    out_suffix: str = Field("")
    post_process: List[str] = Field(default_factory=list)
    publishers: List[str]


class Config(BaseModel):
    plans: Dict[str, Plan]
    publishers: Dict[str, Publisher]
    sources: Dict[str, Source]
