from abc import ABC, abstractmethod

from src.domain.model import AdminsAggregate


class AdminRepositoryAbstract(ABC):
    """Abstract repository that works with AdminsAggregate"""
    @abstractmethod
    def get_list_of_admins(self) -> AdminsAggregate:
        raise NotImplementedError

    @abstractmethod
    def save_admins(self, aggregate: AdminsAggregate) -> None:
        """Save the entire aggregate to persistence"""
        raise NotImplementedError

