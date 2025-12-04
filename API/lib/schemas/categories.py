import typing
from dataclasses import dataclass

from API.lib.schemas.base import BaseModel
from API.lib.schemas.roles import Roles


@dataclass
class Categories(BaseModel):
    id: typing.Optional[str] = None
    name: typing.Optional[str] = None
    roles: typing.List[Roles] = None

    def get_roles_by_id(self, item_id: str) -> Roles:
        for item in self.roles:
            if item.id == item_id:
                return item


@dataclass
class ItemsCategories(BaseModel):
    data: typing.List[Categories] = None
    found: typing.Optional[int] = 100

    def append_item(self, item: Categories):
        if self.data is None or not self.data:
            self.data = []

        # item.id = quantity_items + 1
        self.data.append(
            item
        )

    def get_item_by_id(self, item_id: str) -> Categories:
        for item in self.data:
            if item.id == item_id:
                return item

    def delete_item(self, item: Categories):
        self.data.remove(item)