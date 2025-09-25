


import numpy as np
import pandas as pd
from oemof import solph


class Custom_block:

    def __init__(self, block):
        self.block = block
        self.results = self.__class__.results
        self.main_risk_plot = None
        self.risk_events_plot = None
        self.repair_events_plot = None
        self.repair_cost_plot = None
        self.repair_events = None
        
    
    
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
        res_df.colors = colors
        return res_df
        
    def get_cost_profile_for_repairs_dict(self):
        res_df = pd.DataFrame()
        colors = []
        for repair_label, repair_plot_data in self.repair_plot_dict.items():
            colors.append(repair_plot_data["color"])
            block = repair_plot_data["repair_block"]
            output_bus = block.outputs_pair[0][1]
            startup_cost = block.startup_cost
            results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
            res_df[repair_label] = results[((block.label, output_bus.label), "status")]
            res_df[repair_label]  = res_df[repair_label] * startup_cost
        res_df = res_df.sum(axis=1)
        res_df.colors = colors
        return res_df
###############################################################################################################    
    
    
    def get_all_helper_profiles_dict(self):
        res = {}
        if self.block.risk_mode:
            res.update(self.get_helper_risks_profiles_dict())

            if self.block.default_risk_mode:
                res.update(self.get_helper_default_profiles_dict())

            if self.block.repair_mode:
                for repair_part_name in self.block.repair_nodes:
                    res.update(self.get_helper_repair_profiles_dict(repair_part_name))
        return res
    
    
    def get_helper_default_profiles_dict(self):
        helper_node_calculator = Helper_node_calculator(self)
        res = {}
        res["source_default_risk"] = {"output": helper_node_calculator.get_default_risk_profile()}
        return res        

    
    def get_helper_risks_profiles_dict(self):
        helper_node_calculator = Helper_node_calculator(self)
        res = {}
        res["storage_main_risk"] = {
            "input": helper_node_calculator.get_storage_main_risk_profiles("input"),
            "output": helper_node_calculator.get_storage_main_risk_profiles("output"),
            "content": helper_node_calculator.get_storage_main_risk_profiles("content"),
        }
        return res


    def get_helper_repair_profiles_dict(self, repair_part_name):
        
        repair_nodes_dict = self.block.repair_nodes
        selected_repair_node = next(k for k in repair_nodes_dict if repair_part_name in k)
        if not selected_repair_node:
            raise ValueError(f"Repair part {repair_part_name} not found")
        helper_node_calculator = Helper_node_calculator(self, repair_part_name)
        res = {}
        res["source_period"] = {"output": helper_node_calculator.get_source_period_output_profile()}
        res["source_repair"] = {"output": helper_node_calculator.get_source_repair_output_profile()}

        res["converter_repair"] = {
            "input_main_risk": helper_node_calculator.get_converter_input_main_risk_profile(),
            "input_period_control": helper_node_calculator.get_converter_input_period_control_profile(),
            "input_repair_control": helper_node_calculator.get_converter_input_repair_control_profile(),
            "output": helper_node_calculator.get_converter_output_profile(),
        }

        res["storage_period"] = {
            "input": helper_node_calculator.get_storage_repair_profiles(
                "storage_period", "input"
            ),
            "output": helper_node_calculator.get_storage_repair_profiles(
                "storage_period", "output"
            ),
            "content": helper_node_calculator.get_storage_repair_profiles(
                "storage_period", "content"
            ),
        }

        res["storage_repair"] = {
            "input": helper_node_calculator.get_storage_repair_profiles(
                "storage_repair", "input"
            ),
            "output": helper_node_calculator.get_storage_repair_profiles(
                "storage_repair", "output"
            ),
            "content": helper_node_calculator.get_storage_repair_profiles(
                "storage_repair", "content"
            ),
        }
        
        return res
     
     
     
  
class Helper_node_calculator:

    def __init__(self, custom_block, repair_part_name = None):
        self.custom_block = custom_block
        self.results = custom_block.results
        

    def get_default_risk_profile(self):
        if self.custom_block.npp_block.risk_mode is False:
            raise ValueError(
                "The block is not in risk mode, no default risk profile can be extracted"
            )
        default_risk_source = self.custom_block.npp_block.default_risk_nodes["source_default_risk"]
        label = f"{self.custom_block.npp_block.label}_default_risk"
        output_bus = default_risk_source.outputs_pair[0][1]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[label] = results[((default_risk_source.label, output_bus.label), "flow")]
        res_df = res_df.clip(lower=0)
        return res_df
        
                

    def get_storage_repair_profiles(self, storage_type, profile_type):
        
        if self.custom_block.npp_block.repair_mode is False:
            raise ValueError(
                "The block is not in repair mode, no repair profile can be extracted"
            )
        
        
        # укоротить после изучение results(block)
        
        if storage_type not in {"storage_period", "storage_main_risk", "storage_repair"}:
            raise ValueError("storage_type must be storage_period or main_risk_storage")
        
        if profile_type not in {"input", "output", "content"}:
            raise ValueError("profile_type must be input, output or content")
        
        self.repair_nodes = self.custom_block.npp_block.repair_nodes
        
        res = pd.DataFrame()

        if profile_type == "input":
            
            match storage_type:
                case "storage_period":
                    input_bus, storage = self.repair_nodes[storage_type].inputs_pair[0]
                    results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
                    res = results[((input_bus.label, storage.label), "flow")]
                    res = res.to_frame()
                    res.columns = [f"зарядка-{storage.label}"]

                case "storage_repair":
                    input_bus, storage = self.repair_nodes[storage_type].inputs_pair[0]
                    results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
                    res = results[((input_bus.label, storage.label), "flow")]
                    res = res.to_frame()
                    res.columns = [f"зарядка-{storage.label}"]

        elif profile_type == "output":
            
            match storage_type:
                case "storage_period":
                    storage, output_bus = self.repair_nodes[storage_type].outputs_pair[0]
                    results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
                    res = results[((storage.label, output_bus.label), "flow")]
                    res = res.to_frame()
                    res.columns = [f"разрядка-{output_bus.label}"]
                
                case "storage_repair":
                    storage, output_bus = self.repair_nodes[storage_type].outputs_pair[0]
                    results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
                    res = results[((storage.label, output_bus.label), "flow")]
                    res = res.to_frame()
                    res.columns = [f"разрядка-{output_bus.label}"]
                    
        elif profile_type == "content":
            
            match storage_type:
                case "storage_period":
                    storage = self.repair_nodes[storage_type]
                    output_bus = storage.outputs_pair[0][1]
                    results = solph.views.node(self.results, storage.label )["sequences"].dropna()
                    res = results[(output_bus.label, "None"), "storage_content"]
                    res = res.to_frame()
                    res.columns = [f"{storage.label}-content"]
                case "storage_repair":
                    storage = self.repair_nodes[storage_type]
                    output_bus = storage.outputs_pair[0][1]
                    results = solph.views.node(self.results, storage.label)["sequences"].dropna()
                    res = results[(output_bus.label, "None"), "storage_content"]
                    res = res.to_frame()
                    res.columns = [f"{storage.label}-content"]
        else:
            raise ValueError("profile_type must be input, output or content")

        return res                

    def get_storage_main_risk_profiles(self, profile_type):
        # укоротить после изучение results(block)
        
        if self.custom_block.npp_block.risk_mode is False:
            raise ValueError(
                "The block is not in risk mode, no risk profile can be extracted"
            )
            
        self.main_risk_nodes = self.custom_block.npp_block.main_risk_nodes
        
        if profile_type not in {"input", "output", "content"}:
            raise ValueError("profile_type must be input, output or content")
        
        res = pd.DataFrame()
        if profile_type == "input":
            input_bus, storage = self.main_risk_nodes["storage_main_risk"].inputs_pair[0]
            results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
            res = results[((input_bus.label, storage.label), "flow")]
            res = res.to_frame()
            res.columns = [f"зарядка-{storage.label}"]

        elif profile_type == "output":
            storage, output_bus = self.main_risk_nodes["storage_main_risk"].outputs_pair[0]
            results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
            res = results[((storage.label, output_bus.label), "flow")]
            res = res.to_frame()
            res.columns = [f"разрядка-{output_bus.label}"]
                    
        elif profile_type == "content":
            storage = self.main_risk_nodes["storage_main_risk"]
            output_bus = storage.outputs_pair[0][1]
            results = solph.views.node(self.results, storage.label)["sequences"].dropna()
            res = results[(storage.label, "None"), "storage_content"]
            res = res.to_frame()
            res.columns = [f"{storage.label}-content"]
        else:
            raise ValueError("profile_type must be input, output or content")

        return res



    def get_source_period_output_profile(self):
        if self.custom_block.npp_block.repair_mode is False:
            raise ValueError(
                "The block is not in repair mode, no repair profile can be extracted"
            )
        res = pd.DataFrame()
        # проверить необходимость dataframe
        self.repair_nodes = self.custom_block.npp_block.repair_nodes
        repair_nodes = self.repair_nodes
        source_period, output_bus = repair_nodes["source_period"].outputs_pair[0]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = results[((source_period.label, output_bus.label), "flow")]
        return res


    def get_source_repair_output_profile(self):
        if self.custom_block.npp_block.repair_mode is False:
            raise ValueError(
                "The block is not in repair mode, no repair profile can be extracted"
            )
        res = pd.DataFrame()
        self.repair_nodes = self.custom_block.npp_block.repair_nodes
        repair_nodes = self.repair_nodes
        source_repair, output_bus = repair_nodes["source_repair"].outputs_pair[0]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = results[((source_repair.label, output_bus.label), "flow")]
        return res


    def get_converter_repair_output_profile(self):
        if self.custom_block.npp_block.repair_mode is False:
            raise ValueError(
                "The block is not in repair mode, no repair profile can be extracted"
            )
        res = pd.DataFrame()
        self.repair_nodes = self.custom_block.npp_block.repair_nodes
        repair_nodes = self.repair_nodes
        block = repair_nodes["converter_repair"].outputs_pair[0]
        converter, output_bus = block.outputs_pair[0]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = results[((converter.label, output_bus.label), "flow")]
        return res
    
    
    def get_converter_repair_input_main_risk_profile(self):
        if self.custom_block.npp_block.repair_mode is False:
            raise ValueError(
                "The block is not in repair mode, no repair profile can be extracted"
            )
        res = pd.DataFrame()
        self.repair_nodes = self.custom_block.npp_block.repair_nodes
        repair_nodes = self.repair_nodes
        block = repair_nodes["converter_repair"]
        input_bus, converter = block.inputs_pair[0]
        results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res = results[((input_bus.label, converter.label), "flow")]
        return res
    
    def get_converter_repair_input_repair_control_profile(self):
        if self.custom_block.npp_block.repair_mode is False:
            raise ValueError(
                "The block is not in repair mode, no repair profile can be extracted"
            )
        res = pd.DataFrame()
        self.repair_nodes = self.custom_block.npp_block.repair_nodes
        repair_nodes = self.repair_nodes
        block = repair_nodes["converter_repair"]
        input_bus, converter  = block.inputs_pair[1]
        results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res = results[((input_bus.label, converter.label), "flow")]
        return res
    
    def get_converter_repair_input_period_control_profile(self):
        if self.custom_block.npp_block.repair_mode is False:
            raise ValueError(
                "The block is not in repair mode, no repair profile can be extracted"
            )
        res = pd.DataFrame()
        self.repair_nodes = self.custom_block.npp_block.repair_nodes
        repair_nodes = self.repair_nodes
        block = repair_nodes["converter_repair"]
        input_bus, converter  = block.inputs_pair[2]
        results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res = results[((input_bus.label, converter.label), "flow")]
        return res
    



class Block_grouper:

    def __init__(self, results, custom_es):
        self.results = results
        self.custom_es = custom_es
        Custom_block.results = self.results
    
    
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
                    if risk_data["risk_name"]  in  custom_block.block.risks_storages:
                        if not hasattr(custom_block, "risks_plot_dict"):
                            custom_block.risks_plot_dict = {}
                            custom_block.risks_plot_dict[label] = {
                                "color": risk_data["color"],
                                "storage": custom_block.block.risks_storages[risk_data["risk"]]}
                        else:
                            custom_block.risks_plot_dict[label] ={
                                "color": risk_data["color"],
                                "storage": custom_block.block.risks_storages[risk_data["risk"]]}
                            
                                                
            for custom_block in self.electr_groups:
                for label, repair_data in repairs_options.items():
                    if repair_data["id"] in custom_block.block.repairs_blocks:
                        if not hasattr(custom_block, "repair_plot_dict"):
                            custom_block.repair_plot_dict = {}
                            custom_block.repair_plot_dict[label] = {
                                "color": repair_data["color"],
                                "repair_block": custom_block.block.repairs_blocks[repair_data["id"]]
                                }
                        else:
                            custom_block.repair_plot_dict[label] = {
                                "color": repair_data["color"],
                                "repair_block": custom_block.block.repairs_blocks[repair_data["id"]]}
                            
        
            for custom_block in self.electr_groups:
                for label, repair_cost_data in repairs_cost_options.items():
                    if custom_block.block is repair_cost_data["block"]:
                        custom_block.repair_cost_plot = {}
                        custom_block.repair_cost_plot[label] = {"color": repair_cost_data["color"]}

    
    def get_electricity_profile(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block][0]
        res = pd.DataFrame()
        colors = []
        label = list(custom_block.electr_plot.keys())[0]
        res[label] = custom_block.get_electricity_profile()
        colors.append(custom_block.electr_plot[label]["color"])
        res.colors = colors
        return res
   
    
    def get_risks_profile(self, block):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block][0]
        res = custom_block.get_risks_profile()
        return res
    
    
    def get_repairs_profile(self, block, part=1):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block][0]
        res = custom_block.get_repair_status_profile()
        res *= custom_block.block.nominal_power * part
        return res
    
    
    def get_cost_profile(self, block, cumulative=False):
        custom_block = [custom_block for custom_block in self.electr_groups if custom_block.block is block[0]][0]
        res = custom_block.get_cost_profile()
        if cumulative:
            res = res.cumsum()
        return res

    
    def get_helper_block_profiles(self, block):
        for _, custom_block in self.electr_groups.items():
            if custom_block.npp_block is block:
                return custom_block.get_all_helper_profiles_dict()
        return None
    
    
    
    
    
    
    