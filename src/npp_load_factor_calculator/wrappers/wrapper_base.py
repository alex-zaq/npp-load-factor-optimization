from collections import defaultdict

import numpy as np

from src.npp_load_factor_calculator.wrappers.wrapper_source import Wrapper_source
from src.npp_load_factor_calculator.generic_models import Generic_bus
from oemof import solph


class Wrapper_base:
    
    def __init__(self, es, label):
        self.es = es
        self.init_constraints_for_es()
        self.label = label
        self.options = {}   
        self.info = {}
        self.keywords = {}
        self.constraints = defaultdict(list)
        self.block = None
        
        
    def update_options(self, options):
        self.options.update(options)
        

    def init_constraints_for_es(self):
        if not hasattr(self.es, "constraints"):
            self.es.constraints = defaultdict(list)
         
            
    def create_pair_keywords_single_status(self, wrapper_block):
        keyword = f"{self.label}_{wrapper_block.label}_single_status"
        self.keywords[keyword] = True
        wrapper_block.keywords[keyword] = True
        self.constraints["single_status"].append(keyword)

        
    def get_pair_after_building(self):
        pass
    
    def add_min_inactive_status(self, start, finish, length):

        bus_factory = Generic_bus(self.es)
        sink_bus = bus_factory.create_bus(f"{self.label}_sink_bus")
    
        sink = solph.components.sink(
            name=f"{self.label}_min_inactive_sink",
            inputs={sink_bus: solph.Flow(nominal_value=1, fix = 0)},
        )
        self.es.add(sink)
        
        storage_in_bus = bus_factory.create_bus(f"{self.label}_storage_in_bus")
        storage = solph.components.GenericStorage(
            label=f"{self.label}_min_inactive_storage",
            nominal_storage_capacity=0,
            inputs={storage_in_bus: solph.Flow(nominal_value=1, fix = 0)},
            outputs={sink_bus: solph.Flow(nominal_value=1, fix = 0)},
            balanced=False
        )
        self.es.add(storage)
        
        
        wrapper_control_source = Wrapper_source(self.es, f"{self.label}_min_inactive_control_source")
        wrapper_control_source.update_options({
            "nominal_power": 1,
            "output_bus": storage_in_bus,
            "nonconvex": True,
            "min": 0,
            })
        # равные статусы после построения 
        wrapper_control_source.create_pair_equal_status(self)
        wrapper_control_source.build()


    def add_max_up_time(self, max_uptime):
               
        
        bus_factory = Generic_bus(self.es)
    
        storage_in_bus = bus_factory.create_bus(f"{self.label}_max_up_time_storage_in_bus")
        storage_out_bus = bus_factory.create_bus(f"{self.label}_max_up_time_storage_out_bus")

        block_power = self.options["nominal_power"]

        
        wrapper_source_builder = Wrapper_source(self.es, f"{self.label}_max_up_time_control_source")
        wrapper_source_builder.update_options({
            "nominal_power": 1e8,
            "output_bus": storage_in_bus,
            "nonconvex": True,
            "min": 0,
            })
        wrapper_source_builder.create_pair_equal_status(self)
        wrapper_source_builder.build()
        
        
        storage = solph.components.GenericStorage(
            label=f"{self.label}_max_up_time_storage",
            nominal_storage_capacity=max_uptime * block_power ,
            inputs={storage_in_bus: solph.Flow()},
            outputs={storage_out_bus: solph.Flow()},
            balanced=False
        )
        self.es.add(storage)
        
        charger_builder = Wrapper_source(self.es, f"{self.label}_max_up_time_control_source")
        charger_builder.update_options({
            "nominal_power": 1e8,
            "output_bus": storage_in_bus,
            "nonconvex": True,
            "min": 0,
            })
        charger_builder.create_pair_keywords_single_status(wrapper_source_builder)
        charger_builder.build()
        self.options["max_uptime_input_bus"] = storage_out_bus
        
        
    
    def add_status_on_intervals(self, free_profile):
        # совместимость c startupcost
        free_profile = np.array(free_profile)
        no_free_profile = np.where(free_profile == 0, 1e8, free_profile)
        self.options["free_status_profile"] = {"free": free_profile, "no_free": no_free_profile}


    def create_pair_equal_status(self, wrapper_block):
        self.constraints["equal_status"].append(wrapper_block)


    def _apply_constraints(self):
        constraint_groups_names = list(self.constraints.keys())
        if not constraint_groups_names:
            return
        a = "single_status" in constraint_groups_names
        b = "equal_status" in constraint_groups_names
        assert not a and b
        
        for constraint_group_name in constraint_groups_names:
            match constraint_group_name:
                case "single_status":
                    self.es.constraints["single_status"].extend(self.constraints[constraint_group_name])
                case "equal_status":
                    another_wrapper_block = self.constraints[constraint_group_name]
                    pair_1 = self.get_pair_after_building()
                    pair_2 = another_wrapper_block.get_pair_after_building()
                    self.es.constraints["equal_status"].append((pair_1, pair_2))


    def set_info(self, name, value):
        self.info[name] = value
        
    def get_info(self, name):
        return self.info[name]
    
    def build(self):
        pass
    
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