import logging
import typing
import datetime
from datetime import timedelta

from API.config import settings

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse

from API.domain.authentication import security, validate_security
from API.infrastructure.database.session import db_session
from API.infrastructure.database.vacation import VacationDays, StaffVacation
from API.infrastructure.utils.days import get_fact_days_vacation, get_work_days_vacation, get_vacation_days
from API.infrastructure.utils.calendar import months_name
from API.infrastructure.models.vacation import ModelVacation, ModelDismissal
from API.infrastructure.utils.tasks import add_vacation_days, check_work_period

router = APIRouter()


@router.post('/v1/vacation/take_vacation',
             tags=['Vacation'],
             summary="Функция что бы взять отпуск"
             )
async def take_vacation(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        vac: ModelVacation
):
    session: AsyncSession = db_session.get()
    staff = await StaffVacation.get_by_guid(guid=vac.guid, session=session)
    logging.info(
f'''
{vac.date_start}
{vac.date_end}
{vac.is_vacation}
{vac.guid}
'''
    )
    #result = await get_vacation_days(session, vac, 418)
    #if result.get('status_code') == 418:
    #    return result
    years = []
    start = datetime.datetime.strptime(vac.date_start, "%d.%m.%Y")
    end = datetime.datetime.strptime(vac.date_end, "%d.%m.%Y")
    days_count = get_fact_days_vacation(start, end)
    works_day = get_work_days_vacation(start, end)
    today = datetime.datetime.today()
    days_before_vacation = get_fact_days_vacation(today, start)
    logging.info(days_count)
    text = '- {days} календарных дней за период работы с {to} года по {f} года'
    text_day = '{d} {m} {y}'
    works_year = []
    if staff:
        if staff and days_count > 0 and vac.is_vacation in ['932', '933']:
            vacation_periods = await VacationDays.get_staff_vac_by_id(staff.id, session)
            days_to_deduct = days_count

            for period in vacation_periods:
                period.vacation_code = vac.is_vacation
                period.vacation_start = start
                period.vacation_end = end
                
                if days_to_deduct <= 0:
                    # Все дни уже списаны, но нам все равно нужно обновить даты и код отпуска для всех периодов
                    session.add(period)
                    continue

                available_days_in_period = period.dbl_days

                if available_days_in_period > 0:
                    days_from_this_period = min(days_to_deduct, available_days_in_period)

                    # Формируем текст для приказа
                    works_year.append(f"{staff.date_receipt.strftime('%d.%m')}.{period.year - 1}")
                    date_to = text_day.format(d=staff.date_receipt.day, m=months_name.get(staff.date_receipt.month), y=period.year - 1)
                    works_year.append(f"{staff.date_receipt.strftime('%d.%m')}.{period.year}")
                    date_from = text_day.format(d=staff.date_receipt.day, m=months_name.get(staff.date_receipt.month), y=period.year)
                    import math
                    years.append(text.format(days=f'{math.floor(days_from_this_period + 0.5):02d}', to=date_to, f=date_from) + ";")

                    # Списываем дни
                    period.dbl_days -= days_from_this_period
                    period.days = math.floor(period.dbl_days + 0.5)
                    days_to_deduct -= days_from_this_period
                
                session.add(period)

        await session.commit()
    logging.info(works_year)
    if vac.is_vacation not in ['935', '936'] and len(years) > 1:
        text = years[-1]
        years[-1] = text.replace(";", ".")
        return {
            'status_code': 200,
            'work_period_list': "\n".join(years),
            'days':  get_fact_days_vacation(start, end),
            'work_days': works_day,
            'work_period': f"с {works_year[0]} года по {works_year[-1]} года",
            'vacation_days': ''
        }
    elif vac.is_vacation not in ['935', '936'] and len(years) == 1:
        return {
            'status_code': 200,
            'work_period_list': "",
            'days': get_fact_days_vacation(start, end),
            'work_days': works_day,
            'work_period': f"с {works_year[0]} года по {works_year[-1]} года",
            'vacation_days': ''
        }
    else:
        return {
            'status_code': 200,
            'work_period_list': "",
            'days': "",
            'work_days': "",
            'work_period': "",
            'vacation_days': ''
        }


@router.post('/v1/qa/vacation/take_vacation', deprecated=True)
async def take_vacation(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        vacation: ModelVacation
):
    session: AsyncSession = db_session.get()
    for k, v in vacation:
        logging.info(f"{k}: {v}")
    return {
        'status_code': 200,
        'message': f"{vacation.guid}"
    }


@router.post('/v1/vacation/available',
             tags=['Vacation'],
             summary="Для проверки колчество дней")
async def get_days_for_vacation(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        vac: ModelVacation
):
    session: AsyncSession = db_session.get()
    return await get_vacation_days(session, vac, 417)


@router.get('/v1/vacation/dismissal',
            tags=['Vacation'],
            summary="Для получение колчество дней для уволнение")
async def get_days_for_dismissal(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        dismissal_model: ModelDismissal
):
    session: AsyncSession = db_session.get()
    staff = await StaffVacation.get_by_guid(guid=dismissal_model.guid, session=session)
    start = datetime.datetime.today()
    end = datetime.datetime.strptime(dismissal_model.date_dismissal, "%d.%m.%Y")
    days_count = get_fact_days_vacation(start, end)
    logging.info(f"days_count: {days_count * 0.066}")
    vac_days = 0
    logging.info(f"vac_days: {vac_days}")
    text = '- {days} календарных дней за период работы с {to} года по {f} года'
    text_day = '{d} {m} {y}'
    works_year = []
    years = []
    if staff:
        vacation = await VacationDays.get_staff_vac_by_id(staff.id, session)
        for i, v in enumerate(vacation):
            date_to = text_day.format(
                d=staff.date_receipt.day,
                m=months_name.get(staff.date_receipt.month),
                y=v.year - 1
            )
            date_from = text_day.format(
                d=staff.date_receipt.day,
                m=months_name.get(staff.date_receipt.month),
                y=v.year
            )
            works_year.append(
                f"{f'0{staff.date_receipt.day}' if staff.date_receipt.day < 10 else staff.date_receipt.day}.{f'0{staff.date_receipt.month}' if staff.date_receipt.month < 10 else staff.date_receipt.month}.{v.year - 1}")
            works_year.append(
                f"{f'0{staff.date_receipt.day}' if staff.date_receipt.day < 10 else staff.date_receipt.day}.{f'0{staff.date_receipt.month}' if staff.date_receipt.month < 10 else staff.date_receipt.month}.{v.year}")
            #days_for_format = days_count if v.dbl_days - days_count > 0 else v.days
            days_for_format = v.days
            if i == len(vacation) - 1:
                date_from = text_day.format(
                    d=end.day,
                    m=months_name.get(end.month),
                    y=end.year
                )
                works_year[-1] = f"{f'0{end.day}' if end.day < 10 else end.day}.{f'0{end.month}' if end.month < 10 else end.month}.{end.year}"
                days_for_format = round(v.dbl_days + 0.066 * days_count)
            years.append(
                text.format(
                    days=f'0{int(days_for_format)}' if days_for_format < 10 else int(days_for_format),
                    to=date_to,
                    f=date_from
                ) + ";"
            )
            vac_days += days_for_format
    logging.info(f"vac_days: {vac_days}")

    if len(years) > 1:
        text = years[-1]
        years[-1] = text.replace(";", ".")
        return {
            'status_code': 200,
            'work_period_list': "\n".join(years),
            # 'days': days_count,
            'work_period': f"с {works_year[0]} года по {works_year[-1]} года",
            'vacation_days': vac_days
        }
    elif len(years) == 1:
        return {
            'status_code': 200,
            'work_period_list': "",
            # 'days': days_count,
            'work_period': f"с {works_year[0]} года по {works_year[-1]} года",
            'vacation_days': vac_days
        }


@router.post('/v1/vacation/dismissal',
             tags=['Vacation'],
             summary="Для уволнение сотрудника")
async def get_days_for_dismissal(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        dismissal_model: ModelDismissal
):
    session: AsyncSession = db_session.get()
    staff = await StaffVacation.get_by_guid(guid=dismissal_model.guid, session=session)
    if staff:
        staff.is_fired = True
        session.add(staff)
        await session.commit()
    return {
        "status_code": 200,
        "message": "Сотрудник уволен"
    }


@router.post("/v1/vacation/add",
             tags=['Vacation'],
             summary="Для запуска тасков по отпускным дням")
async def add_vacation_days_process(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)]
):
    #session: AsyncSession = db_session.get()
    await add_vacation_days(db_session.get)

    return {
        'status_code': 200,
        'message': "Дни добавлены"
    }
