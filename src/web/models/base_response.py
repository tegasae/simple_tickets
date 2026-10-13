from typing import Self

from pydantic import BaseModel


class BaseResponse(BaseModel):
    @classmethod
    def from_dto(cls, dto) -> Self:
        return cls.model_validate(dto)

    @classmethod
    def from_dtos(cls, dtos) -> list[Self]:
        return [
            cls.from_dto(dto)
            for dto in dtos
        ]