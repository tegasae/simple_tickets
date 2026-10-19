from src.domain.exceptions import DomainOperationError
from src.domain.statuses.mapping_statuses import TICKET_TO_TICKET_USER_STATUS
from src.domain.ticket import Ticket
from src.domain.ticket_user import TicketUser
from src.domain.statuses.ticket_user_status import TicketUserStatus


class TicketSyncService:
    """
    Domain service for synchronization of linked Ticket and TicketUser.

    Ticket and TicketUser are independent aggregates with independent
    workflow histories.

    A Ticket may exist without TicketUser.

    A TicketUser always has a corresponding Ticket. Creation and persistence
    of both aggregates are coordinated by application layer.

    For an existing linked pair:

        ticket.user_ticket_id == ticket_user.ticket_id


    Responsibilities
    ================

    TicketSyncService is responsible for:

    - validation of structural consistency of a linked pair;
    - synchronization of Ticket workflow changes to TicketUser;
    - synchronization of User-originated TicketUser workflow changes
      to Ticket;
    - synchronized change of contact_user_id;
    - verification of workflow correspondence after synchronization.


    The service does not
    ====================

    TicketSyncService does not contain:

    - repositories;
    - persistence;
    - Unit of Work;
    - transactions;
    - RBAC;
    - permissions;
    - enabled-state checks;
    - creation of Ticket;
    - creation of TicketUser;
    - Ticket workflow rules;
    - TicketUser workflow rules;
    - status-record payload validation.

    Ticket and TicketUser remain responsible for their own workflow and
    aggregate invariants.


    Creation scenarios
    ==================

    Standalone Ticket
    -----------------

    Admin may create an internal Ticket without TicketUser:

        Ticket.status == CREATED
        Ticket.user_id == 0
        Ticket.user_ticket_id == 0

    TicketSyncService is not involved.


    User request entered by Admin
    -----------------------------

    Application layer:

        1. creates TicketUser;
        2. persists TicketUser and obtains ticket_id;
        3. creates Ticket with CREATED;
        4. Ticket actor_employee_id contains Admin id;
        5. Ticket.user_id > 0;
        6. Ticket.user_ticket_id == TicketUser.ticket_id;
        7. persists Ticket.

    CREATED is used because the internal Ticket itself was created by Admin.


    User creates request directly
    -----------------------------

    Application layer:

        1. creates TicketUser;
        2. persists TicketUser and obtains ticket_id;
        3. creates Ticket with CREATED_FROM_TICKET_USER;
        4. Ticket actor_employee_id == 0;
        5. Ticket.user_id > 0;
        6. Ticket.user_ticket_id == TicketUser.ticket_id;
        7. persists Ticket.


    Synchronization directions
    ==========================

    Admin-side workflow:

        Ticket -> TicketUser

    User-side workflow:

        TicketUser -> Ticket


    Ticket -> TicketUser
    ====================

    Status correspondence is defined by:

        TICKET_TO_TICKET_USER_STATUS

    Several Ticket statuses may correspond to one TicketUser status.

    For example:

        ACCEPTED
        DEFERRED
        ASSIGNED
        AT_WORK
        PAUSED

    correspond to:

        IN_WORK

    Therefore not every Ticket transition creates a new TicketUser status
    record.


    TicketUser -> Ticket
    ====================

    There is intentionally no general reverse status mapping.

    TicketUser.IN_WORK, for example, corresponds to several different
    internal Ticket states.

    Therefore this direction handles only unambiguous User actions:

        CONFIRMED_BY_USER
        CANCELLED_BY_USER


    Comments
    ========

    Ticket and TicketUser status comments are independent.

    sync_from_ticket():

        comment is a new TicketUser-facing status comment.

    sync_from_ticket_user():

        comment is a new internal Ticket status comment.

    Existing comments are never copied automatically between aggregates.


    Description
    ===========

    Ticket.description and TicketUser.description are independent.

    TicketSyncService never synchronizes descriptions.


    Contact User
    ============

    For a linked pair:

        ticket.contact_user_id == ticket_user.contact_user_id

    is a permanent cross-aggregate invariant.

    Therefore contact User is changed through:

        change_contact_user(...)

    which changes both aggregates as one domain operation.

    contact_user_id == 0 means:

        reset contact User to ticket.user_id

    because linked Ticket/TicketUser always belong to a User and therefore
    cannot exist without a contact User.
    """

    # ==================================================================
    # Pair consistency
    # ==================================================================

    @staticmethod
    def ensure_consistent(

        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """
        Validate structural consistency of a linked pair.

        This method intentionally does not compare workflow statuses.

        During synchronization one aggregate has already changed while the
        other still has its previous status. Such temporary workflow mismatch
        inside one transaction is expected.

        Permanent pair invariants are:

            ticket.user_ticket_id > 0
            ticket_user.ticket_id > 0

            ticket.user_ticket_id == ticket_user.ticket_id
            ticket.client_id == ticket_user.client_id
            ticket.user_id == ticket_user.user_id
            ticket.contact_user_id == ticket_user.contact_user_id
        """

        if ticket.user_ticket_id <= 0:
            raise DomainOperationError(
                "Ticket is not linked to TicketUser"
            )

        if ticket_user.ticket_user_id <= 0:
            raise DomainOperationError(
                "Linked TicketUser must have positive ticket_id"
            )

        if ticket.user_ticket_id != ticket_user.ticket_user_id:
            raise DomainOperationError(
                "Ticket user_ticket_id does not match "
                "TicketUser ticket_id"
            )

        if ticket.client_id != ticket_user.client_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different client_id"
            )

        if ticket.user_id != ticket_user.user_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different user_id"
            )

        if ticket.contact_user_id != ticket_user.contact_user_id:
            raise DomainOperationError(
                "Ticket and TicketUser have different contact_user_id"
            )

    # ==================================================================
    # Ticket -> TicketUser
    # ==================================================================

    def sync_from_ticket(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
        *,
        comment: str = "",
    ) -> None:
        """
        Synchronize current Ticket workflow state to TicketUser.

        This method is normally called immediately after an Admin-side
        operation on Ticket.

        Example:

            ticket.accept(
                actor_employee_id=admin_id,
            )

            sync_service.sync_from_ticket(
                ticket,
                ticket_user,
            )


        Mapping
        =======

        Current Ticket status is projected through:

            TICKET_TO_TICKET_USER_STATUS

        If TicketUser already has the corresponding status, no new status
        record is created.

        Example:

            CREATED -> ACCEPTED

        produces:

            TicketUser.CREATED -> TicketUser.IN_WORK

        A later:

            ACCEPTED -> ASSIGNED

        still corresponds to IN_WORK and therefore causes no TicketUser
        workflow change.


        Actor
        =====

        Admin-originated synchronization uses:

            ticket.current_status_record().actor_employee_id

        as TicketUserStatusRecord.actor_employee_id.


        User-originated statuses
        ========================

        CONFIRMED_BY_USER and CANCELLED_BY_USER normally originate from
        TicketUser.

        Internal Ticket stores:

            actor_employee_id == 0

        for these actions, while TicketUser requires the real positive User
        identifier.

        Therefore this method does not try to reconstruct User identity.


        Comment
        =======

        comment is a new TicketUser-facing status comment.

        The Ticket status comment is never copied automatically.
        """

        self.ensure_consistent(
            ticket,
            ticket_user,
        )

        ticket_record = ticket.current_status_record()

        target_status = self._ticket_user_status_for(ticket)

        current_status = ticket_user.current_status()

        # Several internal Ticket statuses may map to the same external
        # TicketUser status.
        if current_status == target_status:
            return

        # CREATED is an initial TicketUser status.
        #
        # Synchronization never moves an existing TicketUser backwards to
        # CREATED.
        if target_status == TicketUserStatus.CREATED:
            raise DomainOperationError(
                "Cannot synchronize TicketUser back to CREATED"
            )

        # These actions must normally originate from TicketUser because
        # Ticket does not contain the real User actor id.
        if target_status in {
            TicketUserStatus.CONFIRMED_BY_USER,
            TicketUserStatus.CANCELLED_BY_USER,
        }:
            raise DomainOperationError(
                "User-originated Ticket state must be synchronized "
                "from TicketUser"
            )

        actor_employee_id = ticket_record.actor_employee_id

        if target_status == TicketUserStatus.IN_WORK:
            ticket_user.mark_in_work(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )

        elif target_status == TicketUserStatus.WAITING_FOR_CONFIRMATION:
            ticket_user.mark_waiting_for_confirmation(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )

        elif target_status == TicketUserStatus.SUSPENDED:
            ticket_user.suspend(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )

        elif target_status == TicketUserStatus.CONFIRMED_BY_ADMIN:
            ticket_user.confirm_by_admin(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )

        elif target_status == TicketUserStatus.CANCELLED_BY_ADMIN:
            ticket_user.cancel_by_admin(
                actor_employee_id=actor_employee_id,
                comment=comment,
            )

        else:
            raise DomainOperationError(
                "Unsupported Ticket -> TicketUser synchronization: "
                f"{ticket_record.status.value} -> "
                f"{target_status.value}"
            )

        self._ensure_workflow_consistent(
            ticket,
            ticket_user,
        )

    # ==================================================================
    # TicketUser -> Ticket
    # ==================================================================

    def sync_from_ticket_user(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
        *,
        comment: str = "",
    ) -> None:
        """
        Synchronize current User-side TicketUser workflow state to Ticket.

        This method is normally called immediately after a User operation
        on TicketUser.

        Example:

            ticket_user.confirm_by_user(
                actor_employee_id=user_id,
            )

            sync_service.sync_from_ticket_user(
                ticket,
                ticket_user,
            )


        CONFIRMED_BY_USER
        =================

        TicketUser:

            WAITING_FOR_CONFIRMATION
                ->
            CONFIRMED_BY_USER

        synchronizes Ticket:

            READY_FOR_REVIEW
                ->
            CONFIRMED_BY_USER


        CANCELLED_BY_USER
        =================

        TicketUser:

            CREATED
                ->
            CANCELLED_BY_USER

        may synchronize:

            Ticket.CREATED_FROM_TICKET_USER
                ->
            Ticket.CANCELLED_BY_USER

        or, when Admin originally registered the User request:

            Ticket.CREATED
                ->
            Ticket.CANCELLED_BY_USER

        Ticket itself validates that CREATED -> CANCELLED_BY_USER is allowed
        only for a Ticket linked to TicketUser.


        Other TicketUser statuses
        =========================

        No general reverse mapping is used.

        For example:

            IN_WORK

        does not identify whether internal Ticket is:

            ACCEPTED
            DEFERRED
            ASSIGNED
            AT_WORK
            PAUSED

        Such workflow changes originate in Ticket and are synchronized using
        sync_from_ticket().


        Actor
        =====

        TicketUser contains the real positive User actor id.

        Internal Ticket User actions intentionally use:

            actor_employee_id == 0

        Ticket.confirm_by_user() and Ticket.cancel_by_user() construct the
        correct internal representation.


        Comment
        =======

        comment is a new internal Ticket status comment.

        The TicketUser comment is not copied automatically.
        """

        self.ensure_consistent(
            ticket,
            ticket_user,
        )

        ticket_user_status = ticket_user.current_status()

        expected_ticket_user_status = self._ticket_user_status_for(ticket)

        # Nothing to synchronize.
        if ticket_user_status == expected_ticket_user_status:
            return

        if ticket_user_status == TicketUserStatus.CONFIRMED_BY_USER:
            ticket.confirm_by_user(
                comment=comment,
            )

        elif ticket_user_status == TicketUserStatus.CANCELLED_BY_USER:
            ticket.cancel_by_user(
                comment=comment,
            )

        else:
            raise DomainOperationError(
                "TicketUser status cannot be synchronized to Ticket: "
                f"{ticket_user_status.value}"
            )

        self._ensure_workflow_consistent(
            ticket,
            ticket_user,
        )

    # ==================================================================
    # Shared data
    # ==================================================================

    def change_contact_user(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
        *,
        actor_employee_id: int,
        contact_user_id: int,
    ) -> None:
        """
        Change contact User for a linked Ticket/TicketUser pair.

        contact_user_id is a shared cross-aggregate value.

        For every linked pair the invariant is:

            ticket.contact_user_id == ticket_user.contact_user_id


        contact_user_id > 0
        ===================

        Set the specified User as the contact User in both aggregates.


        contact_user_id == 0
        ====================

        Reset contact User to the User who owns the request:

            contact_user_id = ticket.user_id

        Since Ticket and TicketUser are linked, their user_id values are
        already required to be equal.


        contact_user_id < 0
        ===================

        Invalid.


        actor_employee_id
        =================

        Identifies the actor responsible for changing TicketUser data.

        RBAC and permissions are not checked by this service.


        Atomicity
        =========

        Application layer must persist both modified aggregates inside one
        transaction.

        Basic preconditions are checked before either aggregate is modified
        so a predictable validation error does not leave only one aggregate
        changed in memory.
        """

        self.ensure_consistent(
            ticket,
            ticket_user,
        )

        if actor_employee_id <= 0:
            raise DomainOperationError(
                "actor_employee_id must be positive"
            )

        if contact_user_id < 0:
            raise DomainOperationError(
                "contact_user_id cannot be negative"
            )

        if ticket.user_id <= 0:
            raise DomainOperationError(
                "Linked Ticket must have positive user_id"
            )

        # Check both aggregate-level modification conditions before changing
        # either aggregate.
        if not ticket.current_status_record().rule.can_change_data:
            raise DomainOperationError(
                "Cannot change contact User in current Ticket status "
                f"{ticket.current_status().value}"
            )

        if ticket_user.is_terminal():
            raise DomainOperationError(
                "Cannot change contact User of terminal TicketUser"
            )

        resolved_contact_user_id = (
            contact_user_id
            if contact_user_id > 0
            else ticket.user_id
        )

        ticket.change_contact_user(
            contact_user_id=resolved_contact_user_id,
        )

        ticket_user.change_contact_user(
            actor_employee_id=actor_employee_id,
            contact_user_id=resolved_contact_user_id,
        )

        # The shared invariant must hold after the operation.
        self.ensure_consistent(
            ticket,
            ticket_user,
        )

    # ==================================================================
    # Internal helpers
    # ==================================================================

    @staticmethod
    def _ticket_user_status_for(
        ticket: Ticket,
    ) -> TicketUserStatus:
        """
        Return TicketUser status corresponding to current Ticket status.

        The mapping is expected to contain every TicketStatus.

        Runtime protection is kept here because synchronization should fail
        with a domain-level error if mapping configuration is incomplete.
        """

        ticket_status = ticket.current_status()

        try:
            return TICKET_TO_TICKET_USER_STATUS[ticket_status]
        except KeyError as exc:
            raise DomainOperationError(
                "Ticket status has no TicketUser status mapping: "
                f"{ticket_status.value}"
            ) from exc

    def _ensure_workflow_consistent(
        self,
        ticket: Ticket,
        ticket_user: TicketUser,
    ) -> None:
        """
        Verify workflow correspondence after synchronization.

        Ticket and TicketUser have different workflow graphs.

        Therefore their status enum values are not compared directly.

        Instead current Ticket status is projected through:

            TICKET_TO_TICKET_USER_STATUS

        and the result must equal actual TicketUser current status.
        """

        expected_status = self._ticket_user_status_for(ticket)
        actual_status = ticket_user.current_status()

        if actual_status != expected_status:
            raise DomainOperationError(
                "Ticket and TicketUser workflow states are inconsistent: "
                f"Ticket status {ticket.current_status().value} "
                f"corresponds to TicketUser status "
                f"{expected_status.value}, "
                f"but actual TicketUser status is "
                f"{actual_status.value}"
            )