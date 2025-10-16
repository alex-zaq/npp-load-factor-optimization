


import numpy as np
import pandas as pd
from oemof import solph


class Custom_block:

    def __init__(self, block):
        self.wrapper_block = block
        self.results = self.__class__.results
        self.risks_plot_dict = {}
        self.repair_plot_dict = {}
        self.repair_cost_plot_dict = {}
        
        
    
    
    def get_electricity_profile(self):
        block,output_bus = self.wrapper_block.block.outputs_pair[0]     
        block_results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[block.label] = block_results[((block.label, output_bus.label), "flow")]
        res_df = res_df.clip(lower=0)
        return res_df


    def get_risks_profile(self):
        res_df = pd.DataFrame()
        colors = []
        for risk_label, risk_plot_data in self.risks_plot_dict.items():
            colors.append(risk_plot_data["color"])
            storage = risk_plot_data["storage"]
            results = solph.views.node(self.results, storage.label)["sequences"].dropna()
            res_df[risk_label] = results[(storage.label, "None"), "storage_content"]
            res_df = res_df.clip(lower=0)
        res_df.colors = colors
        return res_df
    
    def get_max_risk_dict(self):
        max_risk_dict = {}
        for risk_label, risk_plot_data in self.risks_plot_dict.items():
            storage = risk_plot_data["storage"]
            max_risk_dict[risk_label] = storage.nominal_storage_capacity
        return max_risk_dict
        

    def get_repair_status_profile(self):
        res_df = pd.DataFrame()
        colors = []
        for repair_label, repair_plot_data in self.repair_plot_dict.items():
            colors.append(repair_plot_data["color"])
            block = repair_plot_data["repair_block"].block
            output_bus = block.outputs_pair[0][1]
            results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
            res_df[repair_label] = results[((block.label, output_bus.label), "status")]
        res_df = res_df.clip(lower=0)
        res_df.colors = colors
        return res_df
        
    def get_cost_profile(self):
        res_df = pd.DataFrame()
        colors = []
        for repair_label, repair_plot_data in self.repair_plot_dict.items():
            colors.append(repair_plot_data["color"])
            block = repair_plot_data["repair_block"].block
            output_bus = block.outputs_pair[0][1]
            startup_cost = block.startup_cost
            results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
            res_df[repair_label] = results[((block.label, output_bus.label), "startup")]
            res_df[repair_label]  = res_df[repair_label] * startup_cost
        res_df = res_df.sum(axis=1)
        res_df.colors = colors
        return res_df
    
    def get_sinks_profile(self, repair_id, risk_name):
        selected_repair_block = self.wrapper_block.repairs_blocks[repair_id].block
        sink = selected_repair_block.sinks[risk_name]
        input_bus = sink.inputs_pair[0][0]
        res_df = pd.DataFrame()
        sink_results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res_df[sink.label] = sink_results[((input_bus.label, sink.label), "flow")]
        res_df = res_df.clip(lower=0)
        return res_df
    
    def get_control_stop_block_profile(self):
        control_stop_block = self.wrapper_block.block.control_npp_stop_source.block
        block, output = control_stop_block.outputs_pair[0]
        block_results = solph.views.node(self.results, output.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[block.label] = block_results[((block.label, output.label), "flow")]
        res_df = res_df.clip(lower=0)
        return res_df
    
    def get_npp_status_profile(self):
        block, output = self.wrapper_block.block.outputs_pair[0]
        block_results = solph.views.node(self.results, output.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[block.label] = block_results[((block.label, output.label), "status")]
        res_df = res_df.clip(lower=0)
        return res_df
    
    def get_npp_storage_data_dict(self):
        res_dict = {}
        storage = self.wrapper_block.block.control_npp_stop_source.block.specific_status_duration_storage
        storage_results = solph.views.node(self.results, storage.label)["sequences"].dropna()
        storage_content_df = pd.DataFrame()
        storage_content_df["storage_content"] = storage_results[(storage.label, "None"), "storage_content"]
        res_dict["storage_content"] = storage_content_df
        input_flow_df = pd.DataFrame()
        input_bus, block = storage.inputs_pair[0]
        input_flow_df["input_flow"] = storage_results[(input_bus.label, block.label), "flow"]
        res_dict["input_flow"] = input_flow_df
        output_flow_df = pd.DataFrame()
        block, output_bus = storage.outputs_pair[0]
        output_flow_df["output_flow"] = storage_results[(block.label, output_bus.label), "flow"]
        res_dict["output_flow"] = output_flow_df
        return res_dict
    
    def get_repair_storage_max_uptime_dict(self, repair_id):
        res_dict = {}
        selected_repair_block = self.wrapper_block.block.repairs_blocks[repair_id].block
        max_uptime_storage = selected_repair_block.max_uptime_storage 
        storage_results = solph.views.node(self.results, max_uptime_storage.label)["sequences"].dropna()
        storage_content_df = pd.DataFrame()
        storage_content_df["storage_content"] = storage_results[(max_uptime_storage.label, "None"), "storage_content"]
        res_dict["storage_content"] = storage_content_df
        input_flow_df = pd.DataFrame()
        input_bus, block = max_uptime_storage.inputs_pair[0]
        input_flow_df["input_flow"] = storage_results[(input_bus.label, block.label), "flow"]
        res_dict["input_flow"] = input_flow_df
        output_flow_df = pd.DataFrame()
        block, output_bus = max_uptime_storage.outputs_pair[0]
        output_flow_df["output_flow"] = storage_results[(block.label, output_bus.label), "flow"]
        res_dict["output_flow"] = output_flow_df
        return res_dict
           
                
    def get_events_profile(self):
        for risk_name, events_source in self.wrapper_block.block.events_sources.items():
            block, output = events_source.block.outputs_pair[0]
            block_results = solph.views.node(self.results, output.label)["sequences"].dropna()
            res_df = pd.DataFrame()
            res_df[f"события риска {risk_name} ({self.wrapper_block.label})"] = block_results[((block.label, output.label), "flow")]
            res_df = res_df.clip(lower=0)
            return res_df
        
        
    def get_risk_increase_profile(self):
        res = pd.DataFrame()
        res_df = pd.DataFrame()
        risks = self.wrapper_block.block.risks
        for risk_name, storage in risks.items():
            input_bus, block = storage.inputs_pair[0]
            block_results = solph.views.node(self.results, storage.label)["sequences"].dropna()
            res_df[f"увеличение риска {risk_name} ({self.wrapper_block.label})"] = block_results[((input_bus.label, block.label), "flow")]
            res_df = res_df.clip(lower=0)
            res = pd.concat([res, res_df], axis=1)
        return res_df
        
    
    def get_risk_decrease_profile(self):
        res = pd.DataFrame()
        res_df = pd.DataFrame()
        risks = self.wrapper_block.block.risks
        for risk_name, storage in risks.items():
            block, output_bus = storage.outputs_pair[0]
            block_results = solph.views.node(self.results, storage.label)["sequences"].dropna()
            res_df[f"снижение риска {risk_name} ({self.wrapper_block.label})"] = block_results[((block.label, output_bus.label), "flow")]
            res_df = res_df.clip(lower=0)
            res = pd.concat([res, res_df], axis=1)
        return res_df
                      
        
    
###############################################################################################################    

class Block_grouper:

    def __init__(self, results, custom_es):
        self.results = results
        self.custom_es = custom_es
        Custom_block.results = self.results
        Custom_block.oemof_es = self.custom_es.oemof_es
    
    
    def set_options(self, electricity_options, risks_options, repairs_options, repairs_cost_options):
        
        self.electr_groups = []
        for label, block_data in electricity_options.items():
            if block_data["block"]:
                custom_block = Custom_block(block_data["block"])
                custom_block.electr_plot = {}
                custom_block.electr_plot[label] = {"color": block_data["color"]}
                custom_block.color = block_data["color"]
                self.electr_groups.append(custom_block)
        
        
            for custom_block in self.electr_groups:
                for label, risk_data in risks_options.items():
                    if risk_data["risk_name"]  in  custom_block.wrapper_block.block.risks:
                        custom_block.risks_plot_dict[label] ={
                                "color": risk_data["color"],
                                "block_color": custom_block.color,
                                "storage": custom_block.wrapper_block.block.risks[risk_data["risk_name"]],
                                "max_risk": custom_block.wrapper_block.block.risks[risk_data["risk_name"]].nominal_storage_capacity
                                }
                            
                                                
            for custom_block in self.electr_groups:
                for label, repair_data in repairs_options.items():
                    if repair_data["id"] in custom_block.wrapper_block.block.repairs_blocks:
                        custom_block.repair_plot_dict[label] = {
                                "color": repair_data["color"],
                                "repair_block": custom_block.wrapper_block.block.repairs_blocks[repair_data["id"]]}
                            
        
            for custom_block in self.electr_groups:
                for label, repair_cost_data in repairs_cost_options.items():
                    if custom_block.wrapper_block.block is repair_cost_data["block"]:
                        custom_block.repair_cost_plot = {}
                        custom_block.repair_cost_plot[label] = {"color": repair_cost_data["color"]}

    
    def get_electricity_profile_by_block(self, block):
        custom_blocks = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block]
        custom_block = custom_blocks[0]
        res = pd.DataFrame()
        colors = []
        label = list(custom_block.electr_plot.keys())[0]
        res[label] = custom_block.get_electricity_profile()
        colors.append(custom_block.electr_plot[label]["color"])
        res = res[:-1]
        res.clip(lower=0)
        res.colors = colors
        return res
    
    
    def get_electricity_profile_all_blocks(self):
        res = pd.DataFrame()
        colors = []
        for custom_block in self.electr_groups:
            label = list(custom_block.electr_plot.keys())[0]
            res[label] = custom_block.get_electricity_profile()
            colors.append(custom_block.electr_plot[label]["color"])
        res = res[:-1]
        res.clip(lower=0)
        res.colors = colors
        return res
 
    
    def get_risks_profile_by_block(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        res = custom_block.get_risks_profile()
        colors = res.colors
        res = res[:-1]
        res.clip(lower=0)
        res.colors = colors
        return res
    
    def get_risks_profile_by_all_blocks_dict(self):
        res_dict = {}
        for custom_block in self.electr_groups:
            risk_df = custom_block.get_risks_profile()
            risk_df = risk_df[:-1]
            max_risk_dict = custom_block.get_max_risk_dict()
            block_label = custom_block.wrapper_block.label
            risks = max_risk_dict.keys()
            for risk in risks:
                risk_label = f"{risk} ({block_label})"
                max_risk = max_risk_dict[risk]
                risk_line_col = risk_df[risk]
                res_dict[risk_label] = {
                    "max_risk": max_risk,
                    "risk_line_col": risk_line_col,
                    # "color": custom_block.risks_plot_dict[risk]["color"]}
                    "color": custom_block.color}
        return res_dict
    
    
    def get_repairs_profile_by_block(self, block, part=1):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        res = custom_block.get_repair_status_profile()
        res *= custom_block.wrapper_block.block.nominal_power * part
        colors = res.colors
        res = res[:-1]
        res.clip(lower=0)
        res.colors = colors
        return res
    
    
    def get_repairs_profile_by_all_blocks_dict(self, part=1):
        res = {}
        for custom_block in self.electr_groups:
            repair_df = custom_block.get_repair_status_profile()
            block_color = custom_block.electr_plot[list(custom_block.electr_plot.keys())[0]]["color"]
            colors = repair_df.colors
            repair_df *= custom_block.wrapper_block.block.nominal_power * part
            repair_df = repair_df[:-1]
            # repair_df = repair_df.clip(lower=0)
            repair_df[repair_df <=0] = 0
            repair_df.colors = colors
            repair_df.block_color = block_color
            res[custom_block.wrapper_block.block.label] = repair_df
        return res
    
    
    def get_cost_profile_block(self, block, cumulative=False):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block[0]][0]
        res = custom_block.get_cost_profile()
        if cumulative:
            res = res.cumsum()
        res = res[:-1]
        res = res / 1e6
        return res
    
    
    def get_cost_profile_all_blocks(self, cumulative=False):
        res = pd.DataFrame()
        for custom_block in self.electr_groups:
            res[custom_block.wrapper_block.label] = custom_block.get_cost_profile()
        res = res.sum(axis=1).to_frame()
        res.columns = ["затраты на ремонты"]
        # print(res.max().max())
        if cumulative:
            res = res.cumsum()
        res = res[:-1]
        res = res / 1e6
        return res

    
    def get_sinks_profile(self, block, repair_id, risk_id):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        res = custom_block.get_sinks_profile(repair_id, risk_id)
        res = res[:-1]
        return res
    
    
    def get_control_stop_block_profile(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        res = custom_block.get_control_stop_block_profile()
        res = res[:-1]
        return res
    
    def get_npp_status_profile(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        res = custom_block.get_npp_status_profile()
        res = res[:-1]
        return res
    
    
    def get_npp_storage_dict(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        res_dict = custom_block.get_npp_storage_data_dict()
        return res_dict
    
    
    def get_repair_storage_max_uptime_dict(self, block, repair_id):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        res_dict = custom_block.get_repair_storage_max_uptime_dict(repair_id)
        return res_dict
    
        
    def get_events_profile_by_block(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.wrapper_block is block][0]
        events_df = custom_block.get_events_profile()
        if events_df is None:
            return pd.DataFrame()
        events_df *= 24
        events_df = events_df[:-1]
        return events_df
    
        
    def get_events_profile_all_blocks_df(self):
        res = pd.DataFrame()
        for custom_block in self.electr_groups:
            events_df = self.get_events_profile_by_block(custom_block.wrapper_block)
            res = pd.concat([res, events_df], axis=1)
        return res
    
    
    def get_increase_all_blocks_df(self):
        res = pd.DataFrame()
        for custom_block in self.electr_groups:
            res_loc =  custom_block.get_risk_increase_profile()
            res_loc *= 24
            res = pd.concat([res, res_loc], axis=1)
        res = res[:-1]
        return res
    
    
    def get_decrease_all_blocks_df(self):
        res = pd.DataFrame()
        for custom_block in self.electr_groups:
            res_loc =  custom_block.get_risk_decrease_profile()
            res_loc *= -24
            res = pd.concat([res, res_loc], axis=1)
        res = res[:-1]
        return res
    
    
    
    