# Third party imports.
from ninja import Schema


class MemorySchema(Schema):
    namespace: list
    key: str
    value: dict


class NotFoundSchema(Schema):
    message: str
