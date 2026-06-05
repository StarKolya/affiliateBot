import functools
import logging
import time
from typing import Generic, List, Optional, Type, TypeVar

from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)

_log = logging.getLogger(__name__)


def log_query(func):
    """Decorator that logs the execution time of async repository methods."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = await func(*args, **kwargs)
        _log.debug(
            "%s.%s completed in %.3fs",
            args[0].__class__.__name__,
            func.__name__,
            time.monotonic() - start,
        )
        return result
    return wrapper


class BaseRepository(Generic[ModelType]):

    model: Type[ModelType]

    @log_query
    async def get_by_id(self, pk: int) -> Optional[ModelType]:
        return await self.model.get_or_none(id=pk)

    @log_query
    async def get_all(self) -> List[ModelType]:
        return await self.model.all()

    async def create(self, **kwargs) -> ModelType:
        return await self.model.create(**kwargs)

    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        instance.update_from_dict(kwargs)
        await instance.save()
        return instance

    async def delete(self, instance: ModelType) -> None:
        await instance.delete()
