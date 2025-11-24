from pydantic import BaseModel
from typing import List, Literal


class Change(BaseModel):
    """Represents a single line change in a diff."""
    line_number: int
    type: Literal["added", "removed", "context"]
    content: str


class FileChange(BaseModel):
    """Represents changes to a single file."""
    filename: str
    changes: List[Change]


class DiffResult(BaseModel):
    """Structured result of parsing a unified diff."""
    files: List[FileChange]

