"""
Ticket statuses and their intrinsic rules.

This module describes:

- the set of statuses available for Ticket;
- which statuses represent actions performed by a User rather than an Admin;
- which statuses require a comment;
- which statuses require an executor;
- which statuses may contain actual work-time data.

Workflow transitions are intentionally not defined here.
They belong to a separate part of the domain model.

By default, a status is considered to be produced by an Admin action.
Only statuses explicitly marked with ``user_action=True`` are produced
by a User action.
"""

from enum import StrEnum


class TicketStatus(StrEnum):
    """
    Status of a Ticket.

    The status represents the business state recorded in the Ticket history.

    Notes
    -----
    CREATED
        Ticket was created directly by an Admin.
    CREATED_FROM_USER_REQUEST Пользователь сделал запрос на заявку, по телефону или передал
    CREATED_FROM_TICKET_USER
        Ticket was created from a TicketUser request.
        The action is attributed to the User.
    #CREATED_FROM_SUSPENDED_TICKET
    #    A ticket was created when the ticket was placed in SUSPENDED status because a client or user was disabled.
    REJECTED
        Ticket was rejected by an Admin.
        A comment explaining the reason is required.

    ACCEPTED
        Ticket was accepted by an Admin.

    DEFERRED
        Ticket was deliberately deferred by an Admin.
        A comment explaining the reason is required.

    SUSPENDED
        Ticket was suspended because the related Client or User was disabled.

        This status is semantically different from DEFERRED.
        DEFERRED represents a normal business decision to postpone work,
        while SUSPENDED represents suspension caused by availability of the
        related Client/User.

    ASSIGNED
        An executor was assigned to the Ticket.
        ``executor_id`` is required for the corresponding status record.

    AT_WORK
        Work on the Ticket is being performed or actual work is being
        registered retrospectively.

        The corresponding status record may contain:

        - actual_started_at;
        - actual_finished_at;
        - duration.

        Exact validation rules for these fields belong to the status-record
        payload validation.

    PAUSED
        Work on the Ticket was paused.

    READY_FOR_REVIEW
        Work was completed by the executor and submitted for review.

    CONFIRMED_BY_USER
        User confirmed the result of the work.
        This is a terminal status.

    EXECUTED
        Ticket was finally completed by an authorized Admin.

    CANCELLED
        Ticket was cancelled by an Admin.
        A comment explaining the reason is required.

    CANCELLED_BY_USER
        Ticket was cancelled by the User.
    """

    CREATED = "created"
    CREATED_FROM_REQUEST_USER = "created_from_request_user"
    CREATED_FROM_TICKET_USER = "created_from_ticket_user"


    REJECTED = "rejected"
    ACCEPTED = "accepted"

    DEFERRED = "deferred"
    SUSPENDED = "suspended"

    ASSIGNED = "assigned"
    AT_WORK = "at_work"
    PAUSED = "paused"

    READY_FOR_REVIEW = "ready_for_review"

    CONFIRMED_BY_USER = "confirmed_by_user"
    EXECUTED = "executed"

    CANCELLED = "cancelled"
    CANCELLED_BY_USER = "cancelled_by_user"





