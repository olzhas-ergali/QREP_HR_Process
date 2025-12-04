import logging
import typing
import datetime

from API.config import settings

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse

from API.domain.authentication import security, validate_security
from API.infrastructure.database.session import db_session
from API.lib.hh.HeadHunter import HeadHunter
from API.lib.schemas.vacation import PublicationVacation, VacationItems, Salary
from API.lib.schemas.directories import Directories, ItemDirectories
from API.lib.schemas.resume import ItemAreas
from API.infrastructure.models.recruiting import ModelVacancies, ModelVac2, ModelDiscard
from API.infrastructure.database.recruiting import Token, Vacancies
from API.lib.bitrix import dates

router = APIRouter()


@router.get('/v1/recruiting/managers',
            tags=['HeadHunter'],
            summary="Получение менеджеров")
async def get_managers(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)]
):

    session: AsyncSession = db_session.get()
    token = await Token.get_token(session)
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )
    managers = await hh.get_managers()
    token.access_token = hh.basic_token
    token.refresh_token = hh.ref_token
    session.add(token)
    await session.commit()
    return managers


@router.post('/v1/recruiting/publication_vacancy',
             tags=['HeadHunter'],
             summary="Публикация вакансий")
async def publication_vacancy(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        vac: ModelVacancies
):
    logging.info(vac.name)
    for k, v in vac:
        logging.info(f"{k}: {v}")
    session: AsyncSession = db_session.get()
    token = await Token.get_token(session)
    #token = "USERHOD1HP6BU2HRPEJEOA018HGO3PQKTBKIO79MS45MPUDM657BB2BI5JBBQ9VN"
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )
    items_work_format: ItemDirectories = await hh.get_dictionaries('work_format')
    items_work_schedule: ItemDirectories = await hh.get_dictionaries('work_schedule_by_days')
    items_working_hours: ItemDirectories = await hh.get_dictionaries('working_hours')
    items_vacancy_billing_type: ItemDirectories = await hh.get_dictionaries('vacancy_billing_type')
    items_types: ItemDirectories = await hh.get_dictionaries('vacancy_type')
    items_employment_form: ItemDirectories = await hh.get_dictionaries('employment_form')
    items_experience: ItemDirectories = await hh.get_dictionaries('experience')
    items_role = await hh.get_roles()
    items_template = await hh.get_brand_templates()
    if not vac.type_work:
        vac.type_work = '0'

    address = await hh.get_address()
    managers = await hh.get_managers()
    item_areas: ItemAreas = await hh.get_areas()
    logging.info(vac.toDo.split('*'))
    to_do = [f"<li>{i}</li>\n" if i != "" else "" for i in vac.toDo.split('*')]
    except_candidates = [f"<li>{i}</li>\n" if i != "" else "" for i in vac.exceptCandidates.split('*')]
    offer = [f"<li>{i}</li>\n" if i != "" else "" for i in vac.offer.split('*')]
    v = PublicationVacation(
        name=vac.name,
        description=f'''<strong>Чем предстоит заниматься:</strong>
<ul>
{"".join(to_do)}
</ul>
<strong>Что мы ждем от кандидатов:</strong>
<ul>
{"".join(except_candidates)}
</ul>
<strong>Мы предлагаем:</strong>
<ul>
{"".join(offer)}
</ul>
    ''',
        work_format=[
            items_work_format.get_item_by_id(dates.work_format.get(vac.workFormat)).to_json()
        ],
        area=item_areas.get_item_by_id(dates.cities.get(vac.city)).to_json(),
        working_schedule=[
            items_work_schedule.get_item_by_id(dates.working_schedule.get(vac.workGraphics)).to_json()
        ],
        work_hours=[
            items_working_hours.get_item_by_id(dates.work_hours.get(vac.workGraphics)).to_json()
        ],
        employment_form=items_employment_form.get_item_by_id(dates.employment_form.get(vac.employment_type)).to_json(),
        experience=items_experience.get_item_by_id(dates.experience.get(vac.experience)).to_json(),
        address=address.get_item_by_id(dates.address.get(vac.address)),
        manager=managers.get_item_by_id(dates.managers.get(vac.manager)),
        billing_type=items_vacancy_billing_type.get_item_by_id('standard').to_json(),
        professional_roles=[
            items_role.get_item_by_id('27').get_roles_by_id('40').to_json()
        ],
        type=items_types.get_item_by_id('open').to_json(),
        branded_template=items_template.get_item_by_id('makeup:41365').to_json(),
        accept_temporary=dates.type_work.get(vac.type_work) if dates.type_work.get(vac.type_work) else False,
        internship=dates.type_work.get(vac.type_work) if dates.type_work.get(vac.type_work) else False
        # salary=Salary(
        #     currency='KZT',
        #     to=350000,
        #     from_=0,
        #     gross=True
        # )
    )
    logging.info(v.to_json())
    res = await hh.publication_vacation(v.to_json())
    logging.info(f"RES -> {res}")
    token.access_token = hh.basic_token
    token.refresh_token = hh.ref_token
    session.add(token)

    vacancies = Vacancies(
        id=res.get('id'),
        gender=vac.gender,
        age_to=vac.age_to,
        age_from=vac.age_from,
        salary=vac.salary_from
    )
    session.add(vacancies)
    await session.commit()
    return {
        'status_code': 200,
        'id': res.get('id')
    }


@router.post(
    '/v1/recruiting/publication_draft',
    tags=['HeadHunter'],
    summary="Публикация черновика"
)
async def publication_draft(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        vac: ModelVacancies
):
    logging.info(vac.name)
    for k, v in vac:
        logging.info(f"{k}: {v}")
    session: AsyncSession = db_session.get()
    token = await Token.get_token(session)
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )
    items_work_format: ItemDirectories = await hh.get_dictionaries('work_format')
    items_work_schedule: ItemDirectories = await hh.get_dictionaries('work_schedule_by_days')
    items_working_hours: ItemDirectories = await hh.get_dictionaries('working_hours')
    items_vacancy_billing_type: ItemDirectories = await hh.get_dictionaries('vacancy_billing_type')
    items_types: ItemDirectories = await hh.get_dictionaries('vacancy_type')
    items_employment_form: ItemDirectories = await hh.get_dictionaries('employment_form')
    items_experience: ItemDirectories = await hh.get_dictionaries('experience')
    items_role = await hh.get_roles()
    items_template = await hh.get_brand_templates()
    if not vac.type_work:
        vac.type_work = '0'

    address = await hh.get_address()
    managers = await hh.get_managers()
    item_areas: ItemAreas = await hh.get_areas()
    logging.info(vac.toDo.split('*'))
    to_do = [f"<li>{i}</li>\n" if i != "" else "" for i in vac.toDo.split('*')]
    except_candidates = [f"<li>{i}</li>\n" if i != "" else "" for i in vac.exceptCandidates.split('*')]
    offer = [f"<li>{i}</li>\n" if i != "" else "" for i in vac.offer.split('*')]
    v = PublicationVacation(
        name=vac.name,
        description=f'''<strong>Чем предстоит заниматься:</strong>
<ul>
{"".join(to_do)}
</ul>
<strong>Что мы ждем от кандидатов:</strong>
<ul>
{"".join(except_candidates)}
</ul>
<strong>Мы предлагаем:</strong>
<ul>
{"".join(offer)}
</ul>
    ''',
        work_format=[
            items_work_format.get_item_by_id(dates.work_format.get(vac.workFormat)).to_json()
        ],
        area=item_areas.get_item_by_id(dates.cities.get(vac.city)).to_json(),
        working_schedule=[
            items_work_schedule.get_item_by_id(dates.working_schedule.get(vac.workGraphics)).to_json()
        ],
        work_hours=[
            items_working_hours.get_item_by_id(dates.work_hours.get(vac.workGraphics)).to_json()
        ],
        employment_form=items_employment_form.get_item_by_id(dates.employment_form.get(vac.employment_type)).to_json(),
        experience=items_experience.get_item_by_id(dates.experience.get(vac.experience)).to_json(),
        address=address.get_item_by_id(dates.address.get(vac.address)),
        manager=managers.get_item_by_id(dates.managers.get(vac.manager)),
        billing_type=items_vacancy_billing_type.get_item_by_id('standard').to_json(),
        professional_roles=[
            items_role.get_item_by_id('27').get_roles_by_id('40').to_json()
        ],
        type=items_types.get_item_by_id('open').to_json(),
        branded_template=items_template.get_item_by_id('makeup:41365').to_json(),
        accept_temporary=dates.type_work.get(vac.type_work) if dates.type_work.get(vac.type_work) else False,
        internship=dates.type_work.get(vac.type_work) if dates.type_work.get(vac.type_work) else False
        # salary=Salary(
        #     currency='KZT',
        #     to=350000,
        #     from_=0,
        #     gross=True
        # )
    )
    logging.info(v.to_json())
    res = await hh.publication_draft(v.to_json())
    logging.info(f"RES -> {res}")
    token.access_token = hh.basic_token
    token.refresh_token = hh.ref_token
    session.add(token)
    gender = {
        "Женский": "female",
        "Мужской": "male"
    }

    vacancies = Vacancies(
        id=res.get('id'),
        gender=gender.get(vac.gender) if gender.get(vac.gender) else vac.gender,
        age_to=str(vac.age_from) if vac.age_from else None,
        age_from=str(vac.age_to) if vac.age_to else None,
        salary=int(vac.salary_from.split("|")[0]),
        deal_id=vac.deal_id
    )
    session.add(vacancies)
    await session.commit()
    return {
        'status_code': 200,
        'id': res.get('id'),
        'link': f"https://hh.kz/employer/vacancy/create?draftId={res.get('id')}"
    }


@router.post('/v2/recruiting/publication_vacancies',
             tags=['HeadHunter'],
             summary="Публикация вакансий на основе черновика")
async def publication_vacancy2(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        draft: ModelVac2
):
    session: AsyncSession = db_session.get()
    token = await Token.get_token(session)
    vacancies = await Vacancies.get_vacancies_by_id(
        draft_id=draft.draft_id,
        session=session
    )
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )
    result = await hh.publication_vacancies_by_draft(draft_id=draft.draft_id)
    token.access_token = hh.basic_token
    token.refresh_token = hh.ref_token
    session.add(token)

    vacancies.vacancies_id = str(result.get('vacancy_ids')[0])
    vacancies.is_active = True
    session.add(vacancies)

    await session.commit()
    return {
        'status_code': 200,
        'id': vacancies.vacancies_id,
        'link': f"https://hh.kz/vacancy/{vacancies.vacancies_id}",
        'message': 'Вакансия опубликовано'
    }


@router.put('/v2/recruiting/archive/vacancy',
            tags=['HeadHunter'],
            summary="Архивация вакансий")
async def archive_vacancy(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        draft: ModelVac2
):
    session: AsyncSession = db_session.get()
    token = await Token.get_token(session)
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )
    vacancies = await Vacancies.get_by_id(
        vacancy_id=draft.vacancies_id,
        session=session
    )
    vacancies.is_active = False
    session.add(vacancies)

    await session.commit()
    await hh.archive_vacancies(draft.vacancies_id)
    return {
        'status_code': 200,
        "message": 'Вакансия архива'
    }


@router.post('/v2/recruiting/archive/publication_vacancies',
             tags=['HeadHunter'],
             summary="Публикация архивный вакансий")
async def publication_archive_vacancy(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        draft: ModelVac2
):
    session: AsyncSession = db_session.get()
    logging.info(draft)
    token = await Token.get_token(session)
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )
    result = await hh.get_draft_vacancies(draft.draft_id)
    result['previous_id'] = draft.previous_id
    result['area'] = {'id': result.get("areas")[0].get('id')}
    result['meta'] = None
    result2 = await hh.publication_vacation(result)
    logging.info(result2)
    vacancies = await Vacancies.get_vacancies_by_id(
        draft_id=draft.draft_id,
        session=session
    )
    token.access_token = hh.basic_token
    token.refresh_token = hh.ref_token
    session.add(token)

    vacancies.vacancies_id = str(result2.get('id'))
    vacancies.is_active = True
    session.add(vacancies)

    await session.commit()
    return {
        'status_code': 200,
        'id': vacancies.vacancies_id,
        'link': f"https://hh.kz/vacancy/{vacancies.vacancies_id}",
        'message': 'Вакансия опубликовано'
    }


@router.post("/v1/recruiting/discard")
async def discard_by_employer_process(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        discard: ModelDiscard
):
    session: AsyncSession = db_session.get()
    token = await Token.get_token(session)
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )

    vacations = VacationItems()
    vacations_all = VacationItems()
    vacations.data = []
    vacations_all.data = []
    p = 0
    # while vacations.found > len(vacations.data):
    #     vacations = await hh.get_response(
    #         vacancy_id=discard.vacancy_id,
    #         vacations=vacations,
    #         page=p
    #     )
    #     p += 1
    # r = None
    # for d in vacations.data:
    #     if d.id == discard.resume_id:
    #         r = d.resume
    text = '''{name} здравствуйте!

Большое спасибо за интерес к вакансии! К сожалению, сейчас мы не готовы пригласить вас на следующий этап.
Ценим ваше внимание и будем рады получать ваши отклики на другие позиции.

Дюсембаева Акмарал Бакытовна
    '''
    result = await hh.negotiation_message(
        nid=discard.resume_id,
        message=text.format(name=discard.name)
    )
    #print(result)
    result = await hh.actions_negotiation(
        states_id="discard_by_employer",
        nid=discard.resume_id
    )
    return {
        'status_code': 201,
        'message': 'Кандидат отклонен'
    }
    #print(result)


@router.post('/v1/qa/vacation/publication_vacancy', deprecated=True)
async def take_vacation(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(validate_security)],
        vac: ModelVacancies
):
    session: AsyncSession = db_session.get()
    return {
        'status_code': 200,
        'id': vac
    }
