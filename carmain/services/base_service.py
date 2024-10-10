from carmain.repository.base_repository import BaseRepository


class BaseService:
    def __init__(self, repository: BaseRepository) -> None:
        self._repository = repository

    def get_by_id(self, obj_id: int):
        return self._repository.read_by_id(obj_id)

    def add(self, schema):
        return self._repository.create(schema)

    def patch(self, obj_id: int, schema):
        return self._repository.update(obj_id, schema)

    def remove_by_id(self, obj_id: int):
        return self._repository.delete_by_id(obj_id)
