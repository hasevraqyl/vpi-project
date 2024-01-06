from abc import ABC, abstractmethod


class IResourceHolder(ABC):
    @abstractmethod
    def get_Resources():
        pass
