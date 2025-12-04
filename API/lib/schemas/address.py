import typing
from API.lib.schemas.base import BaseModel
from dataclasses import dataclass


@dataclass
class Address(BaseModel):
    id: typing.Optional[str] = None
    city: typing.Optional[str] = None
    street: typing.Optional[str] = None
    building: typing.Optional[str] = None
    raw: typing.Optional[str] = None
    show_metro_only: typing.Optional[bool] = False

    def to_json(
            self
    ):
        return {
            'id': self.id,
            'from': self.show_metro_only
        }


@dataclass
class ItemsAddress(BaseModel):
    data: typing.List[Address] = None

    def append_item(self, item: Address):
        if self.data is None or not self.data:
            self.data = []

        #item.id = quantity_items + 1
        self.data.append(
            item
        )

    def get_item_by_id(self, item_id: str) -> Address:
        for item in self.data:
            if item.id == item_id:
                return item

    def delete_item(self, item: Address):
        self.data.remove(item)

    def to_json(self):
        return [
            i.to_json() for i in self.data
        ]
