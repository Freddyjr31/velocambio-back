
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
    
    @abstractmethod
    def get_all_rates_today(self):
        pass

    @abstractmethod
    def get_rate_at(self, currency_from_id, rate_type_id, source_type_id, as_of):
        pass

    @abstractmethod
    def get_rate_history(self, currency_from_id, rate_type_id, source_type_id, desde=None, hasta=None, limit=None, offset=None):
        pass

    @abstractmethod
    def count_rate_history(self, currency_from_id, rate_type_id, source_type_id, desde=None, hasta=None):
        pass