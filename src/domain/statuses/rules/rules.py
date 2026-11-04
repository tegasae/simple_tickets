from dataclasses import dataclass




@dataclass(frozen=True, slots=True)
class TicketStatusRule:
    """
    Intrinsic rules of a Ticket status.

    These rules describe the payload and origin of a status itself.
    They do not describe allowed transitions between statuses.

    Attributes
    ----------
    user_action:
        ``True`` if the status represents an action performed by a User.

        ``False`` means that the action is performed by an Admin.

        Admin is intentionally the default because most Ticket workflow
        actions are administrative actions.

    requires_comment:
        ``True`` if the status record must contain a non-empty comment.

    requires_executor:
        ``True`` if the status record must contain a valid ``executor_id``.

    allows_work_data:
        ``True`` if the status record may contain actual work information:

        - ``actual_started_at``;
        - ``actual_finished_at``;
        - ``duration``.

        This flag only declares that such data is allowed for the status.
        Validation of valid combinations of these fields belongs to the
        status-record payload validation.

     requires_work_mode True if kind of work has to set

    requires_user_id Должен быть установлен пользователь от которог заявка



    """
    requires_comment: bool = False  # internal state
    requires_executor: bool = False  # internal state
    allows_work_data: bool = False  # internal state

    requires_work_mode: bool = False   # а он нужен? Не дублирование ли с allows_work_data?
    user_action: bool = False
    can_change_data: bool = False
    has_executor:bool=False
    requires_user_id:bool=False
    requires_ticket_user_id:bool=False





@dataclass(frozen=True, slots=True)
class TicketOriginRule:
    """
    Requirements determined by the initial Ticket status.

    These requirements remain valid throughout
    the entire Ticket lifecycle.
    """

    requires_user_id: bool = False
    requires_ticket_user_id: bool = False


@dataclass(frozen=True, slots=True)
class TicketStateRule:
    """
    Rules determined by the current Ticket status.

    can_change_data:
        Whether Ticket attributes can be modified.

    has_executor:
        Whether the current workflow state retains
        an active executor assignment.
    """

    can_change_data: bool = False
    has_executor: bool = False
