import logging
import typing
import datetime
from datetime import timedelta

from API.config import settings
from sqlalchemy import or_, select

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse

from API.domain.authentication import security, validate_security
from API.infrastructure.database.session import db_session
from API.infrastructure.database.vacation import VacationDays, StaffVacation, VacationHistory
from API.infrastructure.utils.days import get_fact_days_vacation, get_work_days_vacation, get_vacation_days
from API.infrastructure.utils.calendar import months_name
from API.infrastructure.models.vacation import ModelVacation, ModelDismissal
from API.infrastructure.utils.tasks import add_vacation_days, check_work_period
from API.infrastructure.models.vacation import ModelCalculateDays, VacationReportRequest, VacationHistoryCreate
from API.infrastructure.utils.vacation_calculator import calculate_vacation_report, check_vacation_balance

router = APIRouter()


@router.post('/v1/vacation/take_vacation',
             tags=['Vacation'],
             summary="Функция что бы взять отпуск"
             )
async def take_vacation(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        vac: ModelVacation
):
    """
    Оформление отпуска сотрудника.

    НОВАЯ ЛОГИКА:
    1. Проверяет баланс по расчетной формуле (от даты приема)
    2. Записывает факт отпуска в таблицу vacation_history
    3. Дни больше НЕ списываются из vacation_days (таблица остается для обратной совместимости)

    Коды отпуска:
    - 932, 933: Оплачиваемый отпуск (дни списываются)
    - 935, 936: Специальные типы (без списания дней)
    """
    session: AsyncSession = db_session.get()
    staff = await StaffVacation.get_by_guid(guid=vac.guid, session=session)

    logging.info(
        f'''
take_vacation request:
date_start: {vac.date_start}
date_end: {vac.date_end}
is_vacation: {vac.is_vacation}
guid: {vac.guid}
'''
    )

    if not staff:
        return {
            'status_code': 404,
            'message': 'Сотрудник не найден'
        }

    years = []
    start = datetime.datetime.strptime(vac.date_start, "%d.%m.%Y")
    end = datetime.datetime.strptime(vac.date_end, "%d.%m.%Y")
    days_count = get_fact_days_vacation(start, end)
    works_day = get_work_days_vacation(start, end)

    logging.info(f"Requested vacation days: {days_count}")

    text = '- {days} календарных дней за период работы с {to} года по {f} года'
    text_day = '{d} {m} {y}'
    works_year = []

    # Обработка оплачиваемого отпуска (932, 933)
    if days_count > 0 and vac.is_vacation in ['932', '933']:
        # 1. Проверяем баланс по новой расчетной логике (на дату начала отпуска)
        has_balance, available_balance, message = await check_vacation_balance(
            staff.id, days_count, session, as_of_date=start.date()
        )

        if not has_balance:
            return {
                'status_code': 417,
                'message': message,
                'available_balance': available_balance,
                'requested_days': days_count
            }

        # 2. Записываем в vacation_history (новый источник правды)
        await VacationHistory.create(
            staff_id=staff.id,
            date_start=start.date(),
            date_end=end.date(),
            days_count=days_count,
            vacation_type='paid',
            comment=f"Код отпуска: {vac.is_vacation}",
            session=session
        )

        # 3. Формируем текст для приказа (используем рабочие периоды)
        from API.infrastructure.utils.vacation_calculator import generate_work_periods

        hire_date = staff.date_receipt
        if isinstance(hire_date, datetime.datetime):
            hire_date = hire_date.date()

        periods = generate_work_periods(hire_date, datetime.date.today())

        for period in periods:
            works_year.append(f"{staff.date_receipt.strftime('%d.%m')}.{period.start_date.year}")
            date_to = text_day.format(
                d=staff.date_receipt.day,
                m=months_name.get(staff.date_receipt.month),
                y=period.start_date.year
            )
            works_year.append(f"{staff.date_receipt.strftime('%d.%m')}.{period.end_date.year}")
            date_from = text_day.format(
                d=staff.date_receipt.day,
                m=months_name.get(staff.date_receipt.month),
                y=period.end_date.year
            )
            years.append(text.format(days=f'{days_count:02d}', to=date_to, f=date_from) + ";")
            break  # Берем только текущий период для отображения

        # 4. Обновляем старую таблицу vacation_days для обратной совместимости
        vacation_periods = await VacationDays.get_staff_vac_by_id(staff.id, session)
        for period in vacation_periods:
            period.vacation_code = vac.is_vacation
            period.vacation_start = start
            period.vacation_end = end
            session.add(period)

    await session.commit()

    logging.info(f"works_year: {works_year}")

    if vac.is_vacation not in ['935', '936'] and len(years) > 1:
        text = years[-1]
        years[-1] = text.replace(";", ".")
        return {
            'status_code': 200,
            'work_period_list': "\n".join(years),
            'days': get_fact_days_vacation(start, end),
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
            'work_period': f"с {works_year[0]} года по {works_year[-1]} года" if works_year else "",
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
            days_for_format = v.days or 0
            if i == len(vacation) - 1:
                date_from = text_day.format(
                    d=end.day,
                    m=months_name.get(end.month),
                    y=end.year
                )
                works_year[-1] = f"{f'0{end.day}' if end.day < 10 else end.day}.{f'0{end.month}' if end.month < 10 else end.month}.{end.year}"
                days_for_format = round((v.dbl_days or 0) + 0.066 * days_count)
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


@router.post('/v1/vacation/calculate_days_simple',
             tags=['Vacation'],
             summary="Расчет накопленных дней по формуле (без учета потраченных)")
async def calculate_days_simple(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        data: ModelCalculateDays
):
    session: AsyncSession = db_session.get()

    # 1. Ищем сотрудника (по ИИН или по ФИО)
    # Используем or_ для поиска совпадения
    stmt = select(StaffVacation).where(
        or_(
            StaffVacation.iin == data.identifier,
            StaffVacation.fullname.ilike(f"%{data.identifier}%")
        )
    )
    staff = await session.scalar(stmt)

    if not staff:
        return {
            'status_code': 404,
            'message': f"Сотрудник с данными '{data.identifier}' не найден"
        }

    # 2. Логика расчета
    today = datetime.datetime.now()
    # Если в БД date_receipt это datetime, приводим к дате, если нужно, но для разницы это не критично
    # date_receipt в модели объявлен как DateTime

    # Считаем разницу во времени
    delta = today - staff.date_receipt

    # Количество календарных дней стажа
    days_worked = delta.days

    # Коэффициент из твоей задачи (task.py)
    COEFFICIENT = 0.066

    # Считаем итог
    calculated_days = days_worked * COEFFICIENT

    return {
        'status_code': 200,
        'data': {
            'fullname': staff.fullname,
            'iin': staff.iin,
            'date_receipt': staff.date_receipt.strftime('%d.%m.%Y'),
            'days_worked_total': days_worked, # Сколько дней он уже работает в компании
            'calculated_vacation_days': round(calculated_days, 2), # Итого накоплено дней
            'formula': f"{days_worked} (дней стажа) * {COEFFICIENT}"
        }
    }


@router.post('/v1/vacation/force_recalculate',
             tags=['Vacation'],
             summary="ПРИНУДИТЕЛЬНО пересчитать и обновить дни в БД по дате приема")
async def force_recalculate_days(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        data: ModelCalculateDays
):
    session: AsyncSession = db_session.get()
    identifier = data.identifier

    # 1. Ищем сотрудника
    stmt = select(StaffVacation).where(
        or_(
            StaffVacation.iin == identifier,
            StaffVacation.fullname.ilike(f"%{identifier}%")
        )
    )
    staff = await session.scalar(stmt)

    if not staff:
        return {'status_code': 404, 'message': 'Сотрудник не найден'}

    # 2. Считаем сколько он работает
    today = datetime.datetime.now()
    if not staff.date_receipt:
         return {'status_code': 400, 'message': 'У сотрудника не указана дата приема'}

    start_date = staff.date_receipt
    if isinstance(start_date, datetime.date) and not isinstance(start_date, datetime.datetime):
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())

    delta = today - start_date
    days_worked = delta.days

    if days_worked < 0:
         return {'status_code': 400, 'message': 'Дата приема в будущем!'}

    # 3. Считаем сколько ДОЛЖНО быть дней всего
    total_earned_days = days_worked * 0.066

    # 4. Обновляем записи
    vac_records = await VacationDays.get_staff_vac_by_id(staff.id, session)

    if not vac_records:
        new_vac = VacationDays(
            staff_vac_id=staff.id,
            year=today.year,
            days=int(total_earned_days),
            dbl_days=total_earned_days
        )
        session.add(new_vac)
    else:
        import math
        last_record = vac_records[-1]
        last_record.dbl_days = float(total_earned_days)
        last_record.days = math.floor(total_earned_days + 0.5)
        session.add(last_record)

    await session.commit()

    return {
        'status_code': 200,
        'message': 'Данные в БД обновлены',
        'data': {
            'staff': staff.fullname,
            'days_worked': days_worked,
            'new_balance': total_earned_days
        }
    }


@router.post('/v1/vacation/calculate-report',
             tags=['Vacation'],
             summary="Расчет отпускных дней с детализацией по периодам (рабочим годам)")
async def calculate_report(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        data: VacationReportRequest
):
    """
    Рассчитывает отпускные дни сотрудника с детализацией по периодам.

    Алгоритм:
    1. Определяет рабочие годы (периоды) от даты приема
    2. Рассчитывает "Начислено" для каждого периода (24 дня за полный год)
    3. Получает историю использованных отпусков из vacation_history
    4. Распределяет использованные дни по принципу FIFO
    5. Возвращает баланс по каждому периоду и общий итог
    """
    session: AsyncSession = db_session.get()

    # 1. Ищем сотрудника (по ИИН или по ФИО)
    stmt = select(StaffVacation).where(
        or_(
            StaffVacation.iin == data.identifier,
            StaffVacation.fullname.ilike(f"%{data.identifier}%")
        )
    )
    staff = await session.scalar(stmt)

    if not staff:
        return {
            'status_code': 404,
            'message': f"Сотрудник с данными '{data.identifier}' не найден"
        }

    if not staff.date_receipt:
        return {
            'status_code': 400,
            'message': 'У сотрудника не указана дата приема (date_receipt)'
        }

    # 2. Рассчитываем отчет
    report_data = await calculate_vacation_report(staff, session)

    return {
        'status_code': 200,
        'data': report_data
    }


@router.get('/v1/vacation/history/{identifier}',
            tags=['Vacation'],
            summary="Получить историю отпусков сотрудника")
async def get_vacation_history(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        identifier: str
):
    """
    Возвращает полную историю отпусков сотрудника из таблицы vacation_history.
    """
    session: AsyncSession = db_session.get()

    # Ищем сотрудника
    stmt = select(StaffVacation).where(
        or_(
            StaffVacation.iin == identifier,
            StaffVacation.fullname.ilike(f"%{identifier}%")
        )
    )
    staff = await session.scalar(stmt)

    if not staff:
        return {
            'status_code': 404,
            'message': f"Сотрудник с данными '{identifier}' не найден"
        }

    # Получаем историю отпусков
    history = await VacationHistory.get_by_staff_id(staff.id, session)

    history_items = []
    for item in history:
        history_items.append({
            'id': str(item.id),
            'date_start': item.date_start.strftime('%d.%m.%Y'),
            'date_end': item.date_end.strftime('%d.%m.%Y'),
            'days_count': item.days_count,
            'type': item.type,
            'created_at': item.created_at.strftime('%d.%m.%Y %H:%M'),
            'comment': item.comment
        })

    return {
        'status_code': 200,
        'data': {
            'fullname': staff.fullname,
            'iin': staff.iin,
            'total_used_days': sum(h['days_count'] for h in history_items),
            'history': history_items
        }
    }


@router.post('/v1/vacation/add-history',
             tags=['Vacation'],
             summary="Добавить запись в историю отпусков (для миграции данных)")
async def add_vacation_history(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        data: VacationHistoryCreate
):
    """
    Добавляет запись в историю отпусков.
    Используется для миграции старых данных или ручных корректировок.

    Типы отпуска:
    - paid: оплачиваемый отпуск
    - unpaid: за свой счет
    - migration_balance: корректирующая запись для миграции
    """
    session: AsyncSession = db_session.get()

    # Ищем сотрудника
    stmt = select(StaffVacation).where(
        or_(
            StaffVacation.iin == data.identifier,
            StaffVacation.fullname.ilike(f"%{data.identifier}%")
        )
    )
    staff = await session.scalar(stmt)

    if not staff:
        return {
            'status_code': 404,
            'message': f"Сотрудник с данными '{data.identifier}' не найден"
        }

    # Парсим даты
    try:
        start = datetime.datetime.strptime(data.date_start, "%d.%m.%Y").date()
        end = datetime.datetime.strptime(data.date_end, "%d.%m.%Y").date()
    except ValueError:
        return {
            'status_code': 400,
            'message': 'Неверный формат даты. Используйте DD.MM.YYYY'
        }

    # Создаем запись
    await VacationHistory.create(
        staff_id=staff.id,
        date_start=start,
        date_end=end,
        days_count=data.days_count,
        vacation_type=data.type,
        comment=data.comment,
        session=session
    )

    await session.commit()

    return {
        'status_code': 200,
        'message': 'Запись добавлена в историю отпусков',
        'data': {
            'staff': staff.fullname,
            'date_start': data.date_start,
            'date_end': data.date_end,
            'days_count': data.days_count,
            'type': data.type
        }
    }
