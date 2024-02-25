# Standard Python Libraries
import logging
import re
from typing import Any, List, Tuple

# Third-Party Libraries
import fitz
from pydantic import BaseModel, ValidationError, field_validator

from .. import ActionBase


class GatedRegexActionArgs(BaseModel):
    gate_re: re.Pattern
    clear_res: List[re.Pattern]

    @field_validator("gate_re", mode="before")
    def compile_gate_re(cls, value: Any) -> re.Pattern[bytes]:
        if isinstance(value, str):
            return re.compile(value.encode())
        elif isinstance(value, re.Pattern):
            return value
        else:
            # Handle other unexpected types, or raise an exception
            raise ValueError(
                "Unexpected type for 'regex'. Expected 'str' or compiled regex pattern."
            )

    @field_validator("clear_res", mode="before")
    @classmethod
    def compile_clear_regexes(cls, value: Any) -> List[re.Pattern[bytes]]:
        if isinstance(value, list):
            return [re.compile(v.encode()) for v in value]
        else:
            # Handle other unexpected types, or raise an exception
            raise ValueError(
                "Unexpected type for 'regex'. Expected a list of strings or compiled regular expressions."
            )

    class Config:
        extra = "forbid"


class GatedRegexAction(ActionBase):
    """Clear stream objects matching a regular expression, but only if a gate regex matches."""

    nice_name = "gated-regex"

    @classmethod
    def apply(cls, doc: fitz.Document, **kwargs: Any) -> Tuple[int, bool]:
        try:
            args = GatedRegexActionArgs(**kwargs)
        except ValidationError as e:
            print(f"Error validating arguments: {e}")
            return (0, False)
        change_count = 0

        logging.debug("Gate regex: %s", args.gate_re.pattern)
        logging.debug("Clear regexes: %s", [r.pattern for r in args.clear_res])

        for xref_num in range(1, doc.xref_length()):
            if not doc.xref_is_stream(xref_num):
                continue  # skip non-stream objects
            if args.gate_re.search(doc.xref_stream(xref_num)):
                # replace all instances of the regex with an empty print statement
                new_stream = doc.xref_stream(xref_num)
                for regex in args.clear_res:
                    new_stream, subs_made = re.subn(regex, b"() Tj", new_stream)
                    change_count += subs_made
                doc.update_stream(xref_num, new_stream)
        return (change_count, True)
