import typing
from dataclasses import dataclass

from API.lib.schemas.base import BaseModel


@dataclass
class Areas(BaseModel):
    id: typing.Optional[str] = None
    parent_id: typing.Optional[str] = None
    name: typing.Optional[str] = None

    def to_json(self):
        return {
            'id': self.id
        }


@dataclass
class ItemAreas(BaseModel):
    data: typing.List[Areas] = None

    def append_item(self, item: Areas):
        if self.data is None or not self.data:
            self.data = []

        #item.id = quantity_items + 1
        self.data.append(
            item
        )

    def get_item_by_id(self, item_id: str) -> Areas:
        for item in self.data:
            if item.id == item_id:
                return item

    def delete_item(self, item: Areas):
        self.data.remove(item)


@dataclass
class Gender(BaseModel):
    id: typing.Optional[str] = None
    name: typing.Optional[str] = None

    def to_json(self):
        return {
            'id': self.id
        }


@dataclass
class Salary(BaseModel):
    amount: typing.Optional[str | int] = None
    currency: typing.Optional[str] = None


@dataclass
class Level(BaseModel):
    id: typing.Optional[str] = None
    name: typing.Optional[str] = None

    def to_json(self):
        return {
            'id': self.id
        }


@dataclass
class Primary(BaseModel):
    id: typing.Optional[str] = None
    name: typing.Optional[str] = None

    def to_json(self):
        return {
            'id': self.id
        }


@dataclass
class Experience(BaseModel):
    start: typing.Optional[str] = None
    end: typing.Optional[str] = None
    position: typing.Optional[str] = None
    company: typing.Optional[str] = None
    company_id: typing.Optional[str] = None
    area: typing.Optional[Areas] = None
    company_url: typing.Optional[str] = None
    industry: typing.List[dict] = None


@dataclass
class Education(BaseModel):
    level: typing.Optional[Level] = None
    primary: typing.List[Primary] = None


@dataclass
class Resume(BaseModel):
    id: typing.Optional[str] = None
    last_name: typing.Optional[str] = None
    first_name: typing.Optional[str] = None
    middle_name: typing.Optional[str] = None
    title: typing.Optional[str] = None
    area: typing.Optional[Areas] = None
    age: typing.Optional[str] = None
    gender: typing.Optional[Gender] = None
    salary: typing.Optional[Salary] = None
    total_experience: typing.Optional[dict] = None
    certificate: typing.List[dict] = None
    url: typing.Optional[str] = None
    education: typing.List[Education] = None
    experience: typing.List[Experience] = None


@dataclass
class Contacts(BaseModel):
    birth_date: typing.Optional[str] = None
    email: typing.Optional[str] = None
    phone: typing.Optional[str] = None
    pdf: typing.Optional[str] = None
