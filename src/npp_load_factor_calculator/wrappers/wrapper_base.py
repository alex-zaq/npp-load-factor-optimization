from collections import defaultdict

import numpy as np
from oemof import solph

from src.npp_load_factor_calculator.generic_models import Generic_bus
from src.npp_load_factor_calculator.utilites import plot_array


class Wrapper_base:
    
    def __init__(self, es, label):
        self.es = es
        self.init_constraints_for_es()
        self.add_block_build_lst()
        self.label = label
        self.options = {}   
        self.info = {}
        self.keywords = {}
        self.block = None
        self.built = False
        
        
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
            self.es.constraints = defaultdict(lambda: defaultdict(list))
                            
 
    def add_block_build_lst(self):
        if not hasattr(self.es, "block_build_lst"):
            self.es.block_build_lst = []
        self.es.block_build_lst.append(self)
 
 
    def add_specific_status_duration_in_period(
        self,
        mode,
        avail_months_mask,
        start_days_mask,
        mask,
        coeff,
        min_duration,
        max_duration = None,
        ):
        
        # plot_array(avail_months_mask)
        # plot_array(start_days_mask)
        # plot_array(mask)
        

        if mode not in ("active", "non_active"):
            raise ValueError("mode must be active or non_active")

        charger_power = 1
        storage_capacity = charger_power * min_duration
        
        if max_duration is not None:
            storage_capacity = charger_power * max_duration
            
        fix_profile = np.array(mask) * charger_power * min_duration


        bus_factory = Generic_bus(self.es)
        sink_bus = bus_factory.create_bus(f"{self.label}_sink_bus")
    
        sink = solph.components.Sink(
            label=f"{self.label}_min_inactive_sink",
            inputs={sink_bus: solph.Flow(nominal_value=1, fix = fix_profile)},
        )
        sink.inputs_pair = [(sink_bus, sink)]
        self.es.add(sink)
        
        
        # print(np.sum(avail_months_mask))
        avail_months_mask = avail_months_mask if avail_months_mask is not None else 1
        storage_in_bus = bus_factory.create_bus(f"{self.label}_storage_in_bus")
        storage = solph.components.GenericStorage(
            label=f"{self.label}_min_inactive_storage",
            initial_storage_level=0,
            nominal_storage_capacity=storage_capacity * coeff,
            inputs={storage_in_bus: solph.Flow(
                nominal_value=1e10,
                # max=1,
                max=avail_months_mask,
                min=0,
                # bad
                nonconvex=solph.NonConvex(),
                )},
            outputs={sink_bus: solph.Flow()},
            balanced=False
        )
        storage.inputs_pair = [(storage_in_bus, storage)]
        storage.outputs_pair = [(storage, sink_bus)]
        self.set_info("specific_status_duration_storage", storage)
        self.es.add(storage)
        
        
        
        wrapper_charger_builder = self.create_wrapper_source_builder(self.es, f"{self.label}_min_inactive_control_source")
        wrapper_charger_builder.update_options({
            "nominal_power": charger_power,
            "output_bus": storage_in_bus,
            "min_uptime": min_duration,
            "min": 1,
            })
        
        if start_days_mask is not None:
            wrapper_charger_builder.add_startup_cost_by_mask(start_days_mask)
        
        if mode == "active":
            self.create_pair_equal_status(wrapper_charger_builder)
        elif mode == "non_active":
            self.create_pair_no_equal_status_lower_0(wrapper_charger_builder)



    def add_max_uptime_old(self, max_uptime, coeff=1):
        
        bus_factory = Generic_bus(self.es)
    
        storage_in_bus = bus_factory.create_bus(f"{self.label}_max_up_time_storage_in_bus")
        storage_out_bus = bus_factory.create_bus(f"{self.label}_max_up_time_storage_out_bus")

        block_power = self.options["nominal_power"]

        
        storage_control = solph.components.GenericStorage(
            label=f"{self.label}_max_up_time_storage",
            initial_storage_level=0,
            nominal_storage_capacity=max_uptime * block_power * coeff,
            inputs={storage_in_bus: solph.Flow()},
            outputs={storage_out_bus: solph.Flow()},
            balanced=False
        )
        storage_control.inputs_pair = [(storage_in_bus, storage_control)]
        storage_control.outputs_pair = [(storage_control, storage_out_bus)]
        self.es.add(storage_control)
        self.set_info("max_uptime_storage", storage_control)
        
        charger_builder = self.create_wrapper_source_builder(self.es, f"{self.label}_max_up_time_control_source")
        charger_builder.update_options({
            "nominal_power": 1e8,
            "output_bus": storage_in_bus,
            "min": 0,
            })
        
        self.update_options({"second_input_bus": storage_out_bus})
        charger_builder.create_pair_no_equal_status_lower_0(self)


            
    def add_startup_cost_by_mask(self, mask):
        mask = np.array(mask)
        startup_cost = self.options.get("startup_cost", 0)
        self.options["startup_cost"] = np.where(mask == 1, startup_cost, 1e15)


    def add_shutdown_cost_by_mask(self, mask):
        mask = np.array(mask)
        shutdown_cost = self.options.get("shutdown_cost", 0)
        self.options["shutdown_cost"] = np.where(mask == 1, shutdown_cost, 1e15)
        # print(np.sum(self.options["shutdown_cost"]))


    def create_pair_no_equal_status_lower_0(self, wrapper_block):
        self.es.constraints["no_equal_status_lower_0"][self].append(wrapper_block)


    def create_pair_no_equal_status_lower_1(self, wrapper_block):
        self.es.constraints["no_equal_status_lower_1"][self].append(wrapper_block)


    def create_pair_no_equal_status_equal_1(self, wrapper_block):
        self.es.constraints["no_equal_status_equal_1"][self].append(wrapper_block)


    def create_pair_equal_status(self, wrapper_block):
        self.es.constraints["equal_status"][self].append(wrapper_block)

        
    def add_base_block_for(self, wrapper_block):
        self.es.constraints["strict_order"][self].append(wrapper_block)
         
        
    def add_group_equal_1(self, wrapper_block):
        self.es.constraints["group_equal_1"][self].append(wrapper_block)
             
                    
    def add_group_equal_or_greater_1(self, wrapper_block):
        self.es.constraints["group_equal_or_greater_1"][self].append(wrapper_block)
             
             
    def add_max_uptime_new(self, max_uptime):
        self.es.constraints["max_uptime"][self] = max_uptime
                    
                    
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
                    ) if "fix" not in self.options else None,
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