from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class MigrationType(str, Enum):
    JAVA = "java"
    PYTHON = "python"

class ReleaseType(str, Enum):
    STABLE = "stable"
    RELEASE_CANDIDATE = "rc"

class UserPreferences(BaseModel):
    project_path: Path
    migration_type: MigrationType
    release_type: ReleaseType

    class Config:
        frozen = True

class MemoryState(BaseModel):
    preferences: UserPreferences
    context: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = True

class Decision(BaseModel):
    type: str
    data: Dict[str, Any]
    context: Dict[str, Any]

    class Config:
        frozen = True 