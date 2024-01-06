from abc import ABC, abstractmethod


class ITurnBased(ABC):
    @abstractmethod
    def TurnPassed(self):
        pass
