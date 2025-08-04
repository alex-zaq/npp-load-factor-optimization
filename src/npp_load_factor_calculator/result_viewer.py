


# from pathlib import Path

from matplotlib import pyplot as plt

from npp_load_factor_calculator.utilites import get_file_name_with_auto_number


class Result_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        self.scenario = block_grouper.scenario
        self.save_image_flag = False
        self.image_folder = None
        
        
    def set_save_image_flag(self, flag):
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
        
        ax_el_gen_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_el_gen_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        
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
    
        # full_scen_name = self.scen_name_builder.full_scen_name
        # plt.title(full_scen_name, fontsize=8, y=1.03, x=0.50)
        fig = plt.gcf()
        fig.set_dpi(250)
        fig.canvas.manager.set_window_title("Почасовая генерация электроэнергии")

        plt.xlabel("Время, часы", labelpad=0, fontsize=6)
        plt.ylabel("Производство электроэнергии, МВт$\cdot$ч", labelpad=5, fontsize=6)

        plt.show(block=True)
        
        if self.set_save_image_flag:
            fname = get_file_name_with_auto_number(self.image_folder, self.scenario, "png"),
            fig.savefig(
                fname=fname,
                bbox_inches="tight",
                dpi=600,
                transparent=True,
            )
    
    def plot_main_risk_events_profile(self):
        pass

    
    def plot_risk_events_profile(self):
        pass


    def plot_repair_profile(self, *, mode="all"):
        pass


    def plot_cost_profile(self, *, cumulative=False):
        pass
        
    def plot_general_graph(self):
        pass
    
    
    
class Control_block_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        
    def select_block(self, block):
        if block is None:
            raise ValueError("Block is None")
        self.db = self.block_grouper.get_helper_block_profiles(block)
        
            
    def plot_default_risk_profile(self):
        pass
    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # электроэнергия
        # события рисков
        # накопительный риск
        # ремонты всех видов
        # стоимость ремонтов
        # накопительная стоимость ремонтов
        
    
    
    
    