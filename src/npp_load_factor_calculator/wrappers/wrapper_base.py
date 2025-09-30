from collections import defaultdict

import numpy as np
from oemof import solph

from src.npp_load_factor_calculator.generic_models import Generic_bus


class Wrapper_base:
    
    def __init__(self, es, label):
        self.es = es
        self.init_constraints_for_es()
        self.label = label
        self.options = {}   
        self.alt_options = {}
        self.info = {}
        self.keywords = {}
        self.constraints = defaultdict(list)
        self.block = None
        
    def add_keyword_to_flow(self):
        pass
    
    def get_main_flow(self):
        pass
    
    def get_pair_after_building(self):
        pass
    
    def build(self):
        pass
    
    def create_wrapper_source_builder(self, es, label):
        pass
    
    def create_wrapper_converter_builder(self, es, label):
        pass
                   
    def update_options(self, options):
        if self.block or self.get_main_flow():
            raise Exception("Wrapper is already built")        
        self.options.update(options)
        
    def init_constraints_for_es(self):
        if not hasattr(self.es, "constraints"):
            self.es.constraints = defaultdict(list)


    def add_keyword_no_equal_status(self, keyword):
        self.constraints["no_equal_status"].append(keyword)

    def create_pair_no_equal_status(self, wrapper_block):
        keyword = f"{self.label}_{wrapper_block.label}_no_equal_status"
        self.add_keyword_to_flow(keyword)
        wrapper_block.add_keyword_to_flow(keyword)
        self.constraints["no_equal_status"].append(keyword)

    def create_pair_equal_status(self, wrapper_block):
        self.constraints["equal_status"].append(wrapper_block)
              
    def add_specific_status_duration_in_period(self, outage_duration, max_profile_mask, mode, max_profile = None, startup_cost_mask = 0):

        if mode not in ("active", "non_active"):
            raise ValueError("mode must be active or non_active")

        charger_power = 1
        storage_capacity = charger_power * outage_duration
        fix_profile = np.array(max_profile_mask) * storage_capacity


        bus_factory = Generic_bus(self.es)
        sink_bus = bus_factory.create_bus(f"{self.label}_sink_bus")
    
        sink = solph.components.Sink(
            label=f"{self.label}_min_inactive_sink",
            inputs={sink_bus: solph.Flow(nominal_value=1, fix = fix_profile)},
        )
        sink.inputs_pair = [(sink_bus, sink)]
        self.es.add(sink)
        
        max_profile = max_profile if max_profile is not None else 1
        storage_in_bus = bus_factory.create_bus(f"{self.label}_storage_in_bus")
        storage = solph.components.GenericStorage(
            label=f"{self.label}_min_inactive_storage",
            initial_storage_level=0,
            nominal_storage_capacity=storage_capacity,
            inputs={storage_in_bus: solph.Flow(
                nominal_value=1e10,
                max=max_profile,
                min=0,
                nonconvex=solph.NonConvex(),
                )},
            outputs={sink_bus: solph.Flow()},
            balanced=False
        )
        storage.inputs_pair = [(storage_in_bus, storage)]
        storage.outputs_pair = [(sink_bus, storage)]
        self.es.add(storage)
        
        
        
        wrapper_charger_builder = self.create_wrapper_source_builder(self.es, f"{self.label}_min_inactive_control_source")
        wrapper_charger_builder.update_options({
            "nominal_power": charger_power,
            "output_bus": storage_in_bus,
            "min_uptime": outage_duration,
            "min": 1,
            })
        
        if startup_cost_mask is not None:
            wrapper_charger_builder.add_startup_cost_by_mask(startup_cost_mask)
        
        if mode == "active":
            wrapper_charger_builder.create_pair_equal_status(self)
        elif mode == "non_active":
            wrapper_charger_builder.create_pair_no_equal_status(self)

        wrapper_charger_builder.build()

    def add_max_up_time(self, max_uptime):
        
        bus_factory = Generic_bus(self.es)
    
        storage_in_bus = bus_factory.create_bus(f"{self.label}_max_up_time_storage_in_bus")
        storage_out_bus = bus_factory.create_bus(f"{self.label}_max_up_time_storage_out_bus")

        block_power = self.options["nominal_power"]

        
        storage_control = solph.components.GenericStorage(
            label=f"{self.label}_max_up_time_storage",
            initial_storage_level=0,
            nominal_storage_capacity=max_uptime * block_power,
            inputs={storage_in_bus: solph.Flow()},
            outputs={storage_out_bus: solph.Flow()},
            balanced=False
        )
        storage_control.inputs_pair = [(storage_in_bus, storage_control)]
        storage_control.outputs_pair = [(storage_control, storage_out_bus)]
        self.es.add(storage_control)
        
        charger_builder = self.create_wrapper_source_builder(self.es, f"{self.label}_max_up_time_control_source")
        charger_builder.update_options({
            "nominal_power": 1e8,
            "output_bus": storage_in_bus,
            "min": 0,
            })
        
        self.update_options({"second_input_bus": storage_out_bus})
        charger_builder.create_pair_no_equal_status(self)
        charger_builder.build()


            
    def add_startup_cost_by_mask(self, mask):
        mask = np.array(mask)
        startup_cost = self.options.get("startup_cost", 0)
        self.options["startup_cost"] = np.where(mask == 1, startup_cost, 1e15)


    def _apply_constraints(self):
        constraint_groups_names = list(self.constraints.keys())
        if not constraint_groups_names:
            return

        
        for constraint_group_name in constraint_groups_names:
            match constraint_group_name:
                case "no_equal_status":
                    # возможные повторы
                    self.es.constraints["no_equal_status"].extend(self.constraints[constraint_group_name])
                case "equal_status":
                    another_wrapper_block = self.constraints[constraint_group_name][0]
                    pair_1 = self.get_pair_after_building()
                    pair_2 = another_wrapper_block.get_pair_after_building()
                    self.es.constraints["equal_status"].append((pair_1, pair_2))


    def _get_nonconvex_flow(self):
        if "fix" in self.options:
            self.options["min"] = None
            self.options["max"] = None
        flow = solph.Flow(
                nominal_value=self.options["nominal_power"],
                min = self.options.get("min"),
                max = self.options.get("max"),
                fix = self.options.get("fix"),
                variable_costs=self.options.get("var_cost", 0),
                positive_gradient_limit=self.options.get("positive_gradient_limit", None),
                negative_gradient_limit=self.options.get("negative_gradient_limit", None),
                nonconvex=solph.NonConvex(
                    initial_status=self.options.get("initial_status", 0),
                    maximum_startups=self.options.get("max_startup", None),
                    minimum_uptime=self.options.get("min_uptime", 0),
                    minimum_downtime=self.options.get("min_downtime", 0),
                    startup_costs=self.options.get("startup_cost", None),
                    shutdown_costs=self.options.get("shutdown_cost", None),
                    ),
                custom_attributes=self.keywords
                )
        return flow


    def set_info(self, name, value):
        self.info[name] = value
        
    def get_info(self, name):
        return self.info[name]
    
    def _set_info_to_block(self):
        if self.info:
            for key, value in self.info.items():
                setattr(self.block, key, value)
                
    def __eq__(self, value):
        if isinstance(value, Wrapper_base):
            return self.label == value.label
        return False
        
    def __hash__(self):
        return hash(self.label)