import datetime
import typing

from pydantic import BaseModel


class ModelVacation(BaseModel):
    guid: typing.Optional[str] = None
    date_start: typing.Optional[str] = None
    date_end: typing.Optional[str] = None
    is_vacation: typing.Optional[str] = None


class ModelDismissal(BaseModel):
    guid: typing.Optional[str] = None
    date_dismissal: typing.Optional[str] = None
