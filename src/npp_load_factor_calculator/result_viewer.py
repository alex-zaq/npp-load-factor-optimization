from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt
from oemof.visio import ESGraphRenderer

from src.npp_load_factor_calculator.utilites import (
    add_white_spaces_and_colors_el_gen,
    add_white_spaces_and_colors_repairs,
    center_matplotlib_figure,
    find_empty_columns,
    get_colors_by_repair_name,
    get_file_name_by_scenario,
    get_file_name_with_auto_number,
)


class Result_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        self.scenario = block_grouper.custom_es.scenario
        self.save_image_flag = False
        
    def create_scheme(self, folder):
        
        folder = Path(folder)
        if not folder.exists():
            folder.mkdir(parents=True)
        file_name = get_file_name_by_scenario(self.scenario)
        name = get_file_name_with_auto_number(folder, file_name, "png")
        folder = folder / name
        oemof_es = self.block_grouper.custom_es.oemof_es
        
        gr = ESGraphRenderer(
            energy_system=oemof_es,
            filepath=folder,
            img_format="png",
            txt_fontsize=12,
            txt_width=40,
            legend=False,
        )
        gr.view()


    def plot_single_block_graph(self, block, dpi, font_size = 10):
                
        el_gen_df = self.block_grouper.get_electricity_profile_by_block(block)
        repairs_df = self.block_grouper.get_repairs_profile_by_block(block, part=1)
        risk_increase_df = self.block_grouper.get_increase_by_block_df(block)

        risks_dict = self.block_grouper.get_risks_profile_by_block(block)
        risk_data_dict = {k: v["risk_line_col"] for k, v in risks_dict.items()}
        risks_df = pd.DataFrame(risk_data_dict)

        max_y = 3 * el_gen_df.max().max()

        fig, ax_base = plt.subplots()
        
        ax_el_gen_df = el_gen_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color=el_gen_df.colors,
            linewidth=0.01,
            fontsize=font_size,
            ax=ax_base
        )
        ax_el_gen_df.set_ylabel('Мощность АЭС, МВт', fontsize=font_size - 2)
        ax_el_gen_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_el_gen_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        # ax_el_gen_df.legend(loc="upper center", fontsize=font_size - 2)
        ax_el_gen_df.legend_.remove()

        ax_repair_df = repairs_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            stacked=False,
            color=repairs_df.colors,
            linewidth=0.01,
            fontsize=font_size,
            alpha=0.5,
            ax=ax_base
        )
        max_risk_val = risks_df.max().max()
        max_risk_val = 1 if max_risk_val < 1 else max_risk_val
        risk_increase_colors = ["#e41a1c",  "#0400ff"]
        ax_risks_df = risks_df.plot(
                kind="line",
                style="--",
                ylim=(0, max_risk_val * 1.5),
                legend="reverse",
                color="#000000",
                linewidth=0.5,
                fontsize=font_size,
                ax=ax_base.twinx()
            )
        ax_risks_df.set_ylabel('Величина риска', fontsize=font_size - 2)
        ax_risks_df.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_risks_df.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        ax_risks_df.legend_.remove()

        ax_risk_increase_df = risk_increase_df.plot(
                    kind="line",
                    legend="reverse",
                    ylim=(0, max_risk_val * 1.5),
                    color=risk_increase_colors,
                    linewidth=1,
                    fontsize=font_size-2,
                    ax=ax_risks_df,
                )             
        ax_risk_increase_df.legend_.remove()

        
        lines_1, labels_1 = ax_base.get_legend_handles_labels()
        lines_2, labels_2 = ax_risks_df.get_legend_handles_labels()
        lines = lines_1 + lines_2
        labels = labels_1 + labels_2
        ax_base.legend(lines, labels, loc='upper center', fontsize=font_size - 2, ncol=2)
        ax_base.set_xlabel('Время, дни', fontsize=font_size - 2)


        x_max = risks_df.index[round(risks_df.shape[0]/2)]
        ax_risks_df.text(
                x_max,
                1 * 1.03,
                f"условная граница риска = {1:.1f}",
                fontsize=font_size - 2,
                horizontalalignment="center",
                verticalalignment="bottom",
                color="black",
                # weight="bold"
            )
        
        ax_risks_df.axhline(y=1, color='r', linestyle='--', label='верхняя граница риска')
    
    
        fig = plt.gcf()
        ax_base.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_base.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        fig.canvas.manager.set_window_title(f"Расчет плановых остановок (один блок) - {block.label}")
        fig.set_dpi(dpi)
  
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        plt.show(block=True)
        
        image_builder = Image_builder(fig, self.scenario)
        
        return image_builder
        
          
    def plot_all_blocks_with_risks_graph(self, outages_graph, cost_balance_graph=False, dpi=120, font_size = 10):
    
    
        if not (outages_graph or cost_balance_graph):
            raise ValueError("At least one of npp_graph or risk_graph must be True")
        
        if (outages_graph and cost_balance_graph):
            fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={'width_ratios': [1.7, 1]})
        else:
            fig, ax_left = plt.subplots()
                
        
    
    
        if outages_graph:
            
            el_gen_df = self.block_grouper.get_electricity_profile_all_blocks()
            el_gen_df = add_white_spaces_and_colors_el_gen(el_gen_df, 1170)
            repairs_dict = self.block_grouper.get_repairs_profile_by_all_blocks_dict()
            repairs_df = add_white_spaces_and_colors_repairs(repairs_dict, 1170)
            risk_increase_df = self.block_grouper.get_increase_all_blocks_df()

            risks_dict = self.block_grouper.get_risks_profile_by_all_blocks_dict()
            risk_data_dict = {k: v["risk_line_col"] for k, v in risks_dict.items()}
            risk_df = pd.DataFrame(risk_data_dict)
        
    
            max_y = el_gen_df.sum(axis=1).max() * 2

            el_gen_colors = el_gen_df.colors
            # el_gen_df = el_gen_df.where(el_gen_df<= 0, 0)

            ax_el_gen_df = el_gen_df.plot(
                kind="area",
                ylim=(0, max_y),
                legend="reverse",
                color=el_gen_colors,
                linewidth=0.01,
                alpha=1,
                fontsize=font_size,
                ax=ax_left,
                zorder=0
            )
            
            ax_repairs_df = repairs_df.plot(
                kind="area",
                ylim=(0, max_y),
                legend="reverse",
                stacked=True,
                color=repairs_df.colors,
                linewidth=0.01,
                alpha=0.7,
                fontsize=font_size,
                ax=ax_left,
                zorder=1
            )
            risk_increase_colors = ["#e41a1c",  "#0400ff", "#00ff00", "#ff0"]
            max_y_cost = risk_df.max().max() * 1.5
            ax_risk_df = risk_df.plot(
                kind="line",
                ylim=(0, max_y_cost),
                legend="reverse",
                style="--",
                color=risk_increase_colors,
                linewidth=0.7,
                fontsize=font_size-2,
                ax=ax_left.twinx()
            )
            ax_risk_df.set_ylabel('Условная величина риска', fontsize=font_size - 2)
            ax_risk_df.legend(loc='upper left', fontsize=font_size - 2, ncol=1)
            ax_risk_df.legend_.remove()
            
            
            
            ax_risk_increase_df = risk_increase_df.plot(
                kind="line",
                ylim=(0, max_y_cost),
                legend="reverse",
                color=risk_increase_colors,
                linewidth=1,
                fontsize=font_size-2,
                ax=ax_risk_df,
            )             
            ax_risk_increase_df.legend_.remove()
            
            x_max = risk_df.index[round(risk_df.shape[0]/2)]
            ax_risk_df.text(
                    x_max,
                    1 * 1.03,
                    f"условная граница риска = {1:.1f}",
                    fontsize=font_size - 2,
                    horizontalalignment="center",
                    verticalalignment="bottom",
                    color="black",
                    # weight="bold"
                )
            ax_risk_df.axhline(y=1, color='r', linestyle='--')
           
            
            # legend_empty_cols = [col for col in repairs_df.columns if (repairs_df[col] <= 0).all()]
            legend_empty_cols = find_empty_columns(repairs_df)
            
            
            lines_1, labels_1 = ax_left.get_legend_handles_labels()
            lines_2, labels_2 = ax_risk_df.get_legend_handles_labels()
            main_legend_dict = dict(zip(labels_1, lines_1))
            legend_dict_updated = {k:v for k,v in main_legend_dict.items() if ("white" not in k) and (k not in legend_empty_cols)}
            updated_lines = list(legend_dict_updated.values()) + lines_2
            updated_labels = list(legend_dict_updated.keys()) + labels_2
            ax_left.legend(updated_lines, updated_labels, loc='upper left', fontsize=font_size - 2, ncol=2)
            ax_left.set_ylabel('Мощность АЭС, МВт', fontsize=font_size - 2)
            ax_left.set_xlabel('Время, дни', fontsize=font_size - 2)
    
        if cost_balance_graph:
                                
                ax_cost = ax_right if outages_graph else ax_left
                
                cost_balance_by_repair_name = self.block_grouper.get_cost_balance_by_repair_name_all_blocks()
                repairs_dict = self.block_grouper.get_repairs_profile_by_all_blocks_dict()
                cost_balance_colors = get_colors_by_repair_name(repairs_dict)
                cost_balance_df = pd.DataFrame(cost_balance_by_repair_name, index=["затраты на ремонты"])/ 1e6

                max_Y = cost_balance_df.sum(axis=1)[0]

                ax_cost_balance_df = cost_balance_df.plot(
                    kind="bar",
                    stacked=True,
                    # figsize=(6.5, 6),
                    ylim=(0, max_Y * 1.5),
                    width=0.1,
                    legend="reverse",
                    fontsize=font_size-2,
                    alpha=0.6,
                    ax = ax_cost,
                    color=cost_balance_colors,
                )
                
                y_res = 0
                x_res = ax_cost_balance_df.patches[0].get_x() + ax_cost_balance_df.patches[0].get_width() / 2
                for p in ax_cost_balance_df.patches:
                    width = p.get_width()
                    height = p.get_height()
                    y_res += height
                    x, y = p.get_x(), p.get_y()
                    ax_cost_balance_df.text(x+width/2, y+height/2, f"{height:.0f}", ha='center', va='center', fontsize=font_size-2)
                
                total = max_Y
                ax_cost_balance_df.text(x_res, total*1.03, f"{total:.0f}", ha="center", va="center", fontsize=font_size-2, fontweight='bold')

                
                ax_cost_balance_df.tick_params(axis='x', rotation=0)
                ax_cost_balance_df.set_ylabel('Затраты, млн. долл. США', fontsize=font_size - 2)
                ax_cost_balance_df.legend(loc='upper right', fontsize=font_size - 2, ncol=1)
                fig.subplots_adjust(wspace=0.25)
    
    
    
    
    

        
        ax_left.tick_params(axis="both", which="major", labelsize=font_size - 2)
        ax_left.tick_params(axis="both", which="minor", labelsize=font_size - 2)
        fig = plt.gcf()
        fig.canvas.manager.set_window_title("Расчет плановых остановок")
        fig.set_dpi(dpi)
  
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        plt.show(block=True)
        
        image_builder = Image_builder(fig, self.scenario)
        return image_builder
              
               
               
                
   
    def plot_all_blocks_with_cost_graph(self, outages_graph, risk_graph=False, dpi=120, font_size = 10):
        
        if not (outages_graph or risk_graph):
            raise ValueError("At least one of npp_graph or risk_graph must be True")
        
        if (outages_graph and risk_graph):
            fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 5))
        else:
            fig, ax_left = plt.subplots()
                
                          
                       
        el_gen_df = self.block_grouper.get_electricity_profile_all_blocks()
        repairs_dict = self.block_grouper.get_repairs_profile_by_all_blocks_dict()
        cost_all_blocks_df = self.block_grouper.get_cost_profile_all_blocks(cumulative=True)
        risk_increase_df = self.block_grouper.get_increase_all_blocks_df()
        # risk_decrease_df = self.block_grouper.get_decrease_all_blocks_df()
        
        el_gen_df = add_white_spaces_and_colors_el_gen(el_gen_df, 1170)
        repairs_df = add_white_spaces_and_colors_repairs(repairs_dict, 1170)
        

        if outages_graph:
            max_y = el_gen_df.sum(axis=1).max() * 2
            
            el_gen_colors = el_gen_df.colors
            # el_gen_df = el_gen_df.where(el_gen_df<= 0, 0)
            ax_el_gen_df = el_gen_df.plot(
                kind="area",
                ylim=(0, max_y),
                legend="reverse",
                color=el_gen_colors,
                linewidth=0.01,
                alpha=1,
                fontsize=font_size,
                ax=ax_left
            )
                
            ax_repairs_df = repairs_df.plot(
                kind="area",
                ylim=(0, max_y),
                legend="reverse",
                stacked=True,
                color=repairs_df.colors,
                linewidth=0.01,
                alpha=0.6,
                fontsize=font_size,
                ax=ax_left
            )
        
            max_y_cost = cost_all_blocks_df.max().max() * 1.5
            ax_cost_all_blocks_df = cost_all_blocks_df.plot(
                kind="line",
                ylim=(0, max_y_cost),
                legend="reverse",
                color="black",
                style="-",
                linewidth=1,
                fontsize=font_size-2,
                ax=ax_left.twinx()
            )
            ax_cost_all_blocks_df.set_ylabel('Затраты, млн. долл. США', fontsize=font_size - 2)
            ax_cost_all_blocks_df.legend_.remove()
        
            ax_left.set_ylabel('Мощность АЭС, МВт', fontsize=font_size - 2)

            lines, labels = ax_cost_all_blocks_df.get_legend_handles_labels()
            
            legen_cost_dict = dict(zip(labels, lines))
    
        
            lines, labels = ax_left.get_legend_handles_labels()
            
            
            main_legend_dict = dict(zip(labels, lines))
            
            main_legend_dict.update(legen_cost_dict)

            # legend_empty_cols = [col for col in repairs_df.columns if (repairs_df[col] <= 0).all()]
            legend_empty_cols = find_empty_columns(repairs_df)
            
            legend_dict_updated = {k:v for k,v in main_legend_dict.items() if ("white" not in k) and (k not in legend_empty_cols)}
            
            updated_lines = list(legend_dict_updated.values())
            updated_labels = list(legend_dict_updated.keys())
            ax_left.legend(updated_lines, updated_labels, loc='upper left', fontsize=font_size - 2, ncol=2)
            
            ax_left.tick_params(axis="both", which="major", labelsize=font_size - 2)
            ax_left.tick_params(axis="both", which="minor", labelsize=font_size - 2)

            ax_left.set_xlabel("Время, дни", fontsize=font_size - 2)
            
            cost_upper_bound = cost_all_blocks_df.max().max()
            
            ax_cost_all_blocks_df.axhline(y=cost_upper_bound, color='black', linestyle='--', label='затраты за период')
            
            # x_max = cost_all_blocks_df.index[-round(85*cost_all_blocks_df.shape[0]/365)]
            x_max = cost_all_blocks_df.index[-round(cost_all_blocks_df.shape[0]/2)]
            y_max = cost_all_blocks_df.max().max()
            ax_cost_all_blocks_df.text(
                x_max,
                y_max * 1.03,
                f"затраты на ремонты = {y_max:.2f}",
                fontsize=font_size - 2,
                horizontalalignment="center",
                verticalalignment="bottom",
                color="black",
                weight="bold"
                )
        
        if risk_graph:

            ax_right = ax_left if not outages_graph else ax_right     

            ax_right = ax_right
            risks_dict = self.block_grouper.get_risks_profile_by_all_blocks_dict()
            risk_colors = [v["color"] for v in risks_dict.values()]
            risk_data_dict = {k: v["risk_line_col"] for k, v in risks_dict.items()}
            risk_df = pd.DataFrame(risk_data_dict)
            max_y_cost = risk_df.max().max() * 1.5


            if len(max_risk_value:=set(v["max_risk"] for v in risks_dict.values())) == 1:
                max_risk_value = max_risk_value.pop()
                max_y_cost = 1 * 1.5
            else:
                raise Exception("Different max_risk values")


            ax_risk_df = risk_df.plot(
                kind="line",
                ylim=(0, max_y_cost),
                legend="reverse",
                color=risk_colors,
                linewidth=0.7,
                fontsize=font_size-2,
                ax=ax_right
            )
            ax_right.set_ylabel('Условная величина риска', fontsize=font_size - 2)
            ax_right.legend(loc='upper left', fontsize=font_size - 2, ncol=1)
            

            # x_max = risk_df.index[round(85*risk_df.shape[0]/365)]
            x_max = risk_df.index[round(risk_df.shape[0]/2)]
            y_max = risk_df.max().max()

            ax_risk_df.text(
                x_max,
                1 * 1.03,
                f"Условная граница риска = {max_risk_value:.1f}",
                fontsize=font_size - 2,
                horizontalalignment="center",
                verticalalignment="bottom",
                color="black",
                weight="bold"
            )


            fig.subplots_adjust(wspace=0.3)
            ax_risk_df.set_xlabel("Время, дни", fontsize=font_size - 2)
            
            
            risk_increase_colors = ["#e41a1c",  "#0400ff"]
            
             
            if not risk_increase_df.empty:
                ax_risk_increase_df = risk_increase_df.plot(
                    kind="line",
                    # kind="area",
                    ylim=(0, max_y_cost),
                    legend="reverse",
                    color=risk_increase_colors,
                    linewidth=1,
                    fontsize=font_size-2,
                    ax=ax_right
                )
                
            ax_risk_increase_df.legend(loc='upper right', fontsize=font_size - 2, ncol=1)    


            # risk_decrease_df = risk_decrease_df.mul(-1)
            
            # if not risk_decrease_df.empty:
            #     ax_risk_decrease_df= risk_decrease_df.plot(
            #         kind="area",
            #         ylim=(0, max_y_cost),
            #         legend=False,
            #         color=risk_colors,
            #         linewidth=0.01,
            #         fontsize=font_size-2,
            #         ax=ax_right
            #     )
                
            # ax_risk_increase_df.legend(loc='upper right', fontsize=font_size - 2, ncol=1)    
           
            # min_y = risk_decrease_df.min().min() * 1.1
            

                # ax_risk_decrease_df.legend_.remove()
            # ax_risk_decrease_df.legend(loc='upper right', fontsize=font_size - 2, ncol=1)    


            ax_risk_df.axhline(y=1, color='r', linestyle='--', label='верхняя граница риска')


        fig.set_dpi(dpi)
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        plt.show(block=True)
        
        image_builder = Image_builder(fig, self.scenario)

        return image_builder

class Image_builder:
    
    def __init__(self, fig, scenario):
        self.fig = fig
        self.scenario = scenario
        
    def save(self, folder, format, dpi=100):
        
        folder = Path(folder)
        if not folder.exists():
            folder.mkdir(parents=True)
            
            
        scenario_folder  = folder / get_file_name_by_scenario(self.scenario)
        if not scenario_folder.exists():
            scenario_folder.mkdir(parents=True)
            
        file_name = get_file_name_by_scenario(self.scenario)    
        name = get_file_name_with_auto_number(scenario_folder, file_name, format)

        path = scenario_folder / name
        
        self.fig.savefig(
            path,
            bbox_inches="tight",
            dpi=dpi,
            transparent=True,
        )
        print(f"Saved to {path}")
            

class Control_block_viewer:
    
    def __init__(self, block_grouper):
        self.block_grouper = block_grouper
        
    def plot_npp_status(self, block):
        
        npp_status_df = self.block_grouper.get_npp_status_profile(block)

        font_size = 6
        max_y = 1.2 * npp_status_df.max().max()

        print("npp_status",npp_status_df.sum().sum())

        ax_profile_df = npp_status_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color="black",
            linewidth=0.5,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        ax_profile_df.legend(loc="upper center", fontsize=font_size)
        fig = plt.gcf()
        fig.set_dpi(150)
        
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        
        plt.show(block=True)
        
        
        
    def plot_control_stop_block(self, block):
        
        control_stop_block_profile_df = self.block_grouper.get_control_stop_block_profile(block)

        font_size = 6
        max_y = 1.2 * control_stop_block_profile_df.max().max()

        print("control_stop_block",control_stop_block_profile_df.sum().sum())

        ax_sink_profile_df = control_stop_block_profile_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            color="black",
            linewidth=0.5,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        ax_sink_profile_df.legend(loc="upper center", fontsize=font_size)
        fig = plt.gcf()
        fig.set_dpi(150)
        
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        
        plt.show(block=True)
        

    def plot_sinks_profile(self, block, repair_id, risk_name):
        
        sink_profile_df = self.block_grouper.get_sinks_profile(block, repair_id, risk_name)

        font_size = 6
        max_y = 1.2 * sink_profile_df.max().max()

        ax_sink_profile_df = sink_profile_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            # color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        ax_sink_profile_df.legend(loc="upper center", fontsize=font_size)
        fig = plt.gcf()
        fig.set_dpi(150)
        
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        
        plt.show(block=True)
        
        
    def plot_npp_storage_data(self, block):
        
        npp_storage_data_dict = self.block_grouper.get_npp_storage_dict(block)
        
        input_flow_df = npp_storage_data_dict["input_flow"]
        output_flow_df = npp_storage_data_dict["output_flow"]
        storage_content_df = npp_storage_data_dict["storage_content"]

        # res = pd.concat([input_flow_df, output_flow_df, storage_content_df], axis=1)

        # print(res.head(5))

        font_size = 6
        max_y = 1.2 * storage_content_df.max().max()



        ax_storage_content_df = storage_content_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            # color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        print("зарядка (npp_storage)",input_flow_df.sum().sum())
        
        
        ax_input_df = input_flow_df.plot(
            kind="line",
            ylim=(0, max_y),
            legend="reverse",
            color="red",
            linewidth=1,
            figsize=(7, 5),
            fontsize=font_size,
            ax = ax_storage_content_df
        )
        
        ax_output_df = output_flow_df.plot(
            kind = "line",
            ylim=(0, max_y),
            legend="reverse",
            color="blue",
            linewidth=1,
            figsize=(7, 5),
            fontsize=font_size,
            ax = ax_input_df
        )

        
        ax_storage_content_df.legend(loc="upper center", fontsize=font_size)
        fig = plt.gcf()
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title("npp_storage")
        
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        
        plt.show(block=True)
        
        
        
    def plot_repair_storage_max_uptime(self, block, repair_id):
        
        npp_storage_data_dict = self.block_grouper.get_repair_storage_max_uptime_dict(block, repair_id)
        
        input_flow_df = npp_storage_data_dict["input_flow"]
        output_flow_df = npp_storage_data_dict["output_flow"]
        storage_content_df = npp_storage_data_dict["storage_content"]

        # res = pd.concat([input_flow_df, output_flow_df, storage_content_df], axis=1)

        # print(res.head(5))

        font_size = 6
        max_y = 1.2 * storage_content_df.max().max()

        ax_storage_content_df = storage_content_df.plot(
            kind="area",
            ylim=(0, max_y),
            legend="reverse",
            # color=color,
            linewidth=0.01,
            figsize=(7, 5),
            fontsize=font_size,
        )
        
        ax_input_df = input_flow_df.plot(
            kind="line",
            ylim=(0, max_y),
            legend="reverse",
            color="red",
            linewidth=1,
            figsize=(7, 5),
            fontsize=font_size,
            ax = ax_storage_content_df
        )
        
        print("зарядка (repair_max_uptime_storage)",input_flow_df.sum().sum())
        
        ax_output_df = output_flow_df.plot(
            kind = "line",
            ylim=(0, max_y),
            legend="reverse",
            color="blue",
            linewidth=1,
            figsize=(7, 5),
            fontsize=font_size,
            ax = ax_input_df
        )

        
        ax_storage_content_df.legend(loc="upper center", fontsize=font_size)
        fig = plt.gcf()
        fig.set_dpi(150)
        fig.canvas.manager.set_window_title("repair_max_uptime_storage")
        
        center_matplotlib_figure(fig, extra_y=-60, extra_x=40)
        
        plt.show(block=True)

    
 
        
        
        
        
        

        
        
        
        
        
        
        
        
        
        
        
        
        

        
    
    
    
    