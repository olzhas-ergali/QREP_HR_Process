import typing
from dataclasses import dataclass
from pathlib import Path

import environs
from sqlalchemy import make_url, URL


@dataclass
class RedisSettings:
    redis_host: str = 'localhost'


@dataclass
class DatabaseSettings:
    db_user: str = 'user'
    db_pass: str = 'pass'
    db_host: str = 'host'
    db_name: str = 'db_name'

    @property
    def url(self):
        url = URL(
            drivername="postgresql+asyncpg",
            username=self.db_user,
            password=self.db_pass,
            host=self.db_host,
            database=self.db_name,
            query={},
            port=5432
        )
        return make_url(url)


@dataclass
class LoggingSettings:
    """Configure the logging engine."""

    # The time field can be formatted using more human-friendly tokens.
    # These constitute a subset of the one used by the Pendulum library
    # https://pendulum.eustace.io/docs/#tokens
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <5} | {message}"

    # The .log filename
    file: str = "backend"

    # The .log file Rotation
    rotation: str = "1MB"

    # The type of compression
    compression: str = "zip"


@dataclass
class TgbotSettings:
    bot_token: typing.Optional[str] = None


@dataclass
class MiscSettings:
    login: str
    pwd: str


@dataclass
class Bitrix:
    token: str
    user_id: str


@dataclass
class Settings:
    # Project file system
    root_dir: Path
    src_dir: Path

    # Infrastructure settings
    database: DatabaseSettings
    redis: RedisSettings
    misc: MiscSettings
    tg_bot: TgbotSettings
    bitrix: Bitrix

    # Application configuration
    logging: LoggingSettings = LoggingSettings()
    debug_status: bool = True


ROOT_PATH = Path(__file__).parent.parent
env = environs.Env()
env.read_env('.env')

settings = Settings(
    database=DatabaseSettings(
        db_host=env.str('DB_HOST'),
        db_pass=env.str('DB_PASS'),
        db_name=env.str('DB_NAME'),
        db_user=env.str('DB_USER')
    ),
    redis=RedisSettings(
        redis_host=env.str('REDIS_HOST')
    ),
    root_dir=ROOT_PATH,
    src_dir=ROOT_PATH,
    misc=MiscSettings(
        login=env.str('LOGIN_AUTH'),
        pwd=env.str('PASSWORD_AUTH')
    ),
    tg_bot=TgbotSettings(
        bot_token=env.str('BOT_TOKEN')
    ),
    bitrix=Bitrix(
        token=env.str('BITRIX_TOKEN'),
        user_id=env.str('BITRIX_USER_ID')
    )
)

CLIENT_ID = env.str('CLIENT_ID')
CLIENT_SECRET = env.str('CLIENT_SECRET')
EMPLOYER_ID = env.str('EMPLOYER_ID')
MANAGER_ID = env.str('MANAGER_ID')
PERSONAL_MANAGER_ID = env.str('PERSONAL_MANAGER_ID')
USER_ID = env.str('USER_ID')
REFRESH_TOKEN = env.str('REFRESH_TOKEN')
BITRIX_TOKEN = env.str('BITRIX_TOKEN')
BITRIX_USER_ID = env.str('BITRIX_USER_ID')

DOMAIN_URL = "https://ellection.online"
