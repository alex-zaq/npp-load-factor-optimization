




class Generic_sink:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
        
    def create_sink(self, label, input_bus):
        pass
    
        
class Generic_source:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
    
    def create_source(self, label, output_bus):
        pass
        
    
class Generic_storage:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
    
    def create_storage(self, label, input_bus, output_bus):
        pass
    
    
class Generic_converter:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
    
    def create_converter(self, label, input_bus, output_bus):
        pass
