from API.lib.bitrix.base import BaseApi, MethodRequest


class Bitrix(BaseApi):

    def __init__(
            self
    ):
        super().__init__()

    async def create(
            self,
            fields: dict,
            json: dict = None
    ):
        url = self.url.format(method='crm.lead.add')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False,
            params=fields,
            json=json
        )

        return result

    async def add_contact(
            self,
            fields: dict
    ) -> dict:
        url = self.url.format(method='crm.contact.add')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False,
            params=fields
        )

        return result

    async def add_item(
            self,
            fields: dict
    ):
        url = self.url.format(method='crm.item.add')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False,
            json=fields
        )

        return result
