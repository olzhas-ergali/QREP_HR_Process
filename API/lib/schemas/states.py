import typing
from dataclasses import dataclass

from API.lib.schemas.base import BaseModel


@dataclass
class States(BaseModel):
    id: typing.Optional[str] = None
    name: typing.Optional[str] = None


@dataclass
class CollectionStates(BaseModel):
    data: typing.List[States] = None

    def append_item(self, item: States):
        if self.data is None or not self.data:
            self.data = []

        self.data.append(
            item
        )

    def get_item_by_id(self, item_id: str) -> States:
        for item in self.data:
            if item.id == item_id:
                return item

    def delete_item(self, item: States):
        self.data.remove(item)
