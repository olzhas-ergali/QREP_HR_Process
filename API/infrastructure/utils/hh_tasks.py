import logging
import typing
import base64
import re
import os

from API.infrastructure.database.recruiting import Vacancies, Resumes, Token
from API.lib.bitrix.add import Bitrix
from API.lib.hh.HeadHunter import HeadHunter
from API.lib.schemas.vacation import VacationItems, Vacation
from sqlalchemy.ext.asyncio import AsyncSession
import datetime


async def auto_analysis(
        db_session
):
    session: AsyncSession = db_session()
    vac = await Vacancies.get_vacancies(session)
    token = await Token.get_token(session)
    hh = HeadHunter(
        basic_token=token.access_token,
        refresh_token=token.refresh_token
    )
    valid_resumes = []
    for v in vac:
        vacancies = VacationItems()
        vacancies.data = []
        p = 0
        while vacancies.found > len(vacancies.data):
            #print(vacations.found, len(vacations.data))
            genders = {
                "female": v.gender,
                "male": v.gender
            }

            vacancies = await hh.get_response(
                vacancy_id=int(v.vacancies_id),
                vacations=vacancies,
                page=p,
                age_from=str(v.age_from) if v.age_from else None,
                age_to=str(v.age_to) if v.age_to else None,
                gender=genders.get(v.gender, None),
                #salary_from=0,
                #salary_to=int(v.salary)
            )
            token.access_token = hh.basic_token
            token.refresh_token = hh.ref_token
            session.add(token)
            await session.commit()
            p += 1
        if vacancies.data:
            datas: typing.Sequence[Vacation] = vacancies.data
            for i in datas:
                resume = await Resumes.get_by_resume_id(
                    session=session,
                    resume_id=i.id,
                    vacancies_id=v.id
                )
                if not resume:
                    if i.resume.salary and i.resume.salary.amount > int(v.salary):
                        continue
                    r = Resumes(
                        resume_id=i.id,
                        vacancies_id=v.id
                    )

                    session.add(r)
                    await session.commit()
                    valid_resumes.append(i.id)
                    logging.info(
                        f"\nID: {i.id}\n"
                        f"AGE: {i.resume.age}\n"
                        f"SALARY: {i.resume.salary}\n"
                    )
                    c, path = await hh.get_resumes(i.resume.id)
                    contact_email = ""
                    try:
                        if c.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', c.email):
                            contact_email = c.email.rstrip(".")
                    except:
                        pass
                    try:
                        contact_fields = {
                            "fields[NAME]": i.resume.first_name if i.resume.first_name else "",
                            "fields[SECOND_NAME]": i.resume.middle_name if i.resume.middle_name else "",
                            "fields[LAST_NAME]": i.resume.last_name if i.resume.last_name else "",
                            "fields[BIRTHDATE]": c.birth_date if c.birth_date else "",
                            "fields[PHONE][0][VALUE]": c.phone if c.phone else "",
                            "fields[PHONE][0][VALUE_TYPE]": "WORKMOBILE",
                            "fields[EMAIL][0][VALUE]": contact_email,
                            "fields[EMAIL][0][VALUE_TYPE]": "HOME",
                            "fields[WEB][0][VALUE]": f"https://hh.ru/resume/{i.resume.id}",
                            "fields[WEB][0][VALUE_TYPE]": "HOME",
                            # "fields[UF_CRM_1731574397751]": files_encoded
                            # "fields[COMMENTS]": "Testttttt",
                            #    "fields[SOURCE_ID][VALUE]": "334"
                        }
                        bitrix = Bitrix()
                        result = await bitrix.add_contact(fields=contact_fields)
                        #print(result)
                        with open(path, "rb") as file:
                            encoded_content = base64.b64encode(file.read()).decode("utf-8")
                        fields_item = {
                            "entityTypeId": 180,
                            "fields": {
                                'categoryId': 35,
                                'ufCrm_13_1727330539': ["resume.pdf", encoded_content],
                                'ufCrm_13_1745338188669': v.deal_id,
                                'ufCrm_13_1751297343872': str(r.resume_id),
                                'ufCrm_13_1751298240': str(v.vacancies_id),
                                'opportunity': i.resume.salary.amount if i.resume.salary else 0,
                                'contactId': result.get('result')
                            }
                            # 'contactId':
                        }
                        #result.get('id')
                        result = await bitrix.add_item(fields=fields_item)
                        print(result)
                        os.remove(path)
                    except Exception as ex:
                        print(ex)
            for i in datas:
                if i.id not in valid_resumes:
                    text = '''{name} здравствуйте!

Большое спасибо за интерес к вакансии! К сожалению, сейчас мы не готовы пригласить вас на следующий этап.
Ценим ваше внимание и будем рады получать ваши отклики на другие позиции.

Дюсембаева Акмарал Бакытовна
                        '''
                    result = await hh.negotiation_message(
                        nid=i.id,
                        message=text.format(name=i.resume.first_name)
                    )
                    # print(result)
                    result = await hh.actions_negotiation(
                        states_id="discard_by_employer",
                        nid=i.id
                    )

    await session.close()
