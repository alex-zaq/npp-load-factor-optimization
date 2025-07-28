from datetime import datetime

import oemof.solph as solph
import pandas as pd

from src.npp_load_factor_calculator.constraint_processor import Constraint_processor
from src.npp_load_factor_calculator.custom_model import Custom_model


class Oemof_model:
    
    def __init__(self, scenario, solver_settings):
        self.scenario = scenario
        self.start_year = scenario["start_year"]
        self.end_year = scenario["end_year"]
        self.solver = solver_settings["solver"]
        self.solver_verbose = solver_settings["solver_verbose"]
        self.mip_gap = solver_settings["mip_gap"]
        self.oemof_es = None
            
    def _init_oemof_model(self):
        
        t_delta = datetime(self.end_year, 1, 1, 0, 0, 0) - datetime(self.start_year, 1, 1, 0, 0, 0)
        first_time_step = datetime(self.start_year, 1, 1, 0, 0, 0)
        periods_count = t_delta.days * 24
        date_time_index = pd.date_range(first_time_step, periods=periods_count, freq="h")
        self.oemof_es = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
       
    
    def _init_custom_model(self):
        self.custom_es = Custom_model(scenario = self.scenario, oemof_es = self.oemof_es)
        self.custom_es.add_electricity_demand()
        self.custom_es.add_bel_npp()
        self.custom_es.add_new_npp()
    
    
    def _add_constraints(self, constraints_processor):
        constraints_processor.get_block_parallel_status_limit()
        constraints_processor.apply_block_parallel_status_limit()



    def _launch_solver(self):
        model = solph.Model(self.oemof_es)
        constraints = self.custom_es.get_constraints()
        self._add_constraints(Constraint_processor(model, constraints))
        # hours_count = len(model.timeincrement)
        
        
        
        print("модель сформирована")
        start_time = datetime.now()
        model.solve(
            solver=self.solver,
            cmdline_options={"mipgap": self.mipgap},
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
        self._init_oemof_model()
        self._init_custom_model()
        self._launch_solver()
        
    def get_custom_es(self):
        return self.custom_es

    def get_oemof_es(self):
        return self.oemof_es