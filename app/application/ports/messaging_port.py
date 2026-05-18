from abc import ABC, abstractmethod
from uuid import UUID


class IMessagingPort(ABC):
    @abstractmethod
    async def publish_analysis(self, analysis_id: UUID, file_url: str) -> None:
        ...
