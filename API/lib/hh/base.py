import json
import logging
import typing
import os

import aiohttp
import requests
from oauthlib.oauth2 import WebApplicationClient
from API import config


class MethodRequest:
    post = 'POST'
    put = 'PUT'
    get = 'GET'
    delete = 'DELETE'
    patch = 'PATCH'


def to_format(
        data
) -> str:
    if data is None:
        return ""
    return data


class BaseApi:

    def __init__(
            self,
            basic_token: str = None,
            user_id: str = config.USER_ID,
            client_id: str = config.CLIENT_ID,
            client_secret: str = config.CLIENT_SECRET,
            employer_id: str = config.EMPLOYER_ID,
            manager_id: str = config.MANAGER_ID,
            ref_token: str = None
    ):
        self.client = WebApplicationClient(client_id)
        self.production_url = "https://api.hh.kz/{method}"
        self.token_url = 'https://hh.ru/oauth/token'
        self.user_id = user_id
        self.ref_token = ref_token
        self.basic_token = basic_token
        # self.client_secret =

    def get_token(self):
        return self.basic_token

    def get_refresh_token(
            self
    ):
        response = requests.post(self.token_url, params=self.client.prepare_refresh_body(
            refresh_token=self.ref_token
        ))
        return response.json()

    @property
    def url(self) -> str:
        return self.production_url

    async def request_session(
            self,
            method: MethodRequest.get,
            url: str,
            is_file: bool = False,
            json_status: bool = True,
            answer_log: bool = False,
            **kwargs

    ):
        result = self.get_refresh_token()
        if result.get('access_token'):
            self.basic_token = result.get('access_token')
            self.ref_token = result.get('refresh_token')
        # print(
        #     f"METHOD {method}\nURL - {url}\n"
        #     f"dict - > {kwargs}")
        logging.info(
            f"METHOD {method}\nURL - {url}\n"
            f"dict - > {kwargs}"
        )

        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': 'Bearer {}'.format(self.basic_token)
            }
            response = await session.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            # print(await response.text())
            if response.status == 400 and self.user_id:
                # print(response.status)
                res = await response.read()
                logging.info(res)
                # print(json.loads(res))
                return

            try:
                if is_file:
                    with open('resume.pdf', 'wb') as file:
                        file.write(await response.read())
                    return {
                        "status_code": '200',
                        'file_path': os.path.abspath('resume.pdf')
                    }
                if json_status:
                    data = await response.read()
                    data = json.loads(data)
                    return data
            except Exception as e:
                logging.exception(e)
            finally:
                if answer_log:
                    logging.info(
                        f'ANSWER: {await response.text()}'
                    )

            return response
