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
 

    def add_specific_status_duration_in_period_new(
        self,
        avail_months_mask,
        start_days_mask,
        min_duration,
        periods_pairs
    ):
        avail_months_mask = avail_months_mask if avail_months_mask is not None else 1
        self.add_startup_cost_by_mask(start_days_mask) if start_days_mask is not None else None
        self.add_min_status_in_period(periods_pairs, min_duration)
        self.add_strict_status_off_by_pattern(avail_months_mask)
        self.update_options({"min_uptime": min_duration, "min": 1})


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
                    
                    
    def add_delayed_startup_by_shutdown(self, wrapper_block, delay):
        self.es.constraints["delayed_startup_by_shutdown"][self] = {"triggered_block": wrapper_block, "delay": delay}
                    
    
    def add_min_status_in_period(self, periods, min_required_time):
        self.es.constraints["min_status_in_period"][self] = {"periods": periods, "min_required_time": min_required_time}
              
                    
    def add_max_startup_by_periods(self, periods, max_startup_count_in_every_period):
        self.es.constraints["max_startup_by_periods"][self] = {"periods": periods, "max_startup_count_in_every_period": max_startup_count_in_every_period}
              
    def add_strict_status_off_by_pattern(self, pattern):
        self.es.constraints["strict_status_off_by_pattern"][self] = pattern
                    
                    
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