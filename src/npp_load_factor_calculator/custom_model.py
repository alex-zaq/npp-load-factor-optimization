

from src.npp_load_factor_calculator.generic_models import (
    Generic_sink,
    Generic_source,
    Generic_storage,
)


class Custom_model:

    def __init__(self, scenario, oemof_es):
        self.scenario = scenario
        self.oemof_es = oemof_es
        self.source_factory = Generic_source(oemof_es)
        self.sink_factory = Generic_sink(oemof_es)
        self.storage_factory = Generic_storage(oemof_es)
   
    
    def add_bel_npp(self):
        pass
    
    def add_new_npp(self):
        pass
    
    def add_electricity_demand(self):
        pass
        
        
        # self.el_bus = self.sink_factory.create_sink("el_bus", "el_bus")
        
    
    def add_risk_storage(self):
        pass

    def get_constraints(self):
        pass
        
