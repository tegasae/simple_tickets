from typing import Annotated

from pydantic import StringConstraints

from src.domain.value_objects import CommonComment, TextOfTicket


TicketText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=TextOfTicket.MIN_LENGTH,
        max_length=TextOfTicket.MAX_LENGTH,
    ),
]

TicketCommentText = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=CommonComment.MAX_LENGTH),
]
RequiredTicketCommentText = Annotated[
    str, StringConstraints(
        strip_whitespace=True, min_length=CommonComment.MIN_LENGTH,
        max_length=CommonComment.MAX_LENGTH,
    ),
]
