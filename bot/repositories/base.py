from typing import Generic, List, Optional, Type, TypeVar

from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)


class BaseRepository(Generic[ModelType]):
    """Thin async wrapper around Tortoise ORM queries."""

    model: Type[ModelType]

    async def get_by_id(self, pk: int) -> Optional[ModelType]:
        return await self.model.get_or_none(id=pk)

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
