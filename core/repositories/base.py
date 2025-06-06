from typing import Generic, Type, TypeVar

from sqlalchemy import asc, desc

from app import db

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        db.session.add(instance)
        db.session.commit()
        return instance

    def update(self, object_id: int, **kwargs) -> T | None:
        instance = self.get_by_id(object_id)
        if instance is None:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        db.session.commit()
        return instance

    def get_by_id(self, object_id: int) -> T | None:
        return self.model.query.get(object_id)

    def get_all(self) -> list[T]:
        return self.model.query.all()

    def get_instance_by_key(self, **filters) -> T | None:
        return self.model.query.filter_by(**filters).first()

    def get_list_by_key(
            self,
            order_by: str = None,
            limit: int = None,
            order: str = "asc",
            **filters
    ) -> list[T] | None:
        query = self.model.query.filter_by(**filters)

        if order_by:
            query = query.order_by(asc(order_by) if order.lower() == "asc" else desc(order_by))

        if limit:
            query = query.limit(limit)

        return query.all()
