from oemof import solph

from src.npp_load_factor_calculator.wrappers.wrapper_base import Wrapper_base


class Wrapper_source(Wrapper_base):
    
    def __init__(self, es, label):
        super().__init__(es, label)
        
    def _get_pair_after_building(self):
        output_bus = self.options["output_bus"]
        source = self.build()
        return source, output_bus
    
    def add_keyword_to_flow(self, keyword):
        if self._output_flow:
            setattr(self._output_flow, keyword, True)
        else:
            self.keywords[keyword] = True
        
        
    def get_main_flow(self):
        if hasattr(self, "_output_flow"):
            return self._output_flow
        else:
            return None

    def _get_output_flow(self):
        output_flow = solph.Flow(
                nominal_value=self.options["nominal_power"],
                min = self.options["min"],
                max = self.options["max"],
                nonconvex=solph.NonConvex(
                    minimum_uptime=self.options.get("minimum_uptime", 0),
                    startup_costs=self.options.get("startup_cost_profile",0),
                    shutdown_costs=self.options.get("shutdown_cost_profile",0),
                    ),
                custom_attributes=self.keywords
                )
        return output_flow
       
    def build(self):
        if self.block:
            return self.block
        
        self._output_flow = self._get_output_flow()
        
        self.block = solph.components.Source(
            label=self.label,
            outputs={self.options["output_bus"]: self._output_flow},
        )
        
        self.block.outputs_pair = [(self.block, self.options["output_bus"])]

        self.es.add(self.block)
        self._set_info_to_block()
        self._apply_constraints()

        return self.block