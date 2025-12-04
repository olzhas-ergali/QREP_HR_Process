import datetime
import logging

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
    staff = await StaffVacation.get_by_guid(guid=vac.guid, session=session)
    start = datetime.datetime.strptime(vac.date_start, "%d.%m.%Y")
    today = datetime.datetime.today()
    end = datetime.datetime.strptime(vac.date_end, "%d.%m.%Y")
    days_count = get_fact_days_vacation(start, end)
    days_before_vacation = get_fact_days_vacation(today, start)
    logging.info(f"days_count: {days_count}")
    logging.info(f"days_before_vacation: {days_before_vacation}")
    vac_days = 0
    if staff:
        vacation = await VacationDays.get_staff_vac_by_id(staff.id, session)
        for v in vacation:
            vac_days += v.dbl_days
    vac_days = int(round(vac_days + days_before_vacation * 0.066))
    if days_count > vac_days:
        return {
            'status_code': error_status_code,
            'vacation_days': vac_days
        }
    return {
        'status_code': 200,
        'vacation_days': vac_days
    }
