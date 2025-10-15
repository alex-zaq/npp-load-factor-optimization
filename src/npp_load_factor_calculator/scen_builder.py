

class Scenario_builder:
    
    def __init__(self, scenario_dict):
        self.scenario_dict = scenario_dict

    def update(self, inner_dict):
        single_key = list(self.scenario_dict.keys())[0]
        self.scenario_dict[single_key].update(inner_dict)
        return self.scenario_dict

    def update_risk(self, inner_dict):
        pass
    
    def update_repair(self, inner_dict):
        pass
        