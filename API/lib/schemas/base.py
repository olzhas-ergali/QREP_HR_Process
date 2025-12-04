import dataclass_factory
from dataclass_factory import Schema


class BaseModel:
    def dict(self):
        factory = dataclass_factory.Factory(default_schema=Schema(omit_default=True))
        return factory.dump(self, self.__class__.__name__)

    def load(self, data: dict):
        factory = dataclass_factory.Factory(default_schema=Schema(omit_default=True))
        query = factory.load(data, self.__class__)
        return query
