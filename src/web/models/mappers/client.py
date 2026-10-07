from src.application.dto.client_dto import ClientDTO
from src.web.models.clients import ClientResponse, ClientCreateRequest, ClientUpdateContactRequest

# -------------------------------
# Request -> Application DTO mappers
# -------------------------------
class ClientMapperDTO:
    @staticmethod
    def create_request_to_dto(
            *,
            request: ClientCreateRequest,
            actor_admin_id: int,
    ) -> ClientDTO:
        """
        Convert web request model to application DTO.

        actor_admin_id comes from authenticated admin.
        Other fields come from request body.
        """
        return ClientDTO(
            actor_admin_id=actor_admin_id,
            **request.model_dump(),
        )



    @staticmethod
    def update_contact_request_to_dto(
            *,
            request: ClientUpdateContactRequest,
            actor_admin_id: int,
            client_id: int,
    ) -> ClientDTO:
        """
        Convert contact update request to ClientDTO.

        client_id comes from path parameter.
        actor_admin_id comes from authenticated admin.
        Contact fields come from request body.
        """
        return ClientDTO(
            actor_admin_id=actor_admin_id,
            client_id=client_id,
            **request.model_dump(),
        )

    @staticmethod
    def id_to_dto(
            *,
            client_id: int,
            actor_admin_id: int,
    ) -> ClientDTO:
        return ClientDTO(
            actor_admin_id=actor_admin_id,
            client_id=client_id,
        )

    @staticmethod
    def actor_id_to_dto(
            *,
            actor_admin_id: int,
    ) -> ClientDTO:
        return ClientDTO(
            actor_admin_id=actor_admin_id,
        )

    @staticmethod
    def to_response(response_dto) -> ClientResponse:
        """
        Convert application-layer ClientResponseDTO to web-layer ClientResponse.

        ClientResponse uses Pydantic.
        ClientResponseDTO is probably a dataclass.

        model_validate() works if ClientResponse has:
        model_config = ConfigDict(from_attributes=True)
        """
        return ClientResponse.model_validate(response_dto)

    @staticmethod
    def to_responses(response_dtos) -> list[ClientResponse]:
        """
        Convert list[ClientResponseDTO] to list[ClientResponse].
        """
        return [
            ClientResponse.model_validate(response_dto)
            for response_dto in response_dtos
        ]


