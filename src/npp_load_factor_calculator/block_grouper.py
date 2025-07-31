


import numpy as np
import pandas as pd
from oemof import solph


class Custom_block:

    def __init__(self, npp_block, name, color):
        self.npp_block = npp_block
        self.name = name
        self.color = color
        self.results = self.__class__.results
        self.main_risk_plot = None
        self.risk_events_plot = None
        self.repair_events_plot = None
        self.repair_cost_plot = None
        self.repair_events = None
        
    
    
    def get_electricity_profile(self):
        block,output_bus = self.npp_block.output_pair[0]     
        block_results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = pd.DataFrame()
        res[block.label] = block_results[((block.label, output_bus.label), "flow")]
        res = res.clip(lower=0)
        return res


    def get_main_risk_profile(self):
        if self.npp_block.risk_mode is False:
            raise ValueError("The block is not in risk mode, no main risk profile can be extracted")
        main_risk_label = self.main_risk_plot["label"]        
        main_risk_storage = self.npp_block.main_risk_storage
        results = solph.views.node(self.results, main_risk_storage.label)["sequences"].dropna()
        res = pd.DataFrame()
        res[main_risk_label] = results[(main_risk_storage.label, "None"), "storage_content"]
        res = res.clip(lower=0)
        return res
        


    def get_risk_events_profile(self):
        if self.npp_block.risk_mode is False:
            raise ValueError("The block is not in risk mode, no risk events profile can be extracted")
        risk_events_label = self.risk_events_plot["label"]
        main_risk_source = self.npp_block.main_risk_source
        output_bus = main_risk_source.output_pair[0][1]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = pd.DataFrame()
        res[risk_events_label] = results[((main_risk_source.label, output_bus.label), "flow")]
        res = res.clip(lower=0)
        return res
            
        
    def get_default_risk_profile(self):
        if self.npp_block.risk_mode is False:
            raise ValueError("The block is not in risk mode, no default risk profile can be extracted")
        default_risk_source = self.npp_block.default_risk_source
        label = f"{self.npp_block.label}_default_risk"
        output_bus = default_risk_source.output_pair[0][1]
        results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
        res = pd.DataFrame()
        res[label] = results[((default_risk_source.label, output_bus.label), "flow")]
        res = res.clip(lower=0)
        return res
    
    def get_repair_active_status_profile_dict(self, *, mode):
        if self.npp_block.risk_mode is False:
            raise ValueError("The block is not in risk mode, no repair profile can be extracted")
        after_label = mode if mode in {"status", "flow"} else ValueError("mode must be status or flow")
        res = {}
        repair_nodes = self.npp_block.repair_nodes
        for repair_name in repair_nodes:
            label = f"{repair_name.label}_{after_label}"
            repair_block = repair_nodes[repair_name]["converter_npp"]
            output_bus = repair_block.output_pair[0][1]
            results = solph.views.node(self.results, output_bus.label)["sequences"].dropna()
            res[label] = results[((repair_block.label, output_bus.label), mode)]
        return res
    
    def get_cost_profile_dict(self):
        repair_active_profile_dict = self.get_repair_active_status_profile_dict(mode="status")
        res = {}
        for repair_name in repair_active_profile_dict:
            startup_cost = self.npp_block.repair_nodes[repair_name]["converter_npp"]["startup_cost"]
            repair_active_profile_dict[repair_name].to_numpy()
            res[repair_name] = np.where(repair_active_profile_dict[repair_name] == 1, startup_cost, 0)
        return res
        
    
    def get_cumulative_cost_profile_dict(self):
        cost_profile_dict = self.get_cost_profile_dict()
        res = {}
        for repair_name in cost_profile_dict:
            res[repair_name] = cost_profile_dict[repair_name].cumsum()
            # bad?
        return res
    
    def get_cost_abs_value_dict(self):
        res = self.get_cost_profile_dict()
        res = {k: v.sum() for k, v in res.items()}
        return res
    
    def get_global_abs_value(self):
        res = self.get_cost_abs_value_dict()
        res = sum(res.values())
        return res
    
    
    def get_global_cost_profile(self):
        
        return res
    
    
    def get_global_cumulative_cost_profile(self):
        res = self.get_cumulative_cost_profile_dict()
        res = sum(res.values())
        return res


    def get_helper_profiles(self, mode):
        pass

  


class Block_grouper:

    def __init__(self, results, custom_es):
        self.results = results
        self.custom_es = custom_es
        Custom_block.results = self.results
    
    def set_block_groups(self, electricity_gen, main_risk_gen, risk_events, repair_cost):
        self.electr_groups = {k: Custom_block(v["order"][0], k, v["color"]) for k, v in electricity_gen.items() if v["order"][0]}
        for _, v in self.electr_groups.items():
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
        for _, v in self.electr_groups.items():
            for i, (repair_events_k, repair_events_v) in enumerate(repair_events.items()):
                info_dict = repair_events_v["colors"]
                repair_names, colors = list(info_dict.keys()), list(info_dict.values())
                v.repair_events_plot = {"order": i, "label": repair_events_k, "colors": colors, "repair_names": repair_names}
    
    
    def get_electricity_profile(self):
        res = pd.DataFrame()
        for _, v in self.electr_groups.items():
            res[v.name] = v.get_electricity_profile()[v.name]
        return res
    
    def get_risk_events_profile(self):
        res = pd.DataFrame()
        for _, v in self.electr_groups.items():
            res[v.name] = v.get_risk_events_profile()
        return res
    
    def get_main_risk_profile(self):
        res = pd.DataFrame()
        for _, v in self.electr_groups.items():
            res[v.name] = v.get_main_risk_profile()
        return res
    
    def get_default_risk_profile(self):
        res = pd.DataFrame()
        for _, v in self.electr_groups.items():
            res[v.name] = v.get_default_risk_profile()
        return res
    
    def get_repair_profile(self, mode):
        if mode not in {"status", "flow"}:
            raise ValueError(f"Invalid mode: {mode}")
        res = pd.DataFrame()
        for _, v in self.electr_groups.items():
            buf = v.get_repair_active_status_profile(mode=mode)
            for kk, vv in buf.items():
                res[kk] = vv
        return res
        
        
    def get_global_abs_cost_by_block(self):
        res = pd.DataFrame()
        for _, v in self.electr_groups.items():
            res[v.name] = v.get_global_abs_cost()
        return res
        
    def get_global_abs_cost(self):
        res = 0
        for _, v in self.electr_groups.items():
            res += v.get_global_abs_cost()
        return res
        
    def get_cost_profile(self):
        res = pd.DataFrame()
        for _, v in self.electr_groups.items():
            res[v.name] = v.get_cost_profile()
        return res
    
    
    
    def get_cumulative_cost_profile(self):
        pass
    
    
    def get_helper_block_profiles_dict(self, block_name, mode):
        pass
    
    
    
    
    
    
    