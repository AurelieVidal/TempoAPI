from typing import Generic, TypeVar

from core.repositories.base import BaseRepository

T = TypeVar("T")


class BaseService(Generic[T]):
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository

    def create(self, **kwargs) -> T:
        return self.repository.create(**kwargs)

    def update(self, object_id: int, **kwargs) -> T | None:
        return self.repository.update(object_id, **kwargs)

    def get_by_id(self, object_id: int) -> T | None:
        return self.repository.get_by_id(object_id)

    def get_all(self) -> list[T]:
        return self.repository.get_all()

    def get_instance_by_key(self, **filters) -> T | None:
        return self.repository.get_instance_by_key(**filters)

    def get_list_by_key(
            self,
            order_by: str = None,
            limit: int = None,
            order: str = "asc",
            **filters
    ) -> list[T] | None:
        return self.repository.get_list_by_key(order_by, limit, order, **filters)
