

from copy import deepcopy


class Scenario_builder:
    
    def __init__(self, scenario_dict):
        self.scenario_dict = scenario_dict

    def to_dict(self):
        return self.scenario_dict

    def to_builder(self):
        return Scenario_builder(self.scenario_dict)

    def update(self, other):
        if isinstance(other, Scenario_builder):
            single_key = list(self.scenario_dict.keys())[0]
            self.scenario_dict[single_key].update(other.scenario_dict)
            return self.scenario_dict
        else:
            raise ValueError
               
    
    def update_outage(self, inner_dict):
        single_key = "outage_options"
        self.scenario_dict[single_key].update(inner_dict)
        return deepcopy(self)


    def update_risk(self, inner_dict):
        risk_options = self.scenario_dict["risk_options"]["risks"]
        for risk_to_update, data_to_update in inner_dict.items():
            key_to_update = next((k for k,v in risk_options.items() if k == risk_to_update), None)
            if key_to_update:
                risk_options[key_to_update].update(data_to_update)
            else:
                raise ValueError
        return deepcopy(self)

    def update_repair(self, inner_dict):
        repair_options = self.scenario_dict["repair_options"]["options"]
        for repair_name, data_to_update in inner_dict.items():
            key_to_update = next((k for k,v in repair_options.items() if k == repair_name), None)
            if key_to_update:
                repair_options[key_to_update]["status"] = True
                repair_options[key_to_update].update(data_to_update)
            else:
                raise ValueError
            if "allow_parallel_repairs" in inner_dict:
                self.scenario_dict["repair_options"]["allow_parallel_repairs"] = inner_dict["allow_parallel_repairs"]
        return deepcopy(self)
    
    
    def __or__(self, other):
            if isinstance(other, dict):
                return Scenario_builder({**self.scenario_dict, **other})
            elif isinstance(other, Scenario_builder):
                return Scenario_builder({**self.scenario_dict, **other.scenario_dict})
            else:
                raise ValueError
    
    