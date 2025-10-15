
from pathlib import Path

import pandas as pd

from src.npp_load_factor_calculator.utilites import get_file_name_with_auto_number


class Excel_writer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper


    def _write_data(self, writer):
        res = pd.DataFrame()
        res.to_excel(writer, sheet_name="results")

    
    def write_excel(self, folder):
        scen = self.block_grouper.custom_es.scenario
        folder = Path(folder)
        if not folder.exists():
            folder.mkdir(parents=True)
        excel_file = get_file_name_with_auto_number(folder, scen, "xlsx")
        writer = pd.ExcelWriter(excel_file, engine="openpyxl")
        block_grouper = self.block_grouper
        self._write_data(block_grouper, writer, "results")
        writer._save()
        print("{}  ({})".format("excel файл создан", excel_file))
    
    