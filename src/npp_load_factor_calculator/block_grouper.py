


import numpy as np
import pandas as pd
from oemof import solph


class Custom_block:

    def __init__(self, block):
        self.block = block
        self.results = self.__class__.results
        self.risks_plot_dict = {}
        self.repair_plot_dict = {}
        self.repair_cost_plot_dict = {}
        
        
    
    
    def get_electricity_profile(self):
        block,output_bus = self.block.outputs_pair[0]     
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
        

    def get_repair_status_profile(self):
        res_df = pd.DataFrame()
        colors = []
        for repair_label, repair_plot_data in self.repair_plot_dict.items():
            colors.append(repair_plot_data["color"])
            block = repair_plot_data["repair_block"]
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
            block = repair_plot_data["repair_block"]
            output_bus = block.outputs_pair[0][1]
            startup_cost = block.startup_cost
            results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
            res_df[repair_label] = results[((block.label, output_bus.label), "startup")]
            res_df[repair_label]  = res_df[repair_label] * startup_cost
        res_df = res_df.sum(axis=1)
        res_df.colors = colors
        return res_df
    
    def get_sinks_profile(self, repair_id, risk_name):
        selected_repair_block = self.block.repairs_blocks[repair_id]
        sink = selected_repair_block.sinks[risk_name]
        input_bus = sink.inputs_pair[0][0]
        res_df = pd.DataFrame()
        sink_results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res_df[sink.label] = sink_results[((input_bus.label, sink.label), "flow")]
        res_df = res_df.clip(lower=0)
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
                self.electr_groups.append(custom_block)
        
        
            for custom_block in self.electr_groups:
                for label, risk_data in risks_options.items():
                    if risk_data["risk_name"]  in  custom_block.block.risks:
                        custom_block.risks_plot_dict[label] ={
                                "color": risk_data["color"],
                                "storage": custom_block.block.risks[risk_data["risk_name"]]}
                            
                                                
            for custom_block in self.electr_groups:
                for label, repair_data in repairs_options.items():
                    if repair_data["id"] in custom_block.block.repairs_blocks:
                        custom_block.repair_plot_dict[label] = {
                                "color": repair_data["color"],
                                "repair_block": custom_block.block.repairs_blocks[repair_data["id"]]}
                            
        
            for custom_block in self.electr_groups:
                for label, repair_cost_data in repairs_cost_options.items():
                    if custom_block.block is repair_cost_data["block"]:
                        custom_block.repair_cost_plot = {}
                        custom_block.repair_cost_plot[label] = {"color": repair_cost_data["color"]}

    
    def get_electricity_profile_by_block(self, block):
        custom_blocks = [custom_block for custom_block in self.electr_groups if custom_block.block is block]
        custom_block = custom_blocks[0]
        res = pd.DataFrame()
        colors = []
        label = list(custom_block.electr_plot.keys())[0]
        res[label] = custom_block.get_electricity_profile()
        colors.append(custom_block.electr_plot[label]["color"])
        res = res[:-1]
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
        res.colors = colors
        return res
    
    
    def get_electricity_profile_by_blocks(self, blocks):
        pass
    
    
   
    
    def get_risks_profile_by_block(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block][0]
        res = custom_block.get_risks_profile()
        colors = res.colors
        res = res[:-1]
        res.colors = colors
        return res
    
    
    def get_repairs_profile_by_block(self, block, part=1):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block][0]
        res = custom_block.get_repair_status_profile()
        res *= custom_block.block.nominal_power * part
        colors = res.colors
        res = res[:-1]
        res.colors = colors
        return res
    
    
    def get_cost_profile_block(self, block, cumulative=False):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block[0]][0]
        res = custom_block.get_cost_profile()
        if cumulative:
            res = res.cumsum()
        res = res[:-1]
        return res
    
    
    def get_cost_profile_all_blocks(self, cumulative=False):
        res = pd.DataFrame()
        for custom_block in self.electr_groups:
            res[custom_block.block.label] = custom_block.get_cost_profile()
        res = res.sum(axis=1).to_frame()
        res.columns = ["затраты"]
        if cumulative:
            res = res.cumsum()
        res = res[:-1]
        return res

    
    def get_sinks_profile(self, block, repair_id, risk_id):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block][0]
        res = custom_block.get_sinks_profile(repair_id, risk_id)
        res = res[:-1]
        return res
    
    
    
    
    
    
    