import typing
from dataclasses import dataclass

from API.lib.schemas.base import BaseModel


@dataclass
class Directories(BaseModel):
    id: typing.Optional[str] = None
    name: typing.Optional[str] = None

    def to_json(self):
        return {
            'id': self.id
        }


@dataclass
class ItemDirectories(BaseModel):
    data: typing.List[Directories] = None

    def append_item(self, item: Directories):
        if self.data is None or not self.data:
            self.data = []

        #item.id = quantity_items + 1
        self.data.append(
            item
        )

    def get_item_by_id(self, item_id: str) -> Directories:
        for item in self.data:
            if item.id == item_id:
                return item

    def delete_item(self, item: Directories):
        self.data.remove(item)
