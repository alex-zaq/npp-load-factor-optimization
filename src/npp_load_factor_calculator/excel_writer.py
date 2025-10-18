
from pathlib import Path

import pandas as pd

from src.npp_load_factor_calculator.utilites import get_file_name_with_auto_number


class Excel_writer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper


    def _write_scenario_options(self, writer, sheet_name):
        scenario_options = self.block_grouper.custom_es.scenario
        scenario_options_df = pd.DataFrame.from_dict(scenario_options, orient='index')
        scenario_options_df.to_excel(writer, sheet_name=sheet_name, index=True)

    def _write_results_data(self, writer, sheet_name):
        
        res = self.block_grouper.get_electricity_profile_all_blocks() 
        
        
        # мощность
        # выработка
        # увеличение риска
        # уменьшение риска
        # накопленный риск
        # затраты на ремонты
        # суммарные затраты
        
        
        res.to_excel(writer, sheet_name=sheet_name)

    
    def write(self, folder):
        scen = self.block_grouper.custom_es.scenario
        folder = Path(folder)
        if not folder.exists():
            folder.mkdir(parents=True)
        excel_file = get_file_name_with_auto_number(folder, scen, "xlsx")
        path = folder / excel_file
        writer = pd.ExcelWriter(path, engine="openpyxl")
        self._write_results_data(writer, sheet_name = "results")
        self._write_scenario_options(writer, sheet_name = "scenario_options")
        writer._save()
        print("{}  ({})".format("excel файл создан", excel_file))
    
    