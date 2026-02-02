"""
Сервис расчета отпускных дней.
Реализует "расчетную" логику (формула от стажа) вместо "накопительной" (ежедневное прибавление).
"""
import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from API.infrastructure.database.vacation import StaffVacation, VacationHistory


# Константы
DAYS_PER_YEAR = 24  # Стандарт: 24 дня отпуска за полный год
DAYS_IN_YEAR = 365  # Дней в году для расчета


@dataclass
class WorkPeriod:
    """Рабочий год (период) сотрудника"""
    start_date: datetime.date
    end_date: datetime.date
    is_current: bool  # Текущий (неполный) период
    earned: float = 0.0  # Начислено дней
    used: float = 0.0    # Использовано дней
    balance: float = 0.0 # Остаток дней

    def format_period(self) -> str:
        """Форматирование периода в строку"""
        return f"{self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')}"


def generate_work_periods(hire_date: datetime.date, today: datetime.date = None) -> List[WorkPeriod]:
    """
    Генерирует список рабочих лет (периодов) от даты приема до текущей даты.

    Пример: Если принят 02.05.2023, то:
    - Период 1: 02.05.2023 — 01.05.2024
    - Период 2: 02.05.2024 — 01.05.2025 (текущий)
    """
    if today is None:
        today = datetime.date.today()

    periods = []
    period_start = hire_date
    period_num = 1

    while period_start <= today:
        # Конец периода = начало + 1 год - 1 день
        period_end = datetime.date(
            period_start.year + 1,
            period_start.month,
            period_start.day
        ) - datetime.timedelta(days=1)

        # Определяем, текущий ли это период
        is_current = period_end >= today

        periods.append(WorkPeriod(
            start_date=period_start,
            end_date=period_end if not is_current else today,
            is_current=is_current
        ))

        # Переход к следующему периоду
        period_start = period_end + datetime.timedelta(days=1)
        period_num += 1

        # Защита от бесконечного цикла
        if period_num > 100:
            break

    return periods


def calculate_earned_days(period: WorkPeriod) -> float:
    """
    Расчет начисленных дней за период.

    - Если период прошел полностью: Начислено = 24 дня
    - Если период текущий (неполный): ДнейОтработано * (24 / 365)
    """
    if not period.is_current:
        # Полный период
        return float(DAYS_PER_YEAR)
    else:
        # Неполный (текущий) период
        days_worked = (period.end_date - period.start_date).days + 1
        earned = days_worked * (DAYS_PER_YEAR / DAYS_IN_YEAR)
        return round(earned, 2)


def distribute_used_days_fifo(
    periods: List[WorkPeriod],
    total_used: int
) -> List[WorkPeriod]:
    """
    Распределяет использованные дни по периодам по принципу FIFO.
    Сначала закрывается долг за самый старый год, затем за следующий.
    """
    remaining_to_distribute = float(total_used)

    for period in periods:
        if remaining_to_distribute <= 0:
            period.used = 0.0
        else:
            # Сколько можем списать с этого периода
            can_use = min(period.earned, remaining_to_distribute)
            period.used = can_use
            remaining_to_distribute -= can_use

        # Рассчитываем баланс
        period.balance = round(period.earned - period.used, 2)

    return periods


async def calculate_vacation_report(
    staff: StaffVacation,
    session: AsyncSession,
    as_of_date: datetime.date = None
) -> Dict:
    """
    Основная функция расчета отпускного отчета.

    Параметры:
    - staff: Сотрудник
    - session: Сессия БД
    - as_of_date: Дата, на которую рассчитывать баланс (по умолчанию - сегодня).
                  Используется для расчета баланса на дату начала отпуска.

    Возвращает:
    - fullname: ФИО сотрудника
    - iin: ИИН
    - hire_date: Дата приема
    - total_balance: Итого доступно дней
    - breakdown: Детализация по периодам
    """
    # Получаем дату приема
    hire_date = staff.date_receipt
    if isinstance(hire_date, datetime.datetime):
        hire_date = hire_date.date()

    # Дата расчета: либо переданная, либо сегодня
    calc_date = as_of_date if as_of_date else datetime.date.today()

    # 1. Генерируем рабочие периоды
    periods = generate_work_periods(hire_date, calc_date)

    # 2. Рассчитываем "Начислено" для каждого периода
    for period in periods:
        period.earned = calculate_earned_days(period)

    # 3. Получаем общее количество использованных дней из истории
    total_used = await VacationHistory.get_total_used_days(staff.id, session)

    # 4. Распределяем использованные дни по FIFO
    periods = distribute_used_days_fifo(periods, total_used)

    # 5. Считаем общий баланс
    total_balance = sum(p.balance for p in periods)

    # 6. Формируем результат
    breakdown = []
    for period in periods:
        breakdown.append({
            "period": period.format_period(),
            "earned": period.earned,
            "used": period.used,
            "balance": period.balance
        })

    return {
        "fullname": staff.fullname,
        "iin": staff.iin,
        "hire_date": staff.date_receipt.strftime('%d.%m.%Y'),
        "total_balance": round(total_balance, 2),
        "breakdown": breakdown
    }


async def check_vacation_balance(
    staff_id: int,
    days_requested: int,
    session: AsyncSession,
    as_of_date: datetime.date = None
) -> Tuple[bool, float, str]:
    """
    Проверяет, хватает ли дней отпуска для запроса.

    Параметры:
    - staff_id: ID сотрудника
    - days_requested: Запрашиваемое количество дней
    - session: Сессия БД
    - as_of_date: Дата, на которую проверять баланс (обычно дата начала отпуска)

    Возвращает:
    - bool: Хватает ли дней
    - float: Доступный баланс
    - str: Сообщение
    """
    from sqlalchemy import select

    # Получаем сотрудника
    stmt = select(StaffVacation).where(StaffVacation.id == staff_id)
    staff = await session.scalar(stmt)

    if not staff:
        return False, 0.0, "Сотрудник не найден"

    # Рассчитываем баланс на указанную дату (или на сегодня)
    report = await calculate_vacation_report(staff, session, as_of_date)
    total_balance = report["total_balance"]

    if days_requested > total_balance:
        return False, total_balance, f"Недостаточно дней. Запрошено: {days_requested}, Доступно: {total_balance}"

    return True, total_balance, "OK"
