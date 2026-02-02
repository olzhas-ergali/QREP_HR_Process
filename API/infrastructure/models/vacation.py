import datetime
import typing
from typing import List

from pydantic import BaseModel


class ModelVacation(BaseModel):
    guid: typing.Optional[str] = None
    date_start: typing.Optional[str] = None
    date_end: typing.Optional[str] = None
    is_vacation: typing.Optional[str] = None


class ModelDismissal(BaseModel):
    guid: typing.Optional[str] = None
    date_dismissal: typing.Optional[str] = None


class ModelCalculateDays(BaseModel):
    identifier: typing.Optional[str] = None


# === Схемы для calculate-report ===

class VacationReportRequest(BaseModel):
    """Запрос на расчет отпускного отчета"""
    identifier: str  # ИИН или ФИО


class PeriodBreakdown(BaseModel):
    """Детализация по одному рабочему году"""
    period: str       # "02.05.2023 - 01.05.2024"
    earned: float     # Заработано за этот год
    used: float       # Потрачено за этот год
    balance: float    # Остаток за этот год


class VacationReportData(BaseModel):
    """Данные отчета по отпускам"""
    fullname: str
    iin: str
    hire_date: str
    total_balance: float                # Итого доступно дней на сегодня
    breakdown: List[PeriodBreakdown]    # Детализация по периодам


class VacationReportResponse(BaseModel):
    """Ответ с отчетом по отпускам"""
    status_code: int
    data: VacationReportData


# === Схемы для истории отпусков ===

class VacationHistoryCreate(BaseModel):
    """Создание записи в истории отпусков"""
    identifier: str  # ИИН или ФИО
    date_start: str  # Формат: DD.MM.YYYY
    date_end: str    # Формат: DD.MM.YYYY
    days_count: int
    type: str = 'paid'
    comment: typing.Optional[str] = None


class VacationHistoryItem(BaseModel):
    """Элемент истории отпусков"""
    id: str
    date_start: str
    date_end: str
    days_count: int
    type: str
    created_at: str
    comment: typing.Optional[str] = None
