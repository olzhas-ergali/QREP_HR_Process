import logging

from API.infrastructure.database.vacation import StaffVacation, VacationDays
from sqlalchemy.ext.asyncio import AsyncSession
import datetime


async def add_vacation_days(
        db_session
):
    session: AsyncSession = db_session()
    staffs = await StaffVacation.get_all_user(session)
    logging.info(f"Добавляем дни")
    for staff in staffs:
        vacations = await VacationDays.get_staff_vac_by_id(
            staff.id,
            session
        )
        if vacations:
            v = vacations[-1]
            logging.info(v.vacation_start)
            logging.info(v.vacation_start and datetime.datetime.today() < v.vacation_start)
            if v.vacation_end and datetime.datetime.today() > v.vacation_end:
                v.vacation_code = None
                v.vacation_end = None
                v.vacation_start = None
            if (v.vacation_start and datetime.datetime.today() < v.vacation_start) or v.vacation_code in ['935', '936'] or not v.vacation_code:
                logging.info(f"{staff.iin}: {v.year}")
                v.dbl_days = round(0.066 + v.dbl_days, 3)
                import math
                v.days = math.floor(v.dbl_days + 0.5)
                session.add(v)

    await session.commit()
    await session.close()


async def check_work_period(
        db_session
):
    session: AsyncSession = db_session()
    staffs = await StaffVacation.get_all_user(session)
    for staff in staffs:
        date_today = datetime.datetime.today().date()
#        date_today = datetime.datetime.strptime("02.05.2025", "%d.%m.%Y")
        date_receipt = datetime.datetime.strptime(
            f"{staff.date_receipt.day}.{staff.date_receipt.month}.{date_today.year - 1}",
            "%d.%m.%Y").date()
        vacations = await VacationDays.get_staff_vac_by_id(
            session=session,
            staff_id=staff.id
        )
        vac = vacations[-1]
        if (date_today - date_receipt).days >= 365 and vac.year != date_today.year + 1:
            logging.info(f"Меняем период у {staff.iin} ({staff.id}) {date_today} - {date_receipt} добавляем {date_today.year + 1}")
            vacation = VacationDays(
                year=date_today.year + 1,
                staff_vac_id=staff.id,
                days=0,
                dbl_days=0.0
            )
            session.add(vacation)
    await session.commit()
    await session.close()
