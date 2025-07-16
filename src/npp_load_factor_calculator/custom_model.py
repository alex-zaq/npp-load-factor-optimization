

from src.npp_load_factor_calculator.block_db import Block_db
from src.npp_load_factor_calculator.generic_models import (
    Generic_bus,
    Generic_sink,
    Generic_source,
    Generic_storage,
)


class Custom_model:

    def __init__(self, scenario, oemof_es):
        self.scenario = scenario
        self.oemof_es = oemof_es
        self.bus_factory = Generic_bus(oemof_es)
        self.source_factory = Generic_source(oemof_es)
        self.sink_factory = Generic_sink(oemof_es)
        self.storage_factory = Generic_storage(oemof_es)
        self.block_db = Block_db()
   
    def add_electricity_demand(self):
        self.el_bus = self.bus_factory.create_bus("электроэнергия (bus)")
        self.el_sink = self.sink_factory.create_sink("электроэнергия (sink)", self.el_bus) 
        self.block_db.add_block("потребитель ээ", self.el_sink)
        
        
    def add_bel_npp(self):
                
        bel_npp_block_1 = self.source_factory.create_npp_block(
            label = "БелАЭС (блок 1)",
            nominal_power = 1170,
            output_bus = self.el_bus,
            lcoe = -56.5,
        )
        bel_npp_block_2 = self.source_factory.create_npp_block(
            label = "БелАЭС (блок 2)",
            nominal_power = 1170,
            output_bus = self.el_bus,
            lcoe = -56.5,
        )
        self.block_db.add_block("аэс", bel_npp_block_1)
        self.block_db.add_block("аэс", bel_npp_block_2)

       
    
    def add_new_npp(self):
        new_npp_block_1 = self.source_factory.create_npp_block(
            label="Новая АЭС (блок 1)",
            nominal_power=1170,
            output_bus=self.el_bus,
            lcoe=-56.5,
        )
        self.block_db.add_block("аэс", new_npp_block_1)
            
    
    def add_risk_storage(self):
        risk_bus = self.bus_factory.create_bus("риск (bus)")
        max_risk_level = 99999        
        risk_storage_1 = self.storage_factory.create_storage(
            input_bus=risk_bus,
            output_bus=risk_bus,
            capacity=max_risk_level,
        )
        self.block_db.add_block("риск", risk_storage_1)
    

    def get_constraints(self):
        pass
        
