from abc import ABC, abstractmethod


class BaseRepository(ABC):
    @abstractmethod
    def init_db(self) -> None:
        """Initialize the database. Should be called once at the start of the application"""
        pass
