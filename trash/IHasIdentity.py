from abc import ABC, abstractmethod


class IHASIdentity(ABC):
    @abstractmethod
    def get_ID(self):
        pass

    @abstractmethod
    def get_Name(self):
        pass

    @abstractmethod
    def get_Description(self):
        pass
