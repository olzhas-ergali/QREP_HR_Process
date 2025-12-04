import typing
from dataclasses import dataclass

from API.lib.schemas.base import BaseModel
from API.lib.schemas.states import States
from API.lib.schemas.resume import Areas, Resume
from API.lib.schemas.manager import Manager, Contacts
from API.lib.schemas.address import Address
from API.lib.schemas.templates import Templates


@dataclass
class Salary(BaseModel):
    currency: typing.Optional[str] = None
    from_: typing.Optional[int] = None
    gross: typing.Optional[bool] = False
    to: typing.Optional[int] = None

    def to_json(
            self
    ):
        return {
            'currency': self.currency,
            'from': self.from_,
            'gross': self.gross,
            'to': self.to
        }


@dataclass
class Skills(BaseModel):
    name: typing.Optional[str] = None


@dataclass
class Phone(BaseModel):
    city: typing.Optional[str] = None
    number: typing.Optional[str] = None
    formatted: typing.Optional[str] = None


@dataclass
class PublicationVacation(BaseModel):
    name: typing.Optional[str] = None
    description: typing.Optional[str] = None
    work_format: typing.List[dict] = None
    work_hours: typing.List[dict] = None
    employment_form: typing.Optional[dict] = None
    area: typing.Optional[Areas] = None
    professional_roles: typing.List[dict] = None
    billing_type: typing.Optional[dict] = None
    type: typing.Optional[dict] = None
    allow_messages: typing.Optional[bool] | None = None
    code: typing.Optional[str] | None = None
    contacts: typing.List[Contacts] = None
    experience: typing.Optional[dict] = None
    internship: typing.Optional[bool] = False
    salary: typing.Optional[Salary] = None
    working_schedule: typing.List[dict] = None
    key_skills: typing.List[Skills] = None
    address: typing.Optional[Address] = None
    manager: typing.Optional[Manager] = None
    branded_template: typing.Optional[Templates] = None
    accept_temporary: typing.Optional[bool] = False

    def to_json(
            self
    ):
        return {
            'name': self.name,
            'description': self.description,
            'work_format': self.work_format,
            'area': self.area,
            'professional_roles': self.professional_roles,
            'billing_type': self.billing_type,
            'type': self.type,
            'allow_messages': self.allow_messages,
            'code': self.code,
            'contacts': [c.dict() for c in self.contacts] if self.contacts else None,
            'experience': self.experience,
            'internship': self.internship,
            'salary': self.salary.to_json() if self.salary else None,
            'work_schedule_by_days': self.working_schedule,
            'working_hours': self.work_hours,
            'key_skills': [s.dict() for s in self.key_skills] if self.key_skills else None,
            'manager': self.manager.to_json() if self.manager else None,
            'address': self.address.to_json() if self.address else None,
            'branded_template': self.branded_template if self.branded_template else None,
            'accept_temporary': self.accept_temporary
        }


@dataclass
class Vacation(BaseModel):
    id: typing.Optional[str] = None
    state: typing.Optional[States] = None
    created_at: typing.Optional[str] = None
    resume: typing.Optional[Resume] = None


@dataclass
class VacationItems(BaseModel):
    data: typing.List[Vacation] = None
    found: typing.Optional[int] = 100

    def append_item(self, item: Vacation):
        if self.data is None or not self.data:
            self.data = []

        # item.id = quantity_items + 1
        self.data.append(
            item
        )

    def get_item_by_id(self, item_id: str) -> Vacation:
        for item in self.data:
            if item.id == item_id:
                return item

    def delete_item(self, item: Vacation):
        self.data.remove(item)



