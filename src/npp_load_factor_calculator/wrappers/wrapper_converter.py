import itertools

from oemof import solph

from npp_load_factor_calculator.utilites import set_label
from src.npp_load_factor_calculator.generic_models import Generic_bus
from src.npp_load_factor_calculator.wrappers.wrapper_base import Wrapper_base


class Wrapper_converter(Wrapper_base):
    
    def __init__(self, es, label):
        super().__init__(es, label)
        
        
    def _get_pair_after_building(self):
        output_bus = self.options["output_bus"]
        converter = self.build()
        return converter, output_bus
        
    def add_all_input_combinations(self, bus_lst):
        
        bus_combinations = []
        for r in range(1, len(bus_lst) + 1):
            bus_combinations.extend(itertools.combinations(bus_lst, r))

        bus_factory = Generic_bus(self.es)

        control_bus = bus_factory.create_bus(f"{self.label}_control_bus_for_combinations")
        
        for bus_combination in bus_combinations:
            inputs = {}
            for bus in bus_combination:
                inputs[bus] = solph.Flow()

            converter = solph.components.Converter(
                label=set_label(self.label, *bus_combination),
                inputs=inputs,
                outputs={control_bus: solph.Flow()},
            )
            self.es.add(converter)
            
        self.options["bus_for_input_combinations"] = control_bus 

    def add_sink_for_output_bus(self):
        bus = self.options["output_bus"]
        sink = solph.Sink(label=f"{self.label}_sink_for_output_bus", inputs={bus: solph.Flow()})
        self.es.add(sink)

    def _get_inputs(self):
        inputs = {self.options["input_bus"]: solph.Flow()}
        if "bus_for_input_combinations" in self.options:
            inputs = {self.options["bus_for_input_combinations"]: solph.Flow()}
        return inputs
    
    def _get_outputs(self):
        outputs = {self.options["output_bus"]: solph.Flow(
                nominal_value=self.options["nominal_power"],
                min = self.options["min"],
                max = self.options["max"],
                nonconvex=solph.NonConvex(
                   minimum_uptime=self.options.get("minimum_uptime"),
                   startup_costs=self.options.get("startup_costs",0),
                   shutdown_costs=self.options.get("shutdown_costs",0),
                    ),
                )}
        return outputs

            
    def build(self):
        if self.block:
            return self.block
        
        inputs = self._get_inputs()
        outputs = self._get_outputs()


        self.block = solph.components.Converter(
            label=self.label,
            inputs=inputs,
            outputs=outputs,
        )

        self.es.add(self.block)
        self._set_info_to_block()
        self._apply_constraints()

        return self.block
        
        
        