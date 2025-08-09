


import numpy as np
import pandas as pd
from oemof import solph


class Custom_block:

    def __init__(self, npp_block, name):
        self.npp_block = npp_block
        self.name = name
        # self.color = color
        self.results = self.__class__.results
        self.main_risk_plot = None
        self.risk_events_plot = None
        self.repair_events_plot = None
        self.repair_cost_plot = None
        self.repair_events = None
        
    
    
    def get_electricity_profile(self):
        block,output_bus = self.npp_block.output_pair[0]     
        block_results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[block.label] = block_results[((block.label, output_bus.label), "flow")]
        res_df = res_df.clip(lower=0)
        return res_df


    def get_main_risk_profile(self):
        if self.npp_block.risk_mode is False:
            raise ValueError("The block is not in risk mode, no main risk profile can be extracted")
        main_risk_label = self.main_risk_plot["label"]        
        main_risk_storage = self.npp_block.main_risk_storage
        results = solph.views.node(self.results, main_risk_storage.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[main_risk_label] = results[(main_risk_storage.label, "None"), "storage_content"]
        res_df = res_df.clip(lower=0)
        return res_df
        


    def get_risk_events_profile(self):
        if self.npp_block.risk_mode is False:
            raise ValueError("The block is not in risk mode, no risk events profile can be extracted")
        risk_events_label = self.risk_events_plot["label"]
        main_risk_source = self.npp_block.main_risk_source
        output_bus = main_risk_source.output_pair[0][1]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[risk_events_label] = results[((main_risk_source.label, output_bus.label), "flow")]
        res_df = res_df.clip(lower=0)
        return res_df
            
    
    def get_repair_active_status_profile_dict(self, *, mode):
        if self.npp_block.risk_mode is False:
            raise ValueError("The block is not in risk mode, no repair profile can be extracted")
        # after_label = mode if mode in {"status", "flow"} else ValueError("mode must be status or flow")
        # tag? afterflow
        res_dict = {}
        repair_nodes = self.npp_block.repair_nodes
        for repair_name in repair_nodes:
            # label = f"{repair_name.label}_{after_label}"
            label = f"{repair_name.label}"
            repair_block = repair_nodes[repair_name]["converter_npp"]
            output_bus = repair_block.output_pair[0][1]
            results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
            res_dict[label] = results[((repair_block.label, output_bus.label), mode)]
        return res_dict
    
    
    def get_cost_profile_dict(self):
        repair_active_profile_dict = self.get_repair_active_status_profile_dict(mode="status")
        res_dict = {}
        for repair_name in repair_active_profile_dict:
            startup_cost = self.npp_block.repair_nodes[repair_name]["converter_npp"]["startup_cost"]
            repair_active_profile_dict[repair_name].to_numpy()
            res_dict[repair_name] = np.where(repair_active_profile_dict[repair_name] == 1, startup_cost, 0)
        return res_dict
    
    
    def get_cumulative_cost_profile_dict(self):
        cost_profile_dict = self.get_cost_profile_dict()
        res = {}
        for repair_name in cost_profile_dict:
            res[repair_name] = cost_profile_dict[repair_name].cumsum()
        return res
    
    def get_cost_abs_value_dict(self):
        res = self.get_cost_profile_dict()
        res = {repair_name: repair_array.sum() for repair_name, repair_array in res.items()}
        return res
    
    def get_global_abs_cost(self):
        res = self.get_cost_abs_value_dict()
        res = sum(res.values())
        return res
    
    def get_global_cost_profile(self):
        cost_profile_dict = self.get_cost_profile_dict()
        res = pd.DataFrame({k:v for k,v in cost_profile_dict.items()})
        res = res.sum(axis=1)
        res.name = "cost"
        return res
    
    def get_cumulative_cost_profile(self):
        res = self.get_global_cost_profile()
        res = res.sum(axis=1)
        res.name = "cumulative_cost"
        return res

    def get_helper_profiles_dict(self, repair_part_name):
        
        repair_nodes_dict = self.npp_block.repair_nodes
        selected_repair_node = next(k for k in repair_nodes_dict if repair_part_name in k)
        
        if not selected_repair_node:
            raise ValueError(f"Repair part {repair_part_name} not found")

        helper_node_calculator = Helper_node_calculator(self, repair_part_name)

        res = {}
        res["source_period"] = {"output": helper_node_calculator.get_source_period_output_profile()}
        res["source_repair"] = {"output": helper_node_calculator.get_source_repair_output_profile()}

        res["source_default_risk"] = {"output": helper_node_calculator.get_default_output_profile()}

        res["converter_repair"] = {
            "input_main_risk": helper_node_calculator.get_converter_input_main_risk_profile(),
            "input_period_control": helper_node_calculator.get_converter_input_period_control_profile(),
            "input_repair_control": helper_node_calculator.get_converter_input_repair_control_profile(),
            "output": helper_node_calculator.get_converter_output_profile(),
        }

        res["storage_period"] = {
            "input": helper_node_calculator.get_storage_profiles("storage_period", "input"),
            "output": helper_node_calculator.get_storage_profiles("storage_period", "output"),
            "content": helper_node_calculator.get_storage_profiles("storage_period", "content"),
        }
        res["storage_main_risk"] = {
            "input": helper_node_calculator.get_storage_profiles("storage_main_risk", "input"),
            "output": helper_node_calculator.get_storage_profiles("storage_main_risk", "output"),
            "content": helper_node_calculator.get_storage_profiles("storage_main_risk", "content"),
        }
        res["storage_repair"] = {
            "input": helper_node_calculator.get_storage_profiles("storage_repair", "input"),
            "output": helper_node_calculator.get_storage_profiles("storage_repair", "output"),
            "content": helper_node_calculator.get_storage_profiles("storage_repair", "content"),
        }
        
        return res
     
     
     
  
class Helper_node_calculator:

    def __init__(self, custom_block, repair_part_name):
        self.custom_block = custom_block
        self.repair_dict = custom_block.repair_nodes[repair_part_name]
        self.results = custom_block.results

    def get_default_risk_profile(self):
        if self.custom_block.npp_block.risk_mode is False:
            raise ValueError(
                "The block is not in risk mode, no default risk profile can be extracted"
            )
        default_risk_source = self.npp_block.default_risk_source
        label = f"{self.npp_block.label}_default_risk"
        output_bus = default_risk_source.output_pair[0][1]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res_df = pd.DataFrame()
        res_df[label] = results[((default_risk_source.label, output_bus.label), "flow")]
        res_df = res_df.clip(lower=0)
        return res_df
        

    def get_storage_profiles(self, storage_type, profile_type):
        
        # укоротить после изучение results(block)
        
        if storage_type not in {"storage_period", "storage_main_risk", "storage_repair"}:
            raise ValueError("storage_type must be storage_period or main_risk_storage")
        
        if profile_type not in {"input", "output", "content"}:
            raise ValueError("profile_type must be input, output or content")
        
        res = pd.DataFrame()

        if profile_type == "input":
            
            match storage_type:
                case "storage_period":
                    input_bus, storage  = self.repair_dict[storage_type].input_pair[0]
                    results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
                    res = results[((storage.label, storage.label), "flow")]
                
                case "storage_main_risk":
                    input_bus, storage = self.repair_dict[storage_type].input_pair[0]
                    results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
                    res = results[((storage.label, storage.label), "flow")]
                
                case "storage_repair":
                    input_bus, storage = self.repair_dict[storage_type].input_pair[0]
                    results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
                    res = results[((storage.label, storage.label), "flow")]

        elif profile_type == "output":
            
            match storage_type:
                case "storage_period":
                    storage, output_bus = self.repair_dict[storage_type].output_pair[0]
                    results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
                    res = results[((storage.label, "None"), "flow")]
                
                case "storage_main_risk":
                    storage, output_bus = self.repair_dict[storage_type].output_pair[0]
                    results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
                    res = results[((storage.label, "None"), "flow")]
                
                case "storage_repair":
                    storage, output_bus = self.repair_dict[storage_type].output_pair[0]
                    results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
                    res = results[((storage.label, "None"), "flow")]
        elif profile_type == "content":
            
            storage = self.repair_dict[storage_type]
            
            match storage_type:
                case "storage_period":
                    results = solph.views.node(self.results, storage.label )["sequences"].dropna()
                    res = results[(output_bus.label, "None"), "storage_content"]
                case "storage_main_risk":
                    results = solph.views.node(self.results, storage.label)["sequences"].dropna()
                    res = results[(output_bus.label, "None"), "storage_content"]
                case "storage_repair":
                    results = solph.views.node(self.results, storage.label)["sequences"].dropna()
                    res = results[(output_bus.label, "None"), "storage_content"]
        else:
            raise ValueError("profile_type must be input, output or content")
    

        return res



    def get_source_period_output_profile(self):
        res = pd.DataFrame()
        # проверить необходимость dataframe
        source_period, output_bus = self.repair_dict["source_period"].output_pair[0]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = results[((source_period.label, output_bus.label), "flow")]
        return res


    def get_source_repair_output_profile(self):
        res = pd.DataFrame()
        source_repair, output_bus = self.repair_dict["source_repair"].output_pair[0]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = results[((source_repair.label, output_bus.label), "flow")]
        return res


    def get_converter_repair_output_profile(self):
        res = pd.DataFrame()
        block = self.repair_dict["converter_repair"]
        converter, output_bus = block.output_pair[0]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = results[((converter.label, output_bus.label), "flow")]
        return res
    
    def get_converter_repair_input_main_risk_profile(self):
        res = pd.DataFrame()
        block = self.repair_dict["converter_repair"]
        converter, input_bus = block.input_pair[0]
        results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res = results[((input_bus.label, converter.label), "flow")]
        return res
    
    def get_converter_repair_input_repair_control_profile(self):
        res = pd.DataFrame()
        block = self.repair_dict["converter_repair"]
        converter, input_bus = block.input_pair[1]
        results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res = results[((input_bus.label, converter.label), "flow")]
        return res
    
    def get_converter_repair_input_period_control_profile(self):
        res = pd.DataFrame()
        block = self.repair_dict["converter_repair"]
        converter, input_bus = block.input_pair[2]
        results = solph.views.node(self.results, input_bus.label)["sequences"].dropna()
        res = results[((input_bus.label, converter.label), "flow")]
        return res
    



    
    
    
    
    
    
    
    
    


class Block_grouper:

    def __init__(self, results, custom_es):
        self.results = results
        self.custom_es = custom_es
        Custom_block.results = self.results
    
    
    def set_block_groups(self, electricity_gen, main_risk_gen, risk_events, repair_cost):

        self.electr_groups = {k: Custom_block(v["order"][0], k) for k, v in electricity_gen.items() if v["order"][0]}
        
        for _, v in self.electr_groups.items():
            for i, (es_k, es_v) in enumerate(self.custom_es.items()):
                if v.npp_block is es_v["order"][0]:
                    v.electr_plot = {"order": i, "label": es_k, "color": es_v["color"]}
            for i, (main_risk_k, main_risk_v) in enumerate(main_risk_gen.items()):
                if v.npp_block is main_risk_v["order"][0]:
                    v.main_risk_plot = {"order": i, "label": main_risk_k, "color": main_risk_v["color"]}
            for i, (repair_cost_k, repair_cost_v) in enumerate(repair_cost.items()):
                if v.npp_block is repair_cost_v["order"][0]:
                    v.repair_cost_plot = {"order": i, "label": repair_cost_k, "color": repair_cost_v["color"]}
            for i, (accident_k, accident_v) in enumerate(risk_events.items()):
                if v.npp_block is accident_v["order"][0]:
                    v.risk_events_plot = {"order": i, "label": accident_k, "color": accident_v["color"]}
    
    
    def set_repair_plot_options(self, repair_events):
        if not hasattr(self, "electr_groups"):
            raise ValueError("The block groups have not been set yet")
        for v in self.electr_groups.values():
            for i, (repair_events_k, repair_events_v) in enumerate(repair_events.items()):
                if v.npp_block is repair_events_v["order"][0]:
                    repair_id_lst =[v[1] for v in repair_events_v["color"].values()]  
                    colors_lst = [v[0] for v in repair_events_v["color"].values()]
                    repair_names = list(repair_events_v["color"].keys())
                    repair_names = [f"{repair_events_k}_{v}" for v in repair_names]
                    v.repair_events_plot = {"order": i, "repair_id_lst": repair_id_lst , "colors": colors_lst, "repair_names": repair_names}
    
    
    def get_electricity_profile(self):
        res = pd.DataFrame()
        sorted_by_order = sorted(self.electr_groups.values(), key=lambda x: x.electr_plot["order"])
        colors = []
        for custom_block in sorted_by_order:
            res[custom_block.electr_plot["label"]] = custom_block.get_electricity_profile()
            colors.append(custom_block.electr_plot["color"])
        res.colors = colors
        return res
    
    
    def get_risk_events_profile(self):
        res = pd.DataFrame()
        sorted_by_order = sorted(self.electr_groups.values(), key=lambda x: x.risk_events_plot["order"])
        colors = []
        for custom_block in sorted_by_order:
            res[custom_block.risk_events_plot["label"]] = custom_block.get_risk_events_profile()
            colors.append(custom_block.risk_events_plot["color"])
        res.colors = colors
        return res
    
    
    def get_main_risk_profile(self):
        res = pd.DataFrame()
        sorted_by_order = sorted(self.electr_groups.values(), key=lambda x: x.main_risk_plot["order"])
        colors = []       
        for custom_block in sorted_by_order:
            res[custom_block.main_risk_plot["label"]] = custom_block.get_main_risk_profile()
            colors.append(custom_block.main_risk_plot["color"])
        res.colors = colors
        return res
    
    
    def get_cost_profile_by_block(self, *, cumulative=False):
        res = pd.DataFrame()
        sorted_by_order = sorted(self.electr_groups.values(), key=lambda x: x.electr_plot["order"])
        colors = []
        for custom_block in sorted_by_order:
            res[custom_block.electr_plot["label"]] = custom_block.get_cost_profile()
            colors.append(custom_block.electr_plot["color"])
        res.colors = colors
        
        if cumulative:
            res = res.cumsum()
            
        return res
    
    
    def get_cost_profile(self, *, cumulative=False):
        res = pd.DataFrame()
        for _, custom_block in self.electr_groups.items():
            res[custom_block.name] = custom_block.get_cost_profile()
        res = res.sum(axis=1)
        res.name = "cost"
        
        if cumulative:
            res = res.cumsum()
            res.name = "cumulative_cost"        
        
        return res


    def get_repair_profile(self, mode):
        #  v.repair_events_plot = {"order": i, "repair_id_lst": repair_id_lst , "colors": colors_lst, "repair_names": repair_names}
        if mode not in {"status", "flow"}:
            raise ValueError(f"Invalid mode: {mode}")
        res = pd.DataFrame()
        colors = []
        for custom_block in self.electr_groups.values():
            repair_df = custom_block.get_repair_active_status_profile_dict(mode=mode)
            columns = repair_df.columns.to_list()
            columns_sorted = [columns[i] for i in custom_block.repair_events_plot["repair_id_lst"]] 
            repair_df = repair_df.reindex(columns_sorted)
            repair_df.columns = custom_block.repair_events_plot["repair_names"]
            colors.extend(custom_block.repair_events_plot["colors"])
            res = pd.concat([res, repair_df], axis=1)
        res.colors = colors
        return res

        
    def get_global_abs_cost_by_block(self):
        res = pd.DataFrame()
        for _, custom_block in self.electr_groups.items():
            res[custom_block.name] = custom_block.get_global_abs_cost()
        return res
        
        
    def get_global_abs_cost(self):
        res = 0
        for _, custom_block in self.electr_groups.items():
            res += custom_block.get_global_abs_cost_by_block()
        return res


    
    def get_helper_block_profiles(self, block_name):
        for _, custom_block in self.electr_groups.items():
            if custom_block is block_name:
                return custom_block.get_helper_profiles_dict()
        return None
    
    
    
    
    
    
    