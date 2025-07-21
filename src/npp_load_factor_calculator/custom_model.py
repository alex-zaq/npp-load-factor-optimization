

from src.npp_load_factor_calculator.block_db import Block_db
from src.npp_load_factor_calculator.generic_models import (
    Generic_bus,
    Generic_sink,
    Generic_source,
)
from src.npp_load_factor_calculator.utilites import (
    get_risk_events_profile,
    get_valid_profile_by_months,
    plot_array,
)


class Custom_model:

    def __init__(self, scenario, oemof_es):
        self.scenario = scenario
        self.oemof_es = oemof_es
        self.bus_factory = Generic_bus(oemof_es)
        self.sink_factory = Generic_sink(oemof_es)
        self.source_factory = Generic_source(oemof_es)
        self.source_factory.set_years(scenario["start_year"], scenario["end_year"])
        self.block_db = Block_db()
   
    def add_electricity_demand(self):
        self.el_bus = self.bus_factory.create_bus("электроэнергия (bus)")
        self.el_sink = self.sink_factory.create_sink("электроэнергия (sink)", self.el_bus) 
        self.block_db.add_block("потребитель ээ", self.el_sink)
        
        
    def add_bel_npp(self):
                               
                               
        status_1 = self.scenario["bel_npp"]["block_1"]["status"]
        status_2 = self.scenario["bel_npp"]["block_2"]["status"]
        start_year, end_year = self.scenario["start_year"], self.scenario["end_year"]
        # allow_months_1 = self.scenario["bel_npp"]["block_1"]["repair_options"]["allow_months"]  
        # allow_months_2 = self.scenario["bel_npp"]["block_2"]["repair_options"]["allow_months"] 
        npp_block_1_events = self.scenario["bel_npp"]["block_1"]["events"]
        npp_block_2_events = self.scenario["bel_npp"]["block_2"]["events"]
        upper_bound_risk_1 = self.scenario["bel_npp"]["block_1"]["upper_bound_risk"]
        upper_bound_risk_2 = self.scenario["bel_npp"]["block_2"]["upper_bound_risk"]
        risk_per_hour_1 = self.scenario["bel_npp"]["block_1"]["risk_per_hour"]
        risk_per_hour_2 = self.scenario["bel_npp"]["block_2"]["risk_per_hour"]
        # min_pow_lst_1 = max_pow_lst_1 = get_valid_profile_by_months(start_year, end_year, allow_months_1)        
        # min_pow_lst_2 = max_pow_lst_2 = get_valid_profile_by_months(start_year, end_year, allow_months_2)        
        fix_risk_lst_1 = get_risk_events_profile(start_year, end_year, npp_block_1_events)
        fix_risk_lst_2 = get_risk_events_profile(start_year, end_year, npp_block_2_events)
        repair_options_1 = self.scenario["bel_npp"]["block_1"]["repair_cost_duration"]
        repair_options_2 = self.scenario["bel_npp"]["block_2"]["repair_cost_duration"]
           
        # plot_array(min_pow_lst_1)
        # plot_array(min_pow_lst_2)
        # plot_array(fix_risk_lst_1)
        # plot_array(fix_risk_lst_2)
           
        if status_1:
            bel_npp_block_1 = self.source_factory.create_npp_block(
                label = "БелАЭС (блок 1)",
                nominal_power = 1170,
                output_bus = self.el_bus,
                var_cost = -56.5,
                risk_mode = False,
                risk_per_hour = risk_per_hour_1,
                max_risk_level = upper_bound_risk_1,
                fix_risk_lst = fix_risk_lst_1,
                # min_pow_lst = min_pow_lst_1,
                # max_pow_lst = max_pow_lst_1,
                repair_options = repair_options_1
            )
            self.block_db.add_block("аэс", bel_npp_block_1)
        
        if status_2:
            bel_npp_block_2 = self.source_factory.create_npp_block(
                label = "БелАЭС (блок 2)",
                nominal_power = 1170,
                output_bus = self.el_bus,
                var_cost = -56.5,
                risk_mode = False,
                risk_per_hour = risk_per_hour_2,
                max_risk_level = upper_bound_risk_2,
                fix_risk_lst = fix_risk_lst_2,
                # min_pow_lst = min_pow_lst_2,
                # max_pow_lst = max_pow_lst_2,
                repair_options = repair_options_2
            )
            self.block_db.add_block("аэс", bel_npp_block_2)

       
    
    def add_new_npp(self):
        
        status_1 = self.scenario["new_npp"]["block_1"]["status"]
        start_year, end_year = self.scenario["start_year"], self.scenario["end_year"]
        # allow_months_1 = self.scenario["new_npp"]["block_1"]["repair_options"]["allow_months"]     
        npp_block_1_events = self.scenario["new_npp"]["block_1"]["events"]
        upper_bound_risk_1 = self.scenario["new_npp"]["block_1"]["upper_bound_risk"]
        risk_per_hour_1 = self.scenario["new_npp"]["block_1"]["risk_per_hour"]
        # min_pow_lst_1 = max_pow_lst_1 = get_valid_profile_by_months(start_year, end_year, allow_months_1)        
        fix_risk_lst_1 = get_risk_events_profile(start_year, end_year, npp_block_1_events)
        repair_options_1 = self.scenario["new_npp"]["block_1"]["repair_cost_duration"]
                
        # plot_array(min_pow_lst_1)
        # plot_array(fix_risk_lst_1)
                
        if status_1:
            new_npp_block_1 = self.source_factory.create_npp_block(
                label = "Новая АЭС (блок 1)",
                nominal_power = 1170,
                output_bus = self.el_bus,
                var_cost = -56.5,
                risk_mode = False,
                risk_per_hour = risk_per_hour_1,
                max_risk_level = upper_bound_risk_1,
                fix_risk_lst = fix_risk_lst_1,
                # min_pow_lst = min_pow_lst_1,
                # max_pow_lst = max_pow_lst_1,
                repair_options = repair_options_1
            )
            self.block_db.add_block("аэс", new_npp_block_1)
        

    def get_constraints(self):
        npp_constraints = self.source_factory.get_npp_constraints()
        return npp_constraints
        
