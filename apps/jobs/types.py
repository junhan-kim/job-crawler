from dataclasses import dataclass
from enum import StrEnum


class JobAction(StrEnum):
    """DB 저장 액션."""

    CREATED = "Created"
    UPDATED = "Updated"


class SaveResultKey(StrEnum):
    """저장 결과 키."""

    CREATED = "created"
    UPDATED = "updated"


@dataclass
class SaveResult:
    """배치 저장 결과."""

    created: int
    updated: int

    def to_dict(self) -> dict[str, int]:
        return {SaveResultKey.CREATED: self.created, SaveResultKey.UPDATED: self.updated}
