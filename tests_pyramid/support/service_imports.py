"""Temporary import compatibility while service filenames are being consolidated.

Remove the fallback once the project permanently settles on the
`*_application_service.py` names.
"""
try:
    from src.application.services.ticket_application_service import TicketApplicationService
except ModuleNotFoundError:
    from src.application.services.ticket_service import TicketApplicationService

try:
    from src.application.services.ticket_user_application_service import TicketUserApplicationService
except ModuleNotFoundError:
    from src.application.services.ticket_user_service import TicketUserApplicationService

__all__ = ["TicketApplicationService", "TicketUserApplicationService"]
