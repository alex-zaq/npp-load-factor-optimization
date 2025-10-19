
from pathlib import Path

import pandas as pd

from src.npp_load_factor_calculator.utilites import Converter, get_all_block_repairs_df_by_dict, get_file_name_with_auto_number, get_months_name_by_date_range, get_years_by_date_range


class Excel_writer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper


    def _write_scenario_options(self, writer, sheet_name):
        scenario_options = self.block_grouper.custom_es.scenario
        scenario_options_df = pd.DataFrame.from_dict(scenario_options, orient='index')
        scenario_options_df.to_excel(writer, sheet_name=sheet_name, index=True)

    def _write_results_data(self, writer, sheet_name):
        
        res = pd.DataFrame()
        
        coeff = Converter.convert(1.0, "мвтч", "млн.квтч")
        el_gen_df = self.block_grouper.get_electricity_profile_all_blocks().resample('M').sum()
        el_gen_df = el_gen_df * coeff * 24
        risk_increase_df = self.block_grouper.get_increase_all_blocks_df().resample('M').mean()
        risk_decrease_df = self.block_grouper.get_decrease_all_blocks_df().resample('M').mean()
        cost_all_blocks_df = self.block_grouper.get_cost_profile_all_blocks(cumulative=False).resample('M').sum()
        cost_all_blocks_df = cost_all_blocks_df.cumsum()
        risks_dict = self.block_grouper.get_risks_profile_by_all_blocks_dict()
        risk_data_dict = {k: v["risk_line_col"] for k, v in risks_dict.items()}
        risk_df = pd.DataFrame(risk_data_dict).resample('M').mean()
        repairs_dict = self.block_grouper.get_repairs_profile_by_all_blocks_dict(part = 0)

        repair_df = get_all_block_repairs_df_by_dict(repairs_dict).resample('M').sum()

        res = pd.concat([el_gen_df, risk_df, risk_increase_df, risk_decrease_df, repair_df, cost_all_blocks_df], axis=1)

        year_col = get_years_by_date_range(res.index)
        months_col = get_months_name_by_date_range(res.index)

        res.insert(0, "year", year_col)
        res.insert(1, "month", months_col)
        
        # мощность
        # выработка
        # увеличение риска
        # уменьшение риска
        
        
        res.to_excel(writer, sheet_name=sheet_name, index=False)

    
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
    
    