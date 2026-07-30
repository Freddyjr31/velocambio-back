
from abc import ABC, abstractmethod

class RatesRepositoryInterface(ABC):
    @abstractmethod
    def get_oficial_usd_rates(self):
        pass

    @abstractmethod
    def get_promedio_usd_rates(self):
        pass
    
    @abstractmethod
    def get_eur_rates(self):
        pass
    
    @abstractmethod
    def get_p2p_rates(self):
        pass
    
    def get_all_rates_today(self):
        pass