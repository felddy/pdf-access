# Standard Python Libraries
from pathlib import Path
import re
from typing import Any, Dict, List

# Third-Party Libraries
from pydantic import BaseModel, Field, field_validator, model_validator


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

    @field_validator("path_regex", mode="before")
    def compile_path_regex(cls, value: Any) -> re.Pattern[str]:
        if isinstance(value, str):
            return re.compile(value)
        elif isinstance(value, re.Pattern):
            return value
        else:
            # Handle other unexpected types, or raise an exception
            raise ValueError(
                "Unexpected type for 'path_regex'. Expected 'str' or compiled regex pattern."
            )

    @field_validator("metadata_search", mode="before")
    def compile_metadata_regexes(cls, value: Any) -> Dict[str, re.Pattern[str]]:
        if isinstance(value, dict):
            return {k: re.compile(v) for k, v in value.items()}
        else:
            # Handle other unexpected types, or raise an exception
            raise ValueError(
                "Unexpected type for 'metadata_search'. Expected 'dict' with 'str' keys and 'str' values."
            )

    class Config:
        extra = "forbid"


class Source(BaseModel):
    in_path: Path
    out_path: Path
    out_suffix: str = Field("")
    plans: List[str]

    @field_validator("in_path", "out_path", mode="before")
    def compile_path_regex(cls, value: Any) -> Path:
        if isinstance(value, str):
            return Path(value)
        elif isinstance(value, Path):
            return value
        else:
            # Handle other unexpected types, or raise an exception
            raise ValueError("Unexpected type. Expected 'str' or 'Path'.")

    class Config:
        extra = "forbid"


class Config(BaseModel):
    actions: Dict[str, Action]
    plans: Dict[str, Plan]
    sources: Dict[str, Source]

    class Config:
        extra = "forbid"

    @model_validator(mode="before")
    def resolve_actions(cls, values: Dict[str, Any]) -> Dict[str, Any]:
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
