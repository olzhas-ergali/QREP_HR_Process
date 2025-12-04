import typing
from dataclasses import dataclass

from API.lib.schemas.base import BaseModel


@dataclass
class Roles(BaseModel):
    id: typing.Optional[str] = None
    name: typing.Optional[str] = None

    def to_json(
            self
    ):
        return {
            'id': self.id
        }