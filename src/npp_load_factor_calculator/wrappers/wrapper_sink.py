from collections import deque

from oemof import solph

from src.npp_load_factor_calculator.generic_models import Generic_bus
from src.npp_load_factor_calculator.wrappers.wrapper_base import Wrapper_base


class Wrapper_sink(Wrapper_base):
    
    def __init__(self, es, label):
        super().__init__(es, label)
 
        
    def get_pair_after_building(self):
        input_bus = self.options["input_bus"]
        sink = self.build()
        return input_bus, sink
          
    def add_keyword_to_flow(self, keyword):
        if self._input_flow:
            setattr(self._input_flow, keyword, True)
        else:
            self.keywords[keyword] = True
             
    def get_main_flow(self):
        if hasattr(self, "_input_flow"):
            return self._input_flow
        else:
            return None
        
               
    def build(self):
        if self.block:
            return self.block
        
        self._input_flow = self._get_nonconvex_flow()

        input_bus = self.options["input_bus"]
        
        self.block = solph.components.Sink(
            label=self.label,
            inputs={input_bus: self._input_flow},
       ) 
        
        self.block.inputs_pair = [(input_bus, self.block)]
        
        self.es.add(self.block)
        self._set_info_to_block()
        self._apply_constraints()

        return self.block
        
        
        