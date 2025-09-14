from oemof import solph

from src.npp_load_factor_calculator.wrappers.wrapper_base import Wrapper_base


class Wrapper_source(Wrapper_base):
    
    def __init__(self, es, label):
        super().__init__(es, label)
        self.keywords_outputs = {}
        
    def _get_pair_after_building(self):
        output_bus = self.options["output_bus"]
        source = self.build()
        return source, output_bus

    def _get_outputs(self):
        outputs = {self.options["output_bus"]: solph.Flow(
                nominal_value=self.options["nominal_power"],
                min = self.options["min"],
                max = self.options["max"],
                nonconvex=solph.NonConvex(
                    minimum_uptime=self.options.get("minimum_uptime"),
                    ),
                )}
        return outputs
       
    def build(self):
        if self.block:
            return self.block
        
        outputs = self._get_outputs()
        
        self.block = solph.components.Source(
            label=self.label,
            outputs=outputs,
        )

        self.es.add(self.block)
        self._set_info_to_block()
        self._apply_constraints()

        return self.block