from datetime import datetime

import oemof.solph as solph
import pandas as pd

from src.npp_load_factor_calculator.constraint_processor import Constraint_processor
from src.npp_load_factor_calculator.custom_model import Custom_model
from src.npp_load_factor_calculator.utilites import check_sequential_years


class Oemof_model:
    
    def __init__(self, scenario, solver_settings):
        self.scenario = scenario
        self.solver_settings = solver_settings
        self.oemof_es = None
            
    def init_oemof_model(self, custom_scenario = None):
        self.scenario = custom_scenario or self.scenario
        start_year = self.scenario["years"][0]
        end_year = self.scenario["years"][-1]

        # first_time_step = datetime(start_year, 1, 1, 0, 0, 0)
        # t_delta = datetime(end_year + 1, 1, 1, 0, 0, 0) - first_time_step

        first_time_step = datetime(start_year, 1, 1)
        t_delta = datetime(end_year + 1, 1, 1) - first_time_step

        periods_count = self._get_periods_count(t_delta, self.scenario["freq"])
        periods_count += 1

        date_timeindex = pd.date_range(first_time_step, periods=periods_count, freq=self.scenario["freq"])
        self.oemof_es = solph.EnergySystem(timeindex=date_timeindex, infer_last_interval=True)
        self.oemof_es.custom_timeindex = date_timeindex

       
    def _get_periods_count(self, t_delta, freq):
        if freq == "D":
            return t_delta.days
        elif freq == "H":
            return t_delta.days * 24

    
    def init_custom_model(self, custom_scenario=None, custom_oemof_es = None):
        self.scenario = custom_scenario or self.scenario
        self.oemof_es = custom_oemof_es or self.oemof_es
        self.custom_es = Custom_model(scenario = self.scenario, oemof_es = self.oemof_es)
        self.custom_es.add_electricity_demand()
        self.custom_es.add_bel_npp()
        self.custom_es.add_new_npp()
    
    
    def add_constraints(self, constraints_processor):
        constraints_processor.apply_equal_status()
        constraints_processor.apply_no_equal_status_equal_1()
        constraints_processor.apply_no_equal_status_lower_0()
        constraints_processor.apply_no_equal_lower_1_status()
        constraints_processor.apply_strict_order()
        constraints_processor.add_group_equal_1()


    def launch_solver(self):
        model = solph.Model(self.oemof_es)
        constraints = self.oemof_es.constraints
        self.add_constraints(Constraint_processor(model, constraints))
        print("модель сформирована")
        self.solver = self.solver_settings["solver"]
        self.solver_verbose = self.solver_settings["solver_verbose"]
        self.mip_gap = self.solver_settings["mip_gap"]
        start_time = datetime.now()
        model.solve(
            solver=self.solver,
            cmdline_options={"mipgap": self.mip_gap},
            solve_kwargs={"tee": self.solver_verbose},
        )
        elapsed_solver_time = (datetime.now() - start_time).total_seconds()
        print(
            "работа " + self.solver + " завершена",
            str(elapsed_solver_time) + " cек.",
            sep=" ",
        )
        self.results = solph.processing.results(model)
        self.meta_results = solph.processing.meta_results(model)
        print("результаты извлечены")
    
    
    def calculate(self):
        self.init_oemof_model()
        self.init_custom_model()
        self.launch_solver()
        
        
    def set_custom_es(self, custom_es):
        self.custom_es = custom_es
        
        
    def get_custom_es(self):
        return self.custom_es


    def get_oemof_es(self):
        return self.oemof_es

    
    def get_scenario(self):
        return self.scenario

    
    def get_results(self):
        return self.results

    
    def get_meta_results(self):
        return self.meta_results

    