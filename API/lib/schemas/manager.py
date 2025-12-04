import typing
from dataclasses import dataclass

from API.lib.schemas.base import BaseModel
from API.lib.schemas.resume import Areas


@dataclass
class Phones(BaseModel):
    city: typing.Optional[str] = None
    comment: typing.Optional[str] = None
    country: typing.Optional[str] = None
    formatted: typing.Optional[str] = None
    number: typing.Optional[str] = None


@dataclass
class Manager(BaseModel):
    id: typing.Optional[str] = None
    first_name: typing.Optional[str] = None
    last_name: typing.Optional[str] = None
    middle_name: typing.Optional[str] = None
    position: typing.Optional[str] = None
    email: typing.Optional[str] = None
    area: typing.Optional[Areas] = None
    phone: typing.Optional[Phones] = None

    def to_json(
            self
    ):
        return {
            'id': self.id
        }


@dataclass
class Contacts(BaseModel):
    email: typing.Optional[str] | None = None
    name: typing.Optional[str] = None
    phones: typing.List[Phones] = None


@dataclass
class ItemsManager(BaseModel):
    data: typing.List[Manager] = None

    def append_item(self, item: Manager):
        if self.data is None or not self.data:
            self.data = []

        #item.id = quantity_items + 1
        self.data.append(
            item
        )

    def get_item_by_id(self, item_id: str) -> Manager:
        for item in self.data:
            if item.id == item_id:
                return item

    def delete_item(self, item: Manager):
        self.data.remove(item)

    def to_json(self):
        return [
            i.to_json() for i in self.data
        ]
