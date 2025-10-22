

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
        scen_dict = deepcopy(self.scenario_dict)
        scen_dict[single_key]["status"] = bool(inner_dict)
        scen_dict[single_key].update(inner_dict)
        return Scenario_builder(scen_dict)


    def update_risk(self, inner_dict):
        scen_dict = deepcopy(self.scenario_dict)
        scen_dict["risk_options"]["status"] = bool(inner_dict)
        risk_options = scen_dict["risk_options"]["risks"]
        for risk_to_update, data_to_update in inner_dict.items():
            risk_options[risk_to_update] = risk_options.get(risk_to_update, {})
            risk_options[risk_to_update].update(data_to_update)
        return Scenario_builder(scen_dict)

    def update_repair(self, inner_dict):
        
        new_scen_dict = deepcopy(self.scenario_dict)
        new_scen_dict["repair_options"]["status"] = bool(inner_dict)
        repair_options = new_scen_dict["repair_options"]["options"]
        for repair_name, data_to_update in inner_dict.items():
            key_to_update = next((k for k,v in repair_options.items() if k == repair_name), None)
            if key_to_update:
                repair_options[key_to_update]["status"] = True
                repair_options[key_to_update].update(data_to_update)
            else:
                raise ValueError
        return Scenario_builder(new_scen_dict)
    
    
    def __or__(self, other):
            if isinstance(other, dict):
                return Scenario_builder({**self.scenario_dict, **other})
            elif isinstance(other, Scenario_builder):
                return Scenario_builder({**self.scenario_dict, **other.scenario_dict})
            else:
                raise ValueError
    
    