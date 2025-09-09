

from src.npp_load_factor_calculator.block_db import Block_db
from src.npp_load_factor_calculator.generic_models import (
    Generic_bus,
    Generic_sink,
    Generic_source,
)
from src.npp_load_factor_calculator.utilites import (
    get_main_risk_by_inner_types,
    get_repair_mode_for_block,
    get_risk_events_profile,
    get_profile_for_all_repair_types,
    plot_array,
    # get_valid_profile_by_months,
    # plot_array,
)


class Custom_model:

    def __init__(self, scenario, oemof_es):
        self.scenario = scenario
        self.oemof_es = oemof_es
        self.bus_factory = Generic_bus(oemof_es)
        self.sink_factory = Generic_sink(oemof_es)
        self.source_factory = Generic_source(oemof_es)
        self.source_factory.set_years(scenario["years"])
        self.block_db = Block_db()
        

    def add_electricity_demand(self):
        self.el_bus = self.bus_factory.create_bus("электроэнергия (bus)")
        self.el_sink = self.sink_factory.create_sink("электроэнергия (sink)", self.el_bus) 
        self.block_db.add_block("потребитель ээ", self.el_sink)
        
        
    def add_bel_npp(self):
                               
        start_year, end_year = self.scenario["years"][0], self.scenario["years"][-1]

        status_1 = self.scenario["bel_npp_block_1"]["status"]
        status_2 = self.scenario["bel_npp_block_2"]["status"]
        
        if status_1:
            power_1 = self.scenario["bel_npp_block_1"]["nominal_power"]
            var_cost_1 = self.scenario["bel_npp_block_1"]["var_cost"]
            npp_block_1_events = self.scenario["bel_npp_block_1"]["events"]
            upper_bound_risk_1 = self.scenario["bel_npp_block_1"]["upper_bound_risk"]
            default_risk_options_1 = self.scenario["bel_npp_block_1"]["default_risk_options"]
            repair_options_1 = self.scenario["bel_npp_block_1"]["repair_options"]
            repair_mode_block_1 = get_repair_mode_for_block(self.scenario["bel_npp_block_1"])
            min_up_time_1 = self.scenario["bel_npp_block_1"]["min_up_time"]
            risk_mode_1 = repair_mode_block_1 or bool(default_risk_options_1)
            min_down_time_1 = self.scenario["bel_npp_block_1"]["min_down_time"]
            allow_no_cost_mode_1 = self.scenario["bel_npp_block_1"]["allow_no_cost_mode"]
            main_risk_all_types_1 = get_profile_for_all_repair_types(start_year, end_year + 1, npp_block_1_events)

        if status_2:
            power_2 = self.scenario["bel_npp_block_2"]["nominal_power"]
            var_cost_2 = self.scenario["bel_npp_block_2"]["var_cost"]
            npp_block_2_events = self.scenario["bel_npp_block_2"]["events"]
            upper_bound_risk_2 = self.scenario["bel_npp_block_2"]["upper_bound_risk"]
            default_risk_options_2 = self.scenario["bel_npp_block_2"]["default_risk_options"]
            min_up_time_2 = self.scenario["bel_npp_block_2"]["min_up_time"]
            min_down_time_2 = self.scenario["bel_npp_block_2"]["min_down_time"]
            repair_options_2 = self.scenario["bel_npp_block_2"]["repair_options"]
            repair_mode_block_2 = get_repair_mode_for_block(self.scenario["bel_npp_block_2"])
            risk_mode_2 = repair_mode_block_2 or bool(default_risk_options_2)
            allow_no_cost_mode_2 = self.scenario["bel_npp_block_2"]["allow_no_cost_mode"]
            main_risk_all_types_2 = get_profile_for_all_repair_types(start_year, end_year + 1, npp_block_2_events)
           
           
        if status_1:
            bel_npp_block_1 = self.source_factory.create_npp_block(
                label="БелАЭС (блок 1)",
                nominal_power=power_1,
                output_bus=self.el_bus,
                var_cost=var_cost_1,
                risk_mode=risk_mode_1,
                repair_mode=repair_mode_block_1,
                default_risk_options=default_risk_options_1,
                allow_free_cover_peak_mode=allow_no_cost_mode_1,
                min_up_time=min_up_time_1,
                min_down_time=min_down_time_1,
                max_risk_level=upper_bound_risk_1,
                main_risk_all_types=main_risk_all_types_1,
                repair_options=repair_options_1,
            )
            self.block_db.add_block("аэс", bel_npp_block_1)
        
        if status_2:
            bel_npp_block_2 = self.source_factory.create_npp_block(
                label = "БелАЭС (блок 2)",
                nominal_power = power_2,
                output_bus = self.el_bus,
                var_cost = var_cost_2,
                risk_mode = risk_mode_2,
                repair_mode = repair_mode_block_2,
                default_risk_options = default_risk_options_2,
                allow_free_cover_peak_mode = allow_no_cost_mode_2,
                min_up_time = min_up_time_2,
                min_down_time = min_down_time_2,
                max_risk_level = upper_bound_risk_2,
                main_risk_all_types = main_risk_all_types_2,
                repair_options = repair_options_2
            )
            self.block_db.add_block("аэс", bel_npp_block_2)

       
    
    def add_new_npp(self):
        
        status_1 = self.scenario["new_npp_block_1"]["status"]
        
        if status_1:
            power_1 = self.scenario["new_npp_block_1"]["nominal_power"]
            var_cost_1 = self.scenario["new_npp_block_1"]["var_cost"]
            start_year, end_year = self.scenario["years"][0], self.scenario["years"][-1]
            npp_block_1_events = self.scenario["new_npp_block_1"]["events"]
            upper_bound_risk_1 = self.scenario["new_npp_block_1"]["upper_bound_risk"]
            default_risk_options_1 = self.scenario["new_npp_block_1"]["default_risk_options"]
            main_risk_all_types_1 = get_profile_for_all_repair_types(start_year, end_year + 1, npp_block_1_events)
            repair_options_1 = self.scenario["new_npp_block_1"]["repair_options"]
            repair_mode_block_1 = get_repair_mode_for_block(self.scenario["new_npp_block_1"])
            risk_mode_1 = repair_mode_block_1 or bool(default_risk_options_1)  
            min_up_time_1 = self.scenario["new_npp_block_1"]["min_up_time"]
            min_down_time_1 = self.scenario["new_npp_block_1"]["min_down_time"]
            allow_no_cost_mode_1 = self.scenario["new_npp_block_1"]["allow_no_cost_mode"]    
                
        if status_1:
            new_npp_block_1 = self.source_factory.create_npp_block(
                label="Новая АЭС (блок 1)",
                nominal_power=power_1,
                output_bus=self.el_bus,
                var_cost=var_cost_1,
                risk_mode=risk_mode_1,
                repair_mode=repair_mode_block_1,
                default_risk_options=default_risk_options_1,
                allow_free_cover_peak_mode=allow_no_cost_mode_1,
                min_up_time=min_up_time_1,
                min_down_time=min_down_time_1,
                max_risk_level=upper_bound_risk_1,
                main_risk_all_types=main_risk_all_types_1,
                repair_options=repair_options_1,
            )
            self.block_db.add_block("аэс", new_npp_block_1)
        

    def get_constraints(self):
        npp_constraints = self.source_factory.get_constraints()
        return npp_constraints
        
