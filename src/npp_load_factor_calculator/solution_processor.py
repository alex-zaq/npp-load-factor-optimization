

import oemof.solph as solph

from src.npp_load_factor_calculator.custom_model import Custom_model
from src.npp_load_factor_calculator.excel_writer import Excel_writer
from src.npp_load_factor_calculator.logging_options import get_logger
from src.npp_load_factor_calculator.utilites import (
    get_full_filename,
    get_next_number_file_name,
    get_number,
)

logger = get_logger()

class Solution_processor:

    def __init__(self, oemof_model):
        self.oemof_model = oemof_model
        self.calc_mode = False
        self.restore_mode = False
        self.save_results = False
        self.file_name = None
        self.excel_file_name = None
        self.dumps_folder = None
        self.excel_folder = None
    

    def set_dumps_folder(self, dumps_folder):
        self.dumps_folder = dumps_folder

    def set_block_grouper(self, block_grouper):
        self.block_grouper = block_grouper

    # def set_alt_block_grouper(self, block_grouper):
    #     self.alt_block_grouper = block_grouper

    def set_excel_folder(self, folder):
        self.excel_folder = folder

    def set_calc_mode(self, *, save_results):
        self.calc_mode = True
        self.restore_mode = False
        self.save_results = save_results

    def set_restore_mode(self, *, file_number):
        self.file_name = get_full_filename(self.dumps_folder, file_number)
        self.restore_mode = True
        self.calc_mode = False
        
        
    def calculate(self):
        self.oemof_model.init_energy_system()
        self.oemof_model.add_excel_data_to_custom_es()
        self.oemof_model.construct_energy_system(self.group_options)
        self.oemof_model.launch_solver()
        self.custom_es = self.oemof_model.get_custom_es()
        self.oemof_es = self.oemof_model.get_oemof_es()
        self.results = self.oemof_model.get_results()
        self.meta_results = self.oemof_model.get_meta_results()

    def save_solution(self):
        self.oemof_es.results["main"] = self.results
        self.oemof_es.results["meta"] = self.meta_results
        self.oemof_es.results["group_options"] = self.oemof_model.get_group_options()
        file_name = self.get_dumps_file_name_with_auto_number()
        self.oemof_es.dump(dpath=self.dumps_folder, filename=file_name)


    def get_dumps_file_name(self):
        file_name = ""
        return file_name


    def get_dumps_file_name_with_auto_number(self):
        next_number = get_number(get_next_number_file_name(self.dumps_folder))
        file_name = f"{self.get_dumps_file_name()}.oemof"
        res = [next_number, file_name]
        res = "_".join(res)
        return res


    def restore_solution(self):
        self.oemof_es = solph.EnergySystem()
        self.custom_es = Custom_model(self.oemof_es)
        self.oemof_model.set_custom_es(self.custom_es)

        self.oemof_es.restore(dpath=self.dumps_folder, filename=self.file_name)
        self.results = self.oemof_es.results["main"]
        self.meta_results = self.oemof_es.results["meta"]
        self.group_options = self.oemof_es.results["group_options"]
        self.oemof_model.construct_energy_system(self.group_options)

    def write_excel_file(self, excel_file_name=None):
        if excel_file_name is None:
            self.excel_file_name = f"{self.get_dumps_file_name()}.xlsx"
        else:
            self.excel_file_name = excel_file_name

        Excel_writer.set_options(self.excel_folder, self.excel_file_name)
        Excel_writer.set_group_options(self.group_options)
        Excel_writer.set_block_grouper(self.block_grouper)
        # Excel_writer.set_alt_block_grouper(self.alt_block_grouper)
        Excel_writer.write_excel_data()


    def get_message(self):
        if self.calc_mode:
            mess = "выполнение расчета"
        elif self.calc_mode and self.save_results:
            mess = "выполнение расчета с сохранением результата"
        elif self.restore_mode:
            mess = "выполнение восстановления решения"
        return mess

    # def create_block_scheme(self, file, **kwargs):
    #     image_format = kwargs.get("image_format", "png")
    #     txt_fontsize = kwargs.get("txt_fontsize", 12)
    #     txt_width = kwargs.get("txt_width", 40)
    #     gr = ESGraphRenderer(
    #         energy_system=self.oemof_es,
    #         filepath=file,
    #         img_format=image_format,
    #         txt_fontsize=txt_fontsize,
    #         txt_width=txt_width,
    #         legend=False,
    #     )
    #     gr.view()

    def apply(self):
        mess = self.get_message()

        if self.calc_mode:
            logger.info(mess)

            self.calculate()

            if self.save_results:
                self.save_solution()

        elif self.restore_mode:
            logger.info(mess)
            self.restore_solution()

        
        
        
    
    