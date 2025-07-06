



class Oemof_model:
    
    def __init__(self, scen_settings, model_settings):
        self.scenario_settings = scen_settings
        self.model_settings = model_settings
    
    def init_oemof_model(self):
        pass
    
    def init_custom_model(self):
        pass
    
    def add_constraints(self):
        pass
    
    def calculate(self):
        self.init_oemof_model()
        self.init_custom_model()
        self.add_constraints()
        self.calculate()
        
    def get_custom_es(self):
        return self.custom_es