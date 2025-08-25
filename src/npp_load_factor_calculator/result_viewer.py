from pathlib import Path

from matplotlib import pyplot as plt

from src.npp_load_factor_calculator.utilites import center_matplotlib_figure, get_file_name_with_auto_number


class Result_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        self.scenario = block_grouper.custom_es.scenario
        self.save_image_flag = False
        self.image_folder = None
        
        
    def _save_image(self, figure, dpi):
        
        folder = Path(self.image_folder)
        name = get_file_name_with_auto_number(folder, self.scenario, self.image_format)
        path = folder / name
        
        figure.savefig(
            path,
            bbox_inches="tight",
            dpi=dpi,
            transparent=True,
        )
        print(f"Saved to {path}")
        
        
    def set_image_flag(self, flag):
        self.save_image_flag = flag
    
    
    def set_image_options(self, folder, image_format, dpi):
        self.image_folder = folder
        self.image_format = image_format
        self.image_dpi = dpi
        
        
    def plot_electricity_generation_profile(self):
        
        el_gen_df = self.block_grouper.get_electricity_profile()
        custom_colors = el_gen_df.colors
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
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("Производство электроэнергии, МВт$\cdot$ч", labelpad=5, fontsize=font_size - 2)
        fig.canvas.manager.set_window_title("Почасовая генерация электроэнергии")
        fig.set_dpi(150)
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        
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
            self._save_image(fig, self.image_dpi) 


    
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
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("Величина риска, %", labelpad=5, fontsize=font_size - 2)
        fig.canvas.manager.set_window_title("Обзор величины риска")
        fig.set_dpi(150)
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        
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
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("События риска, %", labelpad=5, fontsize=font_size - 2)
        fig.canvas.manager.set_window_title("Обзор событий риска")
        fig.set_dpi(150)
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
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
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("Статусы ремонтов" if mode == "status" else "Снижение риска от ремонтов", labelpad=5, fontsize=font_size - 2)
        title = "Обзор ремонтов (по статусу)" if mode == "status" else "Обзор ремонтов (по потоку)"
        fig.canvas.manager.set_window_title(title)
        fig.set_dpi(150)
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
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
        
        cost_df = self.block_grouper.get_cost_profile_by_block(сumulative=cumulative)
        colors = cost_df.colors
        
        font_size = 8
        max_y = 5000
        
        ax_cost_by_block_df = cost_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=colors,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_cost_by_block_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_cost_by_block_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("Затраты на ремонты по блокам, $", labelpad=5, fontsize=font_size - 2)
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title("Обзор затрат на ремонты по блокам")
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
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




    def plot_cost_profile(self, *, cumulative=False):
        
        cost_df = self.block_grouper.get_cost_profile(cumulative=cumulative)
        color = "black"
        
        font_size = 8
        max_y = 5000  

        
        ax_cost_df = cost_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_cost_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_cost_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("Затраты на ремонты, $", labelpad=5, fontsize=font_size - 2)
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title("Обзор затрат на ремонты")
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
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

        
    def plot_general_graph(self):
        pass
        # электроэнергия
        # события рисков
        # накопительный риск
        # ремонты всех видов
        # стоимость ремонтов
        # накопительная стоимость ремонтов
        # fig = plt.gcf()
        
        # if self.save_image_flag:
        #     self._save_image(fig) 


    # def _save_image(self, fig):
    #         fname = (
    #             get_file_name_with_auto_number(self.image_folder, self.scenario, "png"),
    #         )
    #         fig.savefig(
    #             fname=fname,
    #             bbox_inches="tight",
    #             dpi=600,
    #             transparent=True,
    #         )
            
            
            

class Control_block_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        
    def select_block(self, block):
        if block is None:
            raise ValueError("Block is None")
        # try:
        self.block_db = self.block_grouper.get_helper_block_profiles(block)
        self.status = True
        # except Exception as e:
        #     self.status = False
        #     print(e)
        
        
            
    def plot_default_risk_profile(self):
        
        if not self.status:
            return
        
        if not self.block_db:
            return
        
        
        default_risk_df = self.block_db["source_default_risk"]["output"]
        
        if default_risk_df.empty:
            return
        
        
        color = "red"
        
        font_size = 8
        max_y = default_risk_df.max().max()  
        
        ax_default_risk_df = default_risk_df.plot(
            kind="area",
            ylim=(0, max_y * 10),
            legend="reverse",
            color="#d2f319",
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_default_risk_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_default_risk_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("default risk profile - output", labelpad=5, fontsize=font_size - 2)
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title("default risk profile - output")
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
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
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)


        plt.show(block=True)
        
        
        
    def plot_source_output_profile(self, *, mode):
        if mode not in ["source_period", "source_repair"]:
            raise ValueError("Mode must be 'source_period' or 'source_repair'")
        
        source_output_df = self.block_db[mode]["output"]
        
        color = "black"
        
        font_size = 8
        max_y = 5000  
        
        ax_source_output_df = source_output_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        fig = plt.gcf()
        ax_source_output_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_source_output_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel(f"(helper block) {mode} - output", labelpad=5, fontsize=font_size - 2)
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title(f"{mode} - output")
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
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
        
        
        
    def plot_storage_profiles(self, *, mode, flow_mode):
        if mode not in ["storage_period", "storage_main_risk", "storage_repair"]:
            raise ValueError("Mode must be 'storage_period', 'storage_main_risk' or 'storage_repair'")

        if flow_mode not in ["input", "output", "content"]:
            raise ValueError("flow_mode must be 'input', 'output' or 'content'")

        font_size = 8

        if flow_mode == "input":
                storage_input_df = self.block_db[mode]["input"]
                max_input = storage_input_df.max().max()
                ax_storage_input_df = storage_input_df.plot(
                    kind="line",
                    ylim=(0, max_input * 1.2),
                    legend="reverse",
                    color="#000000",
                    linewidth=0.5,
                    figsize=(7, 5),
                    fontsize=font_size,
                )
        elif flow_mode == "output":
                storage_output_df = self.block_db[mode]["output"]
                max_output = storage_output_df.max().max()
                ax_storage_output_df = storage_output_df.plot(
                    kind="area",
                    ylim=(0, max_output * 1.2),
                    legend="reverse",
                    color="#002c66",
                    linewidth=0.01,
                    figsize=(7, 5),
                    fontsize=font_size,
                )
        elif flow_mode == "content":
                storage_content_df = self.block_db[mode]["content"]
                max_content = storage_content_df.max().max()
                ax_storage_content_df = storage_content_df.plot(
                kind="area",
                ylim=(0, max_content * 1.2),
                legend="reverse",
                color="#1f77b4",
                linewidth=0.01,
                figsize=(7, 5),
                fontsize=font_size,
            )
        
        plt.xlabel("Время, ч", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("МВт" if flow_mode == "input_output" else "МВтч", labelpad=5, fontsize=font_size - 2)
        fig = plt.gcf()
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title(f"{mode} - {flow_mode}")
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        plt.show(block=True)
   
        

            
    def plot_converter_profiles(self):
        
        converter_input_main_risk_df = self.block_db["converter_repair"]["input_main_risk"]
        converter_input_period_control_df = self.block_db["converter_repair"]["input_period_control"]
        converter_input_repair_control_df = self.block_db["converter_repair"]["input_repair_control"]
        converter_output_df = self.block_db["converter_repair"]["output"]
            
        
        color = "black"
        
        font_size = 8
        max_y = 5000  
        
        ax_converter_input_main_risk_df = converter_input_main_risk_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        ax_converter_input_period_control_df = converter_input_period_control_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
            ax=ax_converter_input_main_risk_df
        )

        ax_converter_input_repair_control_df = converter_input_repair_control_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
            ax=ax_converter_input_period_control_df
        )

        ax_converter_output_df = converter_output_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
            ax=ax_converter_input_repair_control_df
        )
        
        
        fig = plt.gcf()
        ax_converter_output_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_converter_output_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        plt.xlabel("Время, часы", labelpad=0, fontsize=font_size - 2)
        plt.ylabel("converter, Mwt", labelpad=5, fontsize=font_size - 2
        )
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title("converter")
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        
    
    
    
    