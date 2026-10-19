# ============================
# src/domain/ticket_components.py
# Shared components (composition, not inheritance)
# ============================


from dataclasses import dataclass, field
from datetime import datetime, timezone

from typing import TypeVar



from src.domain.value_objects import CommonComment

S = TypeVar("S")  # status enum type
R = TypeVar("R")  # status record type




@dataclass(kw_only=True)
class Comment:
    comment_id:int=0
    employee_id: int
    comment: CommonComment
    date_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_new(self) -> bool:
        return not bool(self.comment_id)





@dataclass
class CommentThread:
    comments: list[Comment] = field(default_factory=list)

    def add(self, comment: Comment) -> None:
        self.comments.append(comment)


