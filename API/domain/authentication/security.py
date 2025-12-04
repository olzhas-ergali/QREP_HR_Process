import typing

from fastapi import Header, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette import status

from API.config import settings

security = HTTPBasic()


def validate_security(
        credentials: typing.Annotated[HTTPBasicCredentials, Depends(security)],
):
    if credentials.username == settings.misc.login and credentials.password == settings.misc.pwd:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='Forbidden'
    )
