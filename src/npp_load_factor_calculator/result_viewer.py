from matplotlib import pyplot as plt

from npp_load_factor_calculator.utilites import get_file_name_with_auto_number


class Result_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        self.scenario = block_grouper.scenario
        self.save_image_flag = False
        self.image_folder = None
        
        
    def save_image_flag(self, flag):
        self.save_image_flag = flag
    
    
    def set_image_folder(self, folder):
        self.image_folder = folder
        
        
    def plot_electricity_generation_profile(self):
        
        el_gen_df = self.block_grouper.get_electricity_profile()
        custom_colors = el_gen_df.custom_colors
        font_size = 8
        max_y = 5000
        
        ax_el_gen_df = el_gen_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=custom_colors,
            linewidth=0.01,
            figsize= (7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_el_gen_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_el_gen_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=6)
        plt.ylabel("Производство электроэнергии, МВт$\cdot$ч", labelpad=5, fontsize=6)
        fig.canvas.manager.set_window_title("Почасовая генерация электроэнергии")
        fig.set_dpi(250)
        
        
        plt.legend(
            loc="upper center",
            # bbox_to_anchor=(0.5, 1),
            fontsize=font_size - 2,
            # ncols=4,
            # ncol=2,
            reverse=True,
            labelspacing=2,
            edgecolor="None",
            facecolor="none",
        )
    
        plt.show(block=True)
        
        
        if self.save_image_flag:
            self._save_image(fig) 


    
    def plot_main_risk_profile(self):
        
        main_risk_df = self.block_grouper.get_main_risk_profile()
        colors = main_risk_df.custom_colors
        font_size = 8
        max_y = 5000
    
        ax_main_risk_df = main_risk_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=colors,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_main_risk_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_main_risk_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=6)
        plt.ylabel("Величина риска, %", labelpad=5, fontsize=6)
        fig.canvas.manager.set_window_title("Обзор величины риска")
        fig.set_dpi(250)
        
        
        plt.legend(
            loc="upper center",
            # bbox_to_anchor=(0.5, 1),
            fontsize=font_size - 2,
            # ncols=4,
            # ncol=2,
            reverse=True,
            labelspacing=2,
            edgecolor="None",
            facecolor="none",
        )

        if self.save_image_flag:
            self._save_image(fig) 

    
    def plot_risk_events_profile(self):
    
        risk_events_df = self.block_grouper.get_risk_events_profile()

        colors = risk_events_df.colors

        font_size = 8
        max_y = 5000
            
        ax_main_risk_df = risk_events_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=colors,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_main_risk_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_main_risk_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=6)
        plt.ylabel("События риска, %", labelpad=5, fontsize=6)
        fig.canvas.manager.set_window_title("Обзор событий риска")
        fig.set_dpi(250)
        
        plt.legend(
            loc="upper center",
            # bbox_to_anchor=(0.5, 1),
            fontsize=font_size - 2,
            # ncols=4,
            # ncol=2,
            reverse=True,
            labelspacing=2,
            edgecolor="None",
            facecolor="none",
        )
            
        if self.save_image_flag:
            self._save_image(fig) 


    def plot_repair_profile(self, *, mode):
        if mode not in ["status", "flow"]:
            raise ValueError("Mode must be 'status' or 'flow'")

        repair_df = self.block_grouper.get_repair_profile(mode=mode)
        
        colors = repair_df.colors

        font_size = 8
        max_y = 5000

        ax_main_risk_df = repair_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=colors,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_main_risk_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_main_risk_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=6)
        plt.ylabel("Статусы ремонтов" if mode == "status" else "Снижение риска от ремонтов", labelpad=5, fontsize=6)
        title = "Обзор ремонтов (по статусу)" if mode == "status" else "Обзор ремонтов (по потоку)"
        fig.canvas.manager.set_window_title(title)
        fig.set_dpi(250)
        
        plt.legend(
            loc="upper center",
            # bbox_to_anchor=(0.5, 1),
            fontsize=font_size - 2,
            # ncols=4,
            # ncol=2,
            reverse=True,
            labelspacing=2,
            edgecolor="None",
            facecolor="none",
        )
            
        if self.save_image_flag:
            self._save_image(fig) 




    def plot_cost_profile_by_blocks(self, *, cumulative=False):
        
        cost_df = self.block_grouper.get_cost_profile_by_block()
        colors = cost_df.colors
        
        fig = plt.gcf()
        fig.set_dpi(250)
        fig.canvas.manager.set_window_title("Обзор стоимости ремонтов по блокам")

            
            
            
        if self.save_image_flag:
            self._save_image(fig) 


    def plot_cost_profile(self, *, cumulative=False):
        
        cost_df = self.block_grouper.get_cost_profile()
        color = "black"
        
        fig = plt.gcf()
        fig.set_dpi(250)
        fig.canvas.manager.set_window_title("Обзор стоимости ремонтов")

            
            
            
        if self.save_image_flag:
            self._save_image(fig) 

        
    def plot_general_graph(self):
        pass
        # электроэнергия
        # события рисков
        # накопительный риск
        # ремонты всех видов
        # стоимость ремонтов
        # накопительная стоимость ремонтов
        fig = plt.gcf()
        
        if self.save_image_flag:
            self._save_image(fig) 


    def _save_image(self, fig):
            fname = (
                get_file_name_with_auto_number(self.image_folder, self.scenario, "png"),
            )
            fig.savefig(
                fname=fname,
                bbox_inches="tight",
                dpi=600,
                transparent=True,
            )
            
            
            

class Control_block_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        
    def select_block(self, block):
        if block is None:
            raise ValueError("Block is None")
        self.db = self.block_grouper.get_helper_block_profiles(block)
        
            
    def plot_default_risk_profile(self):
        pass
        
        
    def plot_source_output_profile(self, *, mode):
        if mode not in ["source_period", "source_repair"]:
            raise ValueError("Mode must be 'source_period' or 'source_repair'")
        
        
    def plot_storage_profiles(self, *, mode):
        if mode not in ["storage_period", "storage_main_risk", "storage_repair"]:
            raise ValueError("Mode must be 'storage_period', 'storage_main_risk' or 'storage_repair'")

            
    def plot_converter_profiles(self, *, mode):
        if mode not in ["input_main_risk", "input_period_control", "input_repair_control", "output"]:
            raise ValueError("Mode must be 'converter_repair'")
            
        
        
        
        
        
        
        
        
        # res = {}
        # res["source_period"] = {"output": helper_node_calculator.get_source_period_output_profile()}
        # res["source_repair"] = {"output": helper_node_calculator.get_source_repair_output_profile()}

        # res["source_default_risk"] = {"output": helper_node_calculator.get_default_output_profile()}

        # res["converter_repair"] = {
        #     "input_main_risk": helper_node_calculator.get_converter_input_main_risk_profile(),
        #     "input_period_control": helper_node_calculator.get_converter_input_period_control_profile(),
        #     "input_repair_control": helper_node_calculator.get_converter_input_repair_control_profile(),
        #     "output": helper_node_calculator.get_converter_output_profile(),
        # }

        # res["storage_period"] = {
        #     "input": helper_node_calculator.get_storage_profiles("storage_period", "input"),
        #     "output": helper_node_calculator.get_storage_profiles("storage_period", "output"),
        #     "content": helper_node_calculator.get_storage_profiles("storage_period", "content"),
        # }
        # res["storage_main_risk"] = {
        #     "input": helper_node_calculator.get_storage_profiles("storage_main_risk", "input"),
        #     "output": helper_node_calculator.get_storage_profiles("storage_main_risk", "output"),
        #     "content": helper_node_calculator.get_storage_profiles("storage_main_risk", "content"),
        # }
        # res["storage_repair"] = {
        #     "input": helper_node_calculator.get_storage_profiles("storage_repair", "input"),
        #     "output": helper_node_calculator.get_storage_profiles("storage_repair", "output"),
        #     "content": helper_node_calculator.get_storage_profiles("storage_repair", "content"),
        # }
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        
    
    
    
    