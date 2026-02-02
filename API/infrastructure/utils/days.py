import datetime
import logging
import math

from API.infrastructure.utils.calendar import vacations_days, vacations_weekend
from sqlalchemy.ext.asyncio import AsyncSession
from API.infrastructure.database.vacation import VacationDays, StaffVacation


def get_fact_days_vacation(
        date_start: datetime.datetime,
        date_end: datetime.datetime,
):
    days_count = 0
    while True:
        if date_start > date_end:
            break
        if date_start not in vacations_days:
            days_count += 1
        date_start = date_start + datetime.timedelta(days=1)
    return days_count


def get_work_days_vacation(
        date_start: datetime.datetime,
        date_end: datetime.datetime,
):
    days_count = 0
    while True:
        if date_start > date_end:
            break
        #[datetime.datetime.strptime('06.06.2025', "%d.%m.%Y")]
        if date_start not in vacations_days and date_start.weekday() not in [5, 6] and date_start not in vacations_weekend:
            days_count += 1
        date_start = date_start + datetime.timedelta(days=1)
    return days_count


async def parse_date(date):
    formats = [
        "%d-%m-%Y %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d-%m-%Y %H:%M:%S"
    ]
    for ftm in formats:
        try:
            d = datetime.datetime.strptime(date, ftm)
            return d
        except Exception as ex:
            pass
    raise ValueError(f"Не найден формат для даты {date}")


async def get_vacation_days(
        session: AsyncSession,
        vac,
        error_status_code: int
):
    """
    Проверяет доступные дни отпуска для сотрудника.

    ОБНОВЛЕНО: Теперь использует новую расчётную логику (vacation_calculator)
    вместо чтения из старой таблицы vacation_days.
    """
    from API.infrastructure.utils.vacation_calculator import calculate_vacation_report

    staff = await StaffVacation.get_by_guid(guid=vac.guid, session=session)

    if not staff:
        logging.warning(f"Сотрудник с GUID '{vac.guid}' не найден")
        return {
            'status_code': error_status_code,
            'vacation_days': 0,
            'message': 'Сотрудник не найден'
        }

    if not staff.date_receipt:
        logging.warning(f"У сотрудника '{staff.fullname}' не указана дата приема")
        return {
            'status_code': error_status_code,
            'vacation_days': 0,
            'message': 'Не указана дата приема'
        }

    start = datetime.datetime.strptime(vac.date_start, "%d.%m.%Y")
    end = datetime.datetime.strptime(vac.date_end, "%d.%m.%Y")
    days_count = get_fact_days_vacation(start, end)

    logging.info(f"days_count (запрошено): {days_count}")

    # Используем новый калькулятор для расчёта баланса (на дату начала отпуска)
    report = await calculate_vacation_report(staff, session, as_of_date=start.date())
    vac_days = math.floor(report["total_balance"] + 0.5)

    logging.info(f"vacation_days (доступно): {vac_days}")

    if days_count > vac_days:
        return {
            'status_code': error_status_code,
            'vacation_days': vac_days
        }
    return {
        'status_code': 200,
        'vacation_days': vac_days
    }
