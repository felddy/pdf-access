# Standard Python Libraries
from pathlib import Path
import re
from typing import Any, Dict, List

# Third-Party Libraries
from pydantic import BaseModel, Field, root_validator, validator


class Action(BaseModel):
    args: Dict[str, Any] = Field(default_factory=dict)
    function: str
    name: str

    class Config:
        extra = "forbid"


class Plan(BaseModel):
    actions: List[Action]
    metadata_search: Dict[str, re.Pattern]
    passwords: List[str] = Field(default_factory=list)
    path_regex: re.Pattern = re.compile(".*")
    post_process: List[str] = Field(default_factory=list)

    @validator("path_regex", pre=True)
    def compile_path_regex(cls, v):
        if isinstance(v, str):
            return re.compile(v)
        return v

    @validator("metadata_search", pre=True)
    def compile_metadata_search(cls, v):
        if isinstance(v, dict):
            return {k: re.compile(v) for k, v in v.items()}
        return v

    class Config:
        extra = "forbid"


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
        extra = "forbid"


class Config(BaseModel):
    actions: Dict[str, Action]
    plans: Dict[str, Plan]
    sources: Dict[str, Source]

    class Config:
        extra = "forbid"

    @root_validator(pre=True)
    def resolve_actions(cls, values):
        # Extract actions and plans from the values dictionary
        actions_dict = values.get("actions", {})
        plans_dict = values.get("plans", {})

        # Iterate over the plans to resolve action names to Action objects
        for plan_name, plan in plans_dict.items():
            resolved_actions = []
            for action_name in plan.get("actions", []):
                action_obj = actions_dict.get(action_name)
                if action_obj:
                    resolved_actions.append(action_obj)
                else:
                    raise ValueError(
                        f"Action '{action_name}' referenced in plan '{plan_name}' does not exist."
                    )
            plan[
                "actions"
            ] = resolved_actions  # Replace action names with resolved Action objects

        return values
