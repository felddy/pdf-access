from typing import Any, Dict, List
import re
from pydantic import BaseModel, Extra, Field, validator
from pathlib import Path


class Action(BaseModel):
    action: str
    args: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = Extra.forbid


class Plan(BaseModel):
    actions: List[str]  # TODO link to action objects
    metadata_search: Dict[str, str]  # TODO precompile regex
    passwords: List[str] = Field(default_factory=list)
    path_regex: re.Pattern = re.compile(".*")
    post_process: List[str] = Field(default_factory=list)

    @validator("path_regex", pre=True)
    def compile_path_regex(cls, v):
        if isinstance(v, str):
            return re.compile(v)
        return v

    class Config:
        extra = Extra.forbid


class Source(BaseModel):
    in_path: Path
    out_path: Path
    out_suffix: str = Field("")
    plans: List[str]

    @validator("in_path", "out_path")
    def convert_to_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    class Config:
        extra = Extra.forbid


class Config(BaseModel):
    actions: Dict[str, Action]
    plans: Dict[str, Plan]
    sources: Dict[str, Source]

    class Config:
        extra = Extra.forbid
