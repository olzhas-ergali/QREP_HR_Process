import datetime
import typing

from pydantic import BaseModel


class ModelVacancies(BaseModel):
    name: typing.Optional[str] = None
    city: typing.Optional[str] = None
    type_work: typing.Optional[str] = None
    employment_type: typing.Optional[str] = None
    workFormat: typing.Optional[str] = None
    workGraphics: typing.Optional[str] = None
    address: typing.Optional[str] = None
    experience: typing.Optional[str] = None
    toDo: typing.Optional[str] = None
    exceptCandidates: typing.Optional[str] = None
    offer: typing.Optional[str] = None
    manager: typing.Optional[str] = None
    salary_to: typing.Optional[str] = None
    salary_from: typing.Optional[str] = None
    gender: typing.Optional[str] = None
    age_to: typing.Optional[int] = None
    age_from: typing.Optional[int] = None
    deal_id: typing.Optional[str] = None


class ModelVac2(BaseModel):
    draft_id: typing.Optional[str] = None
    previous_id: typing.Optional[str] = None
    vacancies_id: typing.Optional[str] = None


class ModelDiscard(BaseModel):
    resume_id: typing.Optional[str] = None
    vacancy_id: typing.Optional[str] = None
    name: typing.Optional[str] = None
