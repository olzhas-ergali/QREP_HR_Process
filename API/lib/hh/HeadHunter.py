import logging
import typing
from typing import Type

from API.lib.hh.base import BaseApi, MethodRequest
from API.lib.schemas.directories import Directories, ItemDirectories
from API.lib.schemas.resume import (Areas, Experience, Education, Gender, Level, Primary,
                                    ItemAreas, Resume, Salary, Contacts)
from API.lib.schemas.manager import Manager, ItemsManager, Phones
from API.lib.schemas.address import Address, ItemsAddress
from API.lib.schemas.templates import Templates, ItemsTemplate
from API.lib.schemas.categories import Categories, ItemsCategories
from API.lib.schemas.roles import Roles
from API.lib.schemas.vacation import Vacation, VacationItems
from API.lib.schemas.states import States, CollectionStates


class HeadHunter(BaseApi):

    def __init__(
            self,
            basic_token: str,
            refresh_token: str
    ):
        super().__init__(basic_token=basic_token, ref_token=refresh_token)

    async def get_vacancies(
            self
    ):
        url = self.url.format(method='employers/4742030/vacancies/active')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,

        )
        return result

    async def get_response(
            self,
            vacancy_id: str | int,
            page: int = 0,
            vacations: VacationItems = None,
            age_to: str = None,
            age_from: str = None,
            gender: str = None,
            salary_from: int = None,
            salary_to: int = None,
            currency: str = 'KZT'
    ):
        
        query_parameters = {
            'vacancy_id': vacancy_id,
            'page': page,
            'currency': currency
        }
        if age_to:
            query_parameters['age_to'] = age_to
        if age_from:
            query_parameters['age_from'] = age_from
        if gender:
            query_parameters['gender'] = gender
        if salary_from:
            query_parameters['salary_from'] = salary_from
        if salary_to:
            query_parameters['salary_to'] = salary_to
        url = self.url.format(method='negotiations/response')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            params=query_parameters
        )
        if not vacations:
            vacations = VacationItems()
        # print(result)
        vacations.found = result.get('found')
        if result.get('items'):
            for i in result.get('items'):
                salary = None
                gender = None
                if i.get('resume').get('salary'):
                    salary = Salary()
                    salary.currency = i.get('resume').get('salary').get('currency', None)
                    salary.amount = i.get('resume').get('salary').get('amount', None)
                if i.get('resume').get('gender'):
                    gender = Gender(
                        id=i.get('resume').get('gender').get('id', None),
                        name=i.get('resume').get('gender').get('name', None)
                    )
                resume = Resume(
                    id=i.get('resume').get('id'),
                    last_name=i.get('resume').get('last_name'),
                    first_name=i.get('resume').get('first_name'),
                    middle_name=i.get('resume').get('middle_name'),
                    title=i.get('resume').get('title'),
                    area=Areas(
                        id=i.get('resume').get('area').get('id'),
                        name=i.get('resume').get('area').get('name')
                    ),
                    age=i.get('resume').get('age'),
                    gender=gender,
                    salary=salary,
                    total_experience=i.get('resume').get('total_experience')
                )
                vacation = Vacation(
                    id=i.get('id'),
                    state=States(
                        id=i.get('state').get('id'),
                        name=i.get('state').get('name')
                    ),
                    created_at=i.get('created_at')
                )
                education = Education()
                if i.get('resume') and i.get('resume').get('education') and i.get('resume').get('education').get('level'):
                    education.level = Level(
                        id=i.get('resume').get('education').get('level').get('id'),
                        name=i.get('resume').get('education').get('level').get('name')
                    )
                if i.get('resume'):
                    if i.get('resume').get('primary'):
                        education.primary = []
                        for j in i.get('resume').get('primary'):
                            education.primary.append(
                                Primary(
                                    id=j.get('id'),
                                    name=j.get('name')
                                )
                            )
                    if i.get('resume').get('experience'):
                        resume.experience = []
                        for j in i.get('resume').get('experience'):
                            e = Experience(
                                start=j.get('start'),
                                end=j.get('end'),
                                company_id=j.get('company_id'),
                                industry=j.get('industry'),
                                company=j.get('company'),
                                company_url=j.get('company_url'),
                                position=j.get('position')
                            )
                            if j.get('area'):
                                e.area = Areas(
                                    id=j.get('area').get('id'),
                                    name=j.get('area').get('name')
                                )
                            resume.experience.append(e)
                vacation.resume = resume
                vacations.append_item(vacation)
        return vacations

    async def get_negotiation(
        self,
        negotiation_id: int | str
    ):
        url = self.url.format(method=f'negotiations/{negotiation_id}')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
        )
        return result

    async def actions_negotiation(
            self,
            states_id: str,
            nid: str
    ):
        url = self.url.format(method=f'negotiations/{states_id}/{nid}')
        result = await self.request_session(
            method=MethodRequest.put,
            url=url,
            json_status=False,
            answer_log=False,
            # headers=headers
        )
        return result

    async def negotiation_message(
            self,
            nid: str,
            message: str
    ):
        url = self.url.format(method=f'negotiations/{nid}/messages')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=False,
            answer_log=False,
            data={
                "message": message
            }
            # headers=headers
        )
        return result

    async def publication_vacation(
            self,
            query_body: dict
    ):
        
        url = self.url.format(method='vacancies')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False,
            params={
                'ignore_duplicates': True
            },
            json=query_body
        )
        #print(result)
        return result

    async def get_draft_vacancies(
            self,
            draft_id: str | int
    ):
        url = self.url.format(method=f'vacancies/drafts/{draft_id}')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            # # headers=headers,
        )
        return result

    async def get_dictionaries(
            self,
            parameter_name: str
    ) -> typing.Optional[ItemDirectories]:
        
        url = self.url.format(method='dictionaries')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
        )
        logging.info(result)
        items = ItemDirectories()
        for i in result.get(parameter_name):
            d = Directories()
            d.id = i.get('id')
            d.name = i.get('name')
            items.append_item(d)

        return items

    async def get_areas(
            self,
            location_id: str = '40'
    ) -> typing.Optional[ItemAreas]:
        
        url = self.url.format(method='areas')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
        )
        items = ItemAreas()
        areas = []
        for i in result:
            if i.get('id') == location_id:
                areas = i.get('areas')
                break

        for i in areas:
            a = Areas(
                id=i.get('id'),
                parent_id=i.get('parent_id'),
                name=i.get('name')
            )
            items.append_item(a)

        return items

    async def get_negotiation_collection(
            self,
            vacancy_id: str | int = None
    ) -> typing.Optional[CollectionStates]:
        
        query_parameters = {
            'vacancy_id': vacancy_id,
        }
        url = self.url.format(method='negotiations')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
            params=query_parameters
        )
        states = CollectionStates()
        for k, v in result.items():
            for i in v:
                s = States(
                    id=i.get('id'),
                    name=i.get('name')
                )
                states.append_item(s)
        return states

    async def get_managers(
            self
    ) -> typing.Optional[ItemsManager]:
        
        url = self.url.format(method='employers/4742030/managers')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
        )
        items = ItemsManager()
        for i in result.get('items'):
            a = Manager(
                id=i.get('id'),
                first_name=i.get('first_name'),
                last_name=i.get('last_name'),
                position=i.get('position'),
                email=i.get('email')
            )
            if i.get('area'):
                a.area = Areas(
                    id=i.get('area').get('id'),
                    name=i.get('area').get('name')
                )
            if i.get('phone'):
                a.phone = Phones(
                    city=i.get('phone').get('id'),
                    comment=i.get('phone').get('comment'),
                    formatted=i.get('phone').get('formatted'),
                    country=i.get('phone').get('country'),
                    number=i.get('phone').get('number')
                )

            items.append_item(a)

        return items

    async def get_address(
            self
    ) -> typing.Optional[ItemsAddress]:
        
        url = self.url.format(method='employers/4742030/addresses')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
        )
        items = ItemsAddress()
        for i in result.get('items'):
            a = Address(
                id=i.get('id'),
                city=i.get('city'),
                street=i.get('city'),
                building=i.get('building'),
                raw=i.get('raw'),
            )

            items.append_item(a)

        return items

    async def get_roles(
            self
    ):
        
        url = self.url.format(method='professional_roles')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
        )
        items = ItemsCategories()
        for i in result.get('categories'):
            c = Categories(
                id=i.get('id'),
                name=i.get('name')
            )
            c.roles = []
            for j in i.get('roles'):
                r = Roles(
                    id=j.get('id'),
                    name=j.get('name')
                )
                if c:
                    c.roles.append(r)
            items.append_item(c)
        return items

    async def get_brand_templates(
            self
    ):
        
        url = self.url.format(method='employers/4742030/vacancy_branded_templates')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            
        )

        items = ItemsTemplate()
        for i in result.get('items'):
            t = Templates(
                id=i.get('id'),
                name=i.get('name')
            )

            items.append_item(t)
        return items

    async def publication_draft(
            self,
            query_body: dict
    ):
        
        url = self.url.format(method='vacancies/drafts')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False,
            
            json=query_body
        )
        #print(result)
        return result

    async def publication_vacancies_by_draft(
            self,
            draft_id: str
    ):
        url = self.url.format(method=f'vacancies/drafts/{draft_id}/publish')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False
        )
        return result

    async def get_resumes(
            self,
            resume_id: str
    ) -> typing.Tuple[Contacts, str] | typing.Tuple[None, None]:
        url = self.url.format(method=f'resumes/{resume_id}')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            json_status=True,
            answer_log=False,
            # # headers=headers,
        )
        contact = Contacts()
        if result.get('birth_date'):
            contact.birth_date = result.get('birth_date')
        if result.get('contact'):
            if len(result.get('contact')) < 2:
                result.get('contact').append({'value': None})
            #print(result.get('contact'))
            if result.get('contact')[1].get('value'):
                contact.email = result.get('contact')[1].get('value')
            if result.get('contact')[0].get('value'):
                contact.phone = result.get('contact')[0].get('value').get('country') + result.get('contact')[0].get('value').get('city') + result.get('contact')[0].get('value').get('number')

        response = await self.request_session(
            method=MethodRequest.get,
            url=result.get('actions').get("download").get('pdf').get('url'),
            json_status=True,
            answer_log=False,
            is_file=True
            # # headers=headers,
        )
        #print(result.get('actions').get("download").get('pdf'))
        if response.get('file_path', None):
            return contact, response.get('file_path')
        return None, None

    async def archive_vacancies(
            self,
            vacancy_id: str | int
    ):
        url = self.url.format(method=f'employers/4742030/vacancies/archived/{vacancy_id}')
        result = await self.request_session(
            method=MethodRequest.put,
            url=url,
            json_status=False,
            answer_log=False
        )
        return result
        #"https://api.hh.ru/employers/{employer_id}/vacancies/archived/{vacancy_id}"