from abc import ABC, abstractmethod


class IStoragePort(ABC):
    @abstractmethod
    async def upload_file(
        self, file_content: bytes, object_name: str, content_type: str
    ) -> str:
        ...
